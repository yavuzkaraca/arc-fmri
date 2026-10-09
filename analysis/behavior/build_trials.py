#!/usr/bin/env python
"""Merge all experimental log JSONs into ONE clean, trial-level CSV.

This is the single data product for the behavioural analysis. It is a local
file (data/ is git-ignored): everything else (summaries, plots) is computed
from it in memory.

One row = one DECISION trial (initial "ready" trials are dropped).

Columns
  participant     p05, p06, ...                      (from the file name)
  session         1, 2, ... by log timestamp within participant
  timestamp       when the log was started (from the file name)
  logfile         source file name
  block           block index within the session
  family          rule family of the block
  rule            rule shown on this trial
  context         block context
  trial_index     trial position within the block
  correct_answer  "same" / "different"
  response        "same" / "different" / "timeout"
  is_correct      bool; a timeout counts as incorrect
  timeout         bool
  rt              reaction time in s; empty for timeouts

Usage:  python build_trials.py [--logfiles-dir DIR] [--out FILE] [--subjects p05 p06]
"""

import argparse
import json
import os
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent

DEFAULT_DATA_DIR = "/gpfs01/bartels/group/ykaraca/arc-fmri"
LOGFILES_SUBPATH = Path("bids") / "sourcedata" / "experimental_logfiles"
LOG_PATTERN = re.compile(r"^log_(p\d+)_(\d{8}T\d{6})\.json$")
DEFAULT_OUT = HERE / "data" / "behavior_trials.csv"

COLUMNS = [
    "participant", "session", "timestamp", "logfile", "block", "family", "rule",
    "context", "trial_index", "correct_answer", "response", "is_correct", "timeout", "rt",
]


def warn(msg: str) -> None:
    print(f"WARNING: {msg}")


def find_logs(root: Path, subjects: list[str] | None) -> dict[str, list[tuple[str, Path]]]:
    """Return {participant: [(timestamp, path), ...]} sorted by timestamp."""
    logs: dict[str, list[tuple[str, Path]]] = {}
    for path in root.rglob("log_p*.json"):
        m = LOG_PATTERN.match(path.name)
        if not m:
            warn(f"ignoring {path.name}: does not match log_pXX_YYYYMMDDTHHMMSS.json")
            continue
        participant, stamp = m.groups()
        if subjects and participant not in subjects:
            continue
        logs.setdefault(participant, []).append((stamp, path))

    # .mat logs that were never converted to .json are invisible to this script
    for mat in root.rglob("log_p*.mat"):
        if not mat.with_suffix(".json").exists():
            m = re.match(r"^log_(p\d+)_", mat.name)
            if m and (not subjects or m.group(1) in subjects):
                warn(f"{mat.name} has no .json next to it -> run mat2json_trials.m")

    return {p: sorted(items) for p, items in sorted(logs.items())}


def load_log(path: Path, participant: str, session: int, stamp: str) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "participant" in data and str(data["participant"]) != participant:
        warn(f"{path.name}: participant field is {data['participant']!r}, "
             f"file name says {participant!r} (using the file name)")
    timestamp = pd.to_datetime(stamp, format="%Y%m%dT%H%M%S")
    rows = []
    for t in data["trials"]:
        if t["trial_role"] != "decision":
            continue
        correct = t["correct"]
        resp = t["resp"]
        # is_correct is [] when the trial has no scorable answer, else a bool
        is_correct = t["is_correct"] if isinstance(t["is_correct"], bool) else None
        rows.append(
            {
                "participant": participant,
                "session": session,
                "timestamp": timestamp,
                "logfile": path.name,
                "block": t["block_index"],
                "family": t["block_family"],
                "rule": t["rule"],
                "context": t["context"],
                "trial_index": t["trial_index"],
                "correct_answer": correct,
                "response": resp,
                "is_correct": is_correct,
                "timeout": resp == "timeout",
                "rt": t["rt"],
            }
        )
    return rows


def build(logs: dict[str, list[tuple[str, Path]]]) -> pd.DataFrame:
    rows = []
    for participant, items in logs.items():
        for session, (stamp, path) in enumerate(items, start=1):
            try:
                rows.extend(load_log(path, participant, session, stamp))
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                raise SystemExit(f"Could not read {path}: {type(e).__name__}: {e}")

    df = pd.DataFrame(rows, columns=COLUMNS)

    # trials without a scorable answer cannot enter accuracy -> drop, loudly
    unscored = df["is_correct"].isna()
    if unscored.any():
        warn(f"dropping {int(unscored.sum())} decision trials without a scorable answer")
        df = df[~unscored].copy()
    df["is_correct"] = df["is_correct"].astype(bool)

    df["rt"] = pd.to_numeric(df["rt"], errors="coerce")
    df.loc[df["timeout"], "rt"] = float("nan")  # no meaningful RT on a timeout

    return df.sort_values(["participant", "session", "block", "trial_index"]).reset_index(drop=True)


def sanity_report(df: pd.DataFrame) -> None:
    per_session = df.groupby(["participant", "session"]).size()
    usual = per_session.mode().iloc[0]
    odd = per_session[per_session != usual]
    for (p, s), n in odd.items():
        warn(f"{p} session {s} has {n} decision trials (most sessions have {usual}) "
             f"- aborted or test run?")
    dup = df.duplicated(["participant", "session", "block", "trial_index"])
    if dup.any():
        warn(f"{int(dup.sum())} duplicated (participant, session, block, trial) rows")

    overview = df.groupby("participant").agg(
        sessions=("session", "nunique"),
        trials=("is_correct", "size"),
        timeouts=("timeout", "sum"),
        accuracy=("is_correct", "mean"),
    )
    print("\n" + overview.round(3).to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--logfiles-dir", type=Path, help="override the experimental_logfiles folder")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output CSV (default: {DEFAULT_OUT})")
    parser.add_argument("--subjects", nargs="*", help="only these participants, e.g. p05 p06")
    args = parser.parse_args()

    root = args.logfiles_dir or Path(os.environ.get("ARC_DATA_DIR", DEFAULT_DATA_DIR)) / LOGFILES_SUBPATH
    if not root.is_dir():
        raise SystemExit(f"Logfiles folder not found: {root}")

    logs = find_logs(root, args.subjects)
    if not logs:
        raise SystemExit(f"No log_pXX_*.json files found under {root}")
    print(f"Found {sum(len(v) for v in logs.values())} log files for {len(logs)} participants.")

    df = build(logs)
    sanity_report(df)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"\nWrote {len(df)} decision trials -> {args.out}")


if __name__ == "__main__":
    main()
