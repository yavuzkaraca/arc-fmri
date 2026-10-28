#!/usr/bin/env python
"""Summarise the trial-level behaviour into tables. No plotting here (see plot.py).

Reads   data/behavior_trials.csv   (made by build_trials.py)
Writes  results/descriptive/tables/*.csv

Subject tables (one row per participant and group; <name>_subject.csv)
  overall, session, session_family, family, rule
  columns: n_trials, n_correct, n_timeouts, accuracy, acc_lo, acc_hi (Wilson 95 %),
           rt_mean, rt_median, rt_sd, rt_lo, rt_hi (t-interval of the mean RT, answered trials);
           the session table also has rt_median_lo, rt_median_hi (bootstrap 95 % of the median).
Group tables (participant = unit; <name>_group.csv)
  session, session_family, family, rule
  columns: metric (accuracy | rt_median), the grouping columns, mean, lo, hi, n
           mean across participants and its 95 % t-interval; n = participants contributing.

Within-participant intervals treat trials as independent, so they are a bit optimistic.

Usage:  python descriptive.py [--data CSV] [--out DIR]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from common import RESULTS_DIR, TRIALS_CSV

Z95 = stats.norm.ppf(0.975)

SUBJECT_TABLES = {  # table name -> grouping columns
    "overall": ["participant"],
    "session": ["participant", "session"],
    "session_family": ["participant", "session", "family"],
    "family": ["participant", "family"],
    "rule": ["participant", "family", "rule"],
}
GROUP_TABLES = {  # table name -> (grouping columns across participants, metrics)
    "session": (["session"], ["accuracy", "rt_median"]),
    "session_family": (["session", "family"], ["accuracy", "rt_median"]),
    "family": (["family"], ["accuracy", "rt_median"]),
    "rule": (["family", "rule"], ["accuracy"]),
}


def summarise(trials: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Accuracy and RT statistics for every group in `by`."""
    def summarise_group(g: pd.DataFrame) -> pd.Series:
        answered = g[~g["timeout"]]
        return pd.Series({
            "n_trials": len(g),
            "n_correct": int(g["is_correct"].sum()),
            "n_timeouts": int(g["timeout"].sum()),
            "accuracy": g["is_correct"].mean(),
            "rt_mean": answered["rt"].mean(),
            "rt_median": answered["rt"].median(),
            "rt_sd": answered["rt"].std(),
        })

    table = trials.groupby(by, sort=True).apply(summarise_group, include_groups=False).reset_index()
    counts = ["n_trials", "n_correct", "n_timeouts"]
    table[counts] = table[counts].astype(int)
    return table


def wilson_interval(n_correct, n_trials):
    """95 % Wilson score interval for a proportion."""
    k, n = np.asarray(n_correct, float), np.asarray(n_trials, float)
    p = k / n
    denom = 1 + Z95**2 / n
    centre = (p + Z95**2 / (2 * n)) / denom
    half = Z95 * np.sqrt(p * (1 - p) / n + Z95**2 / (4 * n**2)) / denom
    return np.clip(centre - half, 0, 1), np.clip(centre + half, 0, 1)


def t_interval(values) -> tuple[float, float, float, int]:
    """Mean, 95 % t-interval (lo, hi) and n of the non-NaN values; interval is NaN if n < 2."""
    v = np.asarray(values, float)
    v = v[~np.isnan(v)]
    n = len(v)
    if n == 0:
        return np.nan, np.nan, np.nan, 0
    mean = v.mean()
    if n < 2:
        return mean, np.nan, np.nan, n
    half = stats.t.ppf(0.975, n - 1) * v.std(ddof=1) / np.sqrt(n)
    return mean, mean - half, mean + half, n


def add_intervals(table: pd.DataFrame) -> pd.DataFrame:
    """Add Wilson accuracy (acc_lo/hi) and t-interval mean RT (rt_lo/hi) columns."""
    table = table.copy()
    table["acc_lo"], table["acc_hi"] = wilson_interval(table["n_correct"], table["n_trials"])
    answered = (table["n_trials"] - table["n_timeouts"]).to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        half = stats.t.ppf(0.975, answered - 1) * table["rt_sd"] / np.sqrt(answered)
    table["rt_lo"], table["rt_hi"] = table["rt_mean"] - half, table["rt_mean"] + half
    return table


def bootstrap_median_intervals(trials: pd.DataFrame, n_boot: int = 2000, seed: int = 0) -> pd.DataFrame:
    """Percentile-bootstrap 95 % interval of the median RT per participant x session."""
    rng = np.random.default_rng(seed)
    rows = []
    for (participant, session), g in trials[~trials["timeout"]].groupby(["participant", "session"]):
        rts = g["rt"].dropna().to_numpy()
        lo = hi = np.nan
        if len(rts) >= 2:
            medians = np.median(rng.choice(rts, size=(n_boot, len(rts)), replace=True), axis=1)
            lo, hi = np.percentile(medians, [2.5, 97.5])
        rows.append((participant, session, lo, hi))
    return pd.DataFrame(rows, columns=["participant", "session", "rt_median_lo", "rt_median_hi"])


def across_participants(subject: pd.DataFrame, by: list[str], metrics: list[str]) -> pd.DataFrame:
    """Mean across participants and 95 % t-interval for each metric and group in `by`."""
    rows = []
    for metric in metrics:
        for keys, g in subject.groupby(by):
            keys = keys if isinstance(keys, tuple) else (keys,)
            mean, lo, hi, n = t_interval(g[metric])
            rows.append({**dict(zip(by, keys)), "metric": metric, "mean": mean, "lo": lo, "hi": hi, "n": n})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=TRIALS_CSV, help="trial-level CSV from build_trials.py")
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "descriptive" / "tables",
                        help="folder for the tables")
    args = parser.parse_args()
    if not args.data.is_file():
        raise SystemExit(f"{args.data} not found - run build_trials.py first")
    args.out.mkdir(parents=True, exist_ok=True)

    trials = pd.read_csv(args.data)
    subject = {name: add_intervals(summarise(trials, by)) for name, by in SUBJECT_TABLES.items()}
    subject["session"] = subject["session"].merge(bootstrap_median_intervals(trials),
                                                  on=["participant", "session"], how="left")
    for name, table in subject.items():
        table.to_csv(args.out / f"{name}_subject.csv", index=False)
        print("wrote", args.out / f"{name}_subject.csv")
    for name, (by, metrics) in GROUP_TABLES.items():
        table = across_participants(subject[name], by, metrics)
        table.to_csv(args.out / f"{name}_group.csv", index=False)
        print("wrote", args.out / f"{name}_group.csv")


if __name__ == "__main__":
    main()
