#!/usr/bin/env python
"""Turn the trial-level behaviour CSV into the table HDDM needs.
 
Reads   data/behavior_trials.csv   (made by build_trials.py)
Writes  data/ddm_trials.csv        (local, git-ignored)
 
Accuracy coding: the two "choices" are CORRECT (response = 1) and WRONG (response = 0),
so the upper boundary is the correct answer and drift rate v measures how well the
evidence supports the right answer. Error RTs stay positive.
RT is in seconds from stimulus onset.
 
Columns
  subj_idx   participant (p05, p06, ...)
  rt         reaction time in seconds
  response   1 = correct, 0 = wrong
  family, rule, session, block, trial_index   as in behavior_trials.csv
  session_z  session number centred and scaled (for regressions on session)
  stim       the correct answer ("same" / "different"), only needed for bias models
 
Dropped, and reported: timeouts (no RT) and RTs faster than --min-rt.
 
Usage:  python build_ddm_data.py [--data CSV] [--out CSV] [--min-rt 0.2]
"""
 
import argparse
from pathlib import Path
 
import pandas as pd
 
from common import DDM_TRIALS_CSV, TRIALS_CSV
 
MIN_TRIALS_PER_CELL = 20  # warn below this many trials per participant x family
 
 
def build_ddm_table(trials: pd.DataFrame, min_rt: float) -> pd.DataFrame:
    n_timeouts = int(trials["timeout"].sum())
    answered = trials[~trials["timeout"]]
    too_fast = answered["rt"] < min_rt
    print(f"{len(trials)} decision trials: dropping {n_timeouts} timeouts "
          f"and {int(too_fast.sum())} answers faster than {min_rt} s")
    kept = answered[~too_fast]
 
    table = pd.DataFrame({
        "subj_idx": kept["participant"],
        "rt": kept["rt"],
        "response": kept["is_correct"].astype(int),
        "family": kept["family"],
        "rule": kept["rule"],
        "session": kept["session"],
        "block": kept["block"],
        "trial_index": kept["trial_index"],
        "stim": kept["correct_answer"],
    })
    table["session_z"] = (table["session"] - table["session"].mean()) / table["session"].std()
    return table.reset_index(drop=True)
 
 
def report(table: pd.DataFrame) -> None:
    per_participant = table.groupby("subj_idx").agg(
        trials=("rt", "size"), accuracy=("response", "mean"),
        rt_median=("rt", "median"), rt_q05=("rt", lambda r: r.quantile(0.05)),
        rt_q95=("rt", lambda r: r.quantile(0.95)))
    print("\n" + per_participant.round(2).to_string())
 
    errors = table[table["response"] == 0]
    print(f"\nerror trials: {len(errors)} ({len(errors) / len(table):.1%}); "
          f"median RT correct {table.loc[table['response'] == 1, 'rt'].median():.2f} s, "
          f"error {errors['rt'].median():.2f} s")
 
    cells = table.groupby(["subj_idx", "family"]).size()
    sparse = cells[cells < MIN_TRIALS_PER_CELL]
    for (participant, family), n in sparse.items():
        print(f"WARNING: {participant} has only {n} trials in family {family} "
              f"(< {MIN_TRIALS_PER_CELL}); family-wise estimates will lean on the group")
    low_errors = per_participant[per_participant["accuracy"] > 0.97]
    for participant in low_errors.index:
        print(f"WARNING: {participant} is above 97% accurate: very few errors constrain the "
              "boundary / drift estimates for this participant")
 
 
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=TRIALS_CSV)
    parser.add_argument("--out", type=Path, default=DDM_TRIALS_CSV)
    parser.add_argument("--min-rt", type=float, default=0.2, help="drop answers faster than this (s)")
    args = parser.parse_args()
    if not args.data.is_file():
        raise SystemExit(f"{args.data} not found - run build_trials.py first")
 
    table = build_ddm_table(pd.read_csv(args.data), args.min_rt)
    report(table)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)
    print(f"\nWrote {len(table)} trials -> {args.out}")
 
 
if __name__ == "__main__":
    main()