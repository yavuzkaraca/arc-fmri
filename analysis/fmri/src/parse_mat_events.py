"""Convert Psychtoolbox trial logs (pre-extracted to JSON via mat2json_trials.m)
into BIDS-compliant _events.tsv files.

Each _bold run is matched to its log file by comparing the log's scanner-trigger
start time (log["experiment_start_abs"]) against the run's AcquisitionTime
sidecar metadata. Runs with no log within tolerance are skipped with a warning
rather than guessed at, since matching by file order/count is not reliable
when a scan was aborted before a log could be saved.

Safe to re-run: every _events.tsv is deterministically regenerated from its
matched log and bold sidecar, so adding new subjects/sessions does not
require touching or invalidating anything already written.
"""

import json
import logging
import os
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import nibabel as nib
import numpy as np
import pandas as pd
from bids import BIDSLayout
from dotenv import load_dotenv
from scipy.optimize import linear_sum_assignment

LOCAL_TZ = ZoneInfo("Europe/Berlin")
MATCH_TOLERANCE_SECONDS = 300  # generous vs. the ~1 min log-save/trigger offset observed

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def log_start_local_time(log: dict) -> time:
    return datetime.fromtimestamp(log["experiment_start_abs"], tz=LOCAL_TZ).time()


def acquisition_local_time(time_str: str) -> time:
    return datetime.strptime(time_str, "%H:%M:%S.%f").time()


def seconds_between(t1: time, t2: time) -> float:
    d1 = datetime.combine(datetime.min, t1)
    d2 = datetime.combine(datetime.min, t2)
    return abs((d1 - d2).total_seconds())


def trials_to_events(log: dict) -> pd.DataFrame:
    trials = pd.DataFrame(log["trials"])
    onsets = trials["stim_onset_rel"].to_numpy(dtype=float)

    # The log does not store RESPONSE_TIME_LIMIT directly, so the per-trial
    # duration is derived empirically from consecutive same-phase onsets
    # instead of being hardcoded -- this keeps the pipeline correct even if
    # the constant changes in a future session.
    same_phase_next = (
        (trials["block_id"] == trials["block_id"].shift(-1))
        & (trials["phase_index"] == trials["phase_index"].shift(-1))
    )
    diffs = np.diff(onsets)[same_phase_next.to_numpy()[:-1]]
    if len(diffs) == 0:
        raise ValueError("Could not determine trial duration: no within-phase consecutive trials found.")
    trial_duration = round(float(np.median(diffs)), 3)

    trial_type = trials["phase"].apply(
        lambda p: "inference" if p.startswith("inference") else "application"
    )

    def fmt_rt(rt):
        return "n/a" if rt is None or (isinstance(rt, float) and np.isnan(rt)) else round(float(rt), 3)

    def fmt_correct(is_correct):
        if isinstance(is_correct, list):  # MATLAB [] for non-decision (instruction) trials
            return "n/a"
        return int(bool(is_correct))

    events = pd.DataFrame({
        "onset": np.round(onsets, 3),
        "duration": trial_duration,
        "trial_type": trial_type,
        "response_time": trials["rt"].apply(fmt_rt),
        "accuracy": trials["is_correct"].apply(fmt_correct),
        "block_id": trials["block_id"],
        "phase": trials["phase"],
        "trial_family": trials["trial_family"],
        "rule": trials["rule"],
    })

    return events.sort_values("onset").reset_index(drop=True)


def find_log_jsons(logfiles_dir: Path, sub_label: str) -> list[Path]:
    sub_dir = logfiles_dir / sub_label
    if not sub_dir.is_dir():
        return []
    return sorted(sub_dir.glob("log_p*.json"))


def n_volumes(bold_path: str) -> int:
    shape = nib.load(bold_path).shape
    return shape[-1] if len(shape) == 4 else 1


def match_logs_to_groups(logs, groups):
    n_logs, n_groups = len(logs), len(groups)
    if n_logs == 0 or n_groups == 0:
        return [], list(range(n_groups))

    cost = np.full((n_logs, n_groups), MATCH_TOLERANCE_SECONDS * 10.0)
    for i, log in enumerate(logs):
        for j, group in enumerate(groups):
            cost[i, j] = seconds_between(log["local_time"], group["acquisition_time"])

    row_ind, col_ind = linear_sum_assignment(cost)

    pairs = []
    matched_groups = set()
    for i, j in zip(row_ind, col_ind):
        if cost[i, j] <= MATCH_TOLERANCE_SECONDS:
            pairs.append((i, j))
            matched_groups.add(j)

    unmatched = [j for j in range(n_groups) if j not in matched_groups]
    return pairs, unmatched


def warn_unmatched(group, all_groups):
    vols = [n_volumes(f.path) for f in group["bold_files"]]
    siblings = [
        n_volumes(f.path)
        for g in all_groups
        if g is not group and g["key"][1] == group["key"][1]  # same task
        for f in g["bold_files"]
    ]
    example = group["bold_files"][0]
    msg = (
        f"No log file matched sub-{example.entities['subject']} "
        f"ses-{example.entities.get('session')} run {group['key']} "
        f"(acquisition time {group['acquisition_time']}). "
        f"log file not found -- perhaps none was written due to the scan being aborted "
        f"(the log is only saved once the full experiment completes). "
        f"This run has {vols} volume(s)."
    )
    if siblings:
        msg += f" Comparable runs have {siblings} volume(s)."
        if vols and min(vols) < 0.9 * max(siblings):
            msg += " The shortfall is consistent with an aborted/truncated acquisition."
    logger.warning(msg)


def write_events_tsv(events: pd.DataFrame, bold_file):
    out_path = Path(bold_file.path.replace("_bold.nii.gz", "_events.tsv"))
    events.to_csv(out_path, sep="\t", index=False, na_rep="n/a")
    logger.info("Wrote %s", out_path)


def main():
    load_dotenv()
    bids_root = Path(os.environ["BIDS_ROOT_DIR"])
    logfiles_dir = Path(os.environ["SOURCE_DATA_DIR"]) / "experimental_logfiles"

    layout = BIDSLayout(bids_root, validate=False)
    bold_files = layout.get(suffix="bold", extension=".nii.gz")

    subjects = sorted({f.entities["subject"] for f in bold_files})

    for subject in subjects:
        sub_label = f"sub-{subject}"
        sub_bold_files = [f for f in bold_files if f.entities["subject"] == subject]

        # Group files that share timing and differ only by reconstruction
        # (e.g. raw vs. rec-nordic): they get identical events.tsv content.
        groups_by_key = {}
        for f in sub_bold_files:
            key = (
                f.entities.get("session"),
                f.entities.get("task"),
                f.entities.get("acquisition"),
                f.entities.get("run"),
            )
            groups_by_key.setdefault(key, []).append(f)

        groups = []
        for key, files in groups_by_key.items():
            acq_time_strs = {f.get_metadata().get("AcquisitionTime") for f in files}
            acq_time_strs.discard(None)
            if not acq_time_strs:
                logger.warning("No AcquisitionTime metadata for %s %s, skipping.", sub_label, key)
                continue
            groups.append({
                "key": key,
                "acquisition_time": acquisition_local_time(sorted(acq_time_strs)[0]),
                "bold_files": files,
            })

        logs = []
        for jp in find_log_jsons(logfiles_dir, sub_label):
            with open(jp) as f:
                log_data = json.load(f)
            logs.append({
                "json_path": jp,
                "local_time": log_start_local_time(log_data),
                "log_data": log_data,
            })

        pairs, unmatched = match_logs_to_groups(logs, groups)

        for group_idx in unmatched:
            warn_unmatched(groups[group_idx], groups)

        for log_idx, group_idx in pairs:
            log_entry = logs[log_idx]
            group = groups[group_idx]
            events = trials_to_events(log_entry["log_data"])
            for bold_file in group["bold_files"]:
                write_events_tsv(events, bold_file)


if __name__ == "__main__":
    main()
