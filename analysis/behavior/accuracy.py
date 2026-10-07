#!/usr/bin/env python

import argparse
import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent

DEFAULT_DATA_DIR = "/gpfs01/bartels/group/ykaraca/arc-fmri"
LOGFILES_SUBPATH = Path("bids") / "sourcedata" / "experimental_logfiles"
LOG_PATTERN = re.compile(r"^log_(p\d+)_(\d{8}T\d{6})\.json$")
DEFAULT_OUT = HERE / "results"

# --------------------------------------------------------------------------- #
# Loading                                                                     #
# --------------------------------------------------------------------------- #

def find_logs(root: Path, subjects: list[str] | None) -> dict[str, list[Path]]:
    """Return {participant: [log paths sorted by timestamp]}."""
    logs: dict[str, list[tuple[str, Path]]] = {}
    for path in root.rglob("log_p*.json"):
        m = LOG_PATTERN.match(path.name)
        if not m:
            continue
        participant, stamp = m.groups()
        if subjects and participant not in subjects:
            continue
        logs.setdefault(participant, []).append((stamp, path))
    return {p: [path for _, path in sorted(items)] for p, items in sorted(logs.items())}


def load_trials(logs: dict[str, list[Path]]) -> pd.DataFrame:
    rows = []
    for participant, paths in logs.items():
        for session, path in enumerate(paths, start=1):
            data = json.loads(path.read_text(encoding="utf-8"))
            for t in data["trials"]:
                rows.append(
                    {
                        "participant": data.get("participant", participant),
                        "session": session,
                        "logfile": path.name,
                        "block": t["block_index"],
                        "family": t["block_family"],
                        "rule": t["rule"],
                        "context": t["context"],
                        "trial_role": t["trial_role"],
                        "trial_index": t["trial_index"],
                        "correct_answer": t["correct"],
                        "response": t["resp"],
                        "is_correct": t["is_correct"],
                        "rt": t["rt"],
                    }
                )
    df = pd.DataFrame(rows)

    # Decision trials only; is_correct is [] on initial trials, bool on decision trials
    df = df[df["trial_role"] == "decision"].copy()
    df["is_correct"] = df["is_correct"].astype(bool)
    df["timeout"] = df["response"] == "timeout"
    df["rt"] = pd.to_numeric(df["rt"], errors="coerce")
    return df.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Summaries                                                                   #
# --------------------------------------------------------------------------- #

def summarise(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    def stats(g: pd.DataFrame) -> pd.Series:
        answered = g[~g["timeout"]]
        correct = g[g["is_correct"]]
        return pd.Series(
            {
                "n_trials": len(g),
                "n_correct": int(g["is_correct"].sum()),
                "n_timeouts": int(g["timeout"].sum()),
                "accuracy": g["is_correct"].mean(),
                "rt_mean": answered["rt"].mean(),
                "rt_median": answered["rt"].median(),
                "rt_sd": answered["rt"].std(),
                "rt_mean_correct": correct["rt"].mean(),
            }
        )

    if not by:  # everything pooled
        table = stats(df).to_frame().T
    else:
        table = df.groupby(by, sort=True).apply(stats, include_groups=False).reset_index()

    count_cols = ["n_trials", "n_correct", "n_timeouts"]
    table[count_cols] = table[count_cols].astype(int)
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--logfiles-dir", type=Path, help="override the experimental_logfiles folder")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output folder (default: {DEFAULT_OUT})")
    parser.add_argument("--subjects", nargs="*", help="only these participants, e.g. p05 p06")
    args = parser.parse_args()

    root = args.logfiles_dir or Path(os.environ.get("ARC_DATA_DIR", DEFAULT_DATA_DIR)) / LOGFILES_SUBPATH
    if not root.is_dir():
        raise SystemExit(f"Logfiles folder not found: {root}")

    logs = find_logs(root, args.subjects)
    if not logs:
        raise SystemExit(f"No log_pXX_*.json files found under {root}")
    print(f"Found {sum(len(v) for v in logs.values())} log files for {len(logs)} participants.")

    df = load_trials(logs)

    summaries = {
        "overall": ["participant"],
        "by_session": ["participant", "session"],
        "by_block": ["participant", "session", "block", "family"],
        "by_family": ["participant", "family"],
        "by_rule": ["participant", "family", "rule"],
    }

    args.out.mkdir(parents=True, exist_ok=True)

    for name, by in summaries.items():
        table = summarise(df, by)
        table.to_csv(args.out / f"{name}.csv", index=False)
        if name in {"overall", "by_family"}:
            print(f"\n=== {name} ===")
            print(table.round(3).to_string(index=False))



if __name__ == "__main__":
    main()