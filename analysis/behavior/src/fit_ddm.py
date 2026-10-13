#!/usr/bin/env python
"""Fit hierarchical drift diffusion models with HDDM (accuracy coding).
 
Reads   data/ddm_trials.csv   (made by build_ddm_data.py)
Writes  results/ddm/tables/<model>_stats.csv     posterior summary of every parameter
        results/ddm/tables/<model>_rhat.csv      R-hat per parameter (Gelman-Rubin)
        results/ddm/tables/model_summary.csv     one row per model: samples, chains, DIC, convergence
        results/ddm/fits/<model>/                raw chains and traces (large, not for reading)
 
Models
  base     v, a, t estimated per participant, drawn from group distributions
  family   drift rate v depends on rule family      (depends_on={"v": "family"})
  session  v ~ family + session (regression: does evidence quality change over sessions?)
  session_all   v, a and t each ~ session (does learning show up in evidence, boundary or non-decision time?)
 
Parameters: v = drift rate (evidence quality for the correct answer), a = boundary separation
(caution), t = non-decision time (s). Outliers are handled by a 5 % uniform mixture.
Running a model again overwrites its previous results; other models are untouched.
 
Run it with the HDDM environment (environment-hddm.yml), not the analysis environment.
Chains are run one after another; use more chains for a trustworthy R-hat.
 
Usage:  press Run (uses the MODEL / SAMPLES / BURN / CHAINS block below), or
        python fit_ddm.py --model family --samples 6000 --burn 2000 --chains 4
"""
from __future__ import annotations
 
import argparse
from datetime import datetime
from pathlib import Path
 
import hddm
import kabuki
import pandas as pd
 
from common import DDM_TRIALS_CSV, RESULTS_DIR
 
# --- settings used when you press the Run button (no command-line arguments) ---------------
MODEL = "session"                        # base | family | session | session_all
SAMPLES, BURN, CHAINS = 900, 300, 2   # quick test run; use 6000, 2000, 4 for a real fit
# -------------------------------------------------------------------------------------------
 
P_OUTLIER = 0.05
INCLUDE = ["v", "a", "t"]  # HDDM >= 0.9.8 estimates only what is listed here
RHAT_LIMIT = 1.1
 
 
def make_model(name: str, data: pd.DataFrame):
    if name == "base":
        return hddm.HDDM(data, include=INCLUDE, p_outlier=P_OUTLIER)
    if name == "family":
        return hddm.HDDM(data, include=INCLUDE, depends_on={"v": "family"}, p_outlier=P_OUTLIER)
    if name == "session":
        return hddm.HDDMRegressor(data, "v ~ C(family) + session_z", include=INCLUDE, p_outlier=P_OUTLIER)
    if name == "session_all":
        return hddm.HDDMRegressor(data, ["v ~ session_z", "a ~ session_z", "t ~ session_z"],
                                  include=INCLUDE, p_outlier=P_OUTLIER)
    raise SystemExit(f"unknown model {name!r}")
 
 
def update_model_summary(path: Path, row: dict) -> None:
    """Keep one row per model in model_summary.csv (replace this model's old row)."""
    table = pd.read_csv(path) if path.is_file() else pd.DataFrame()
    if len(table):
        table = table[table["model"] != row["model"]]
    table = pd.concat([table, pd.DataFrame([row])], ignore_index=True).sort_values("model")
    table.to_csv(path, index=False)
 
 
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", choices=["base", "family", "session", "session_all"], default=MODEL)
    parser.add_argument("--data", type=Path, default=DDM_TRIALS_CSV)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "ddm", help="the results/ddm folder")
    parser.add_argument("--samples", type=int, default=SAMPLES)
    parser.add_argument("--burn", type=int, default=BURN)
    parser.add_argument("--chains", type=int, default=CHAINS)
    args = parser.parse_args()
 
    data = pd.read_csv(args.data)
    fits_dir = args.out / "fits" / args.model
    tables_dir = args.out / "tables"
    fits_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
 
    models = []
    for chain in range(args.chains):
        print(f"\n=== {args.model}: chain {chain + 1}/{args.chains} ===")
        model = make_model(args.model, data)
        model.find_starting_values()
        model.sample(args.samples, burn=args.burn, dbname=str(fits_dir / f"traces_chain{chain}.db"), db="pickle")
        model.save(str(fits_dir / f"model_chain{chain}"))
        models.append(model)
 
    combined = kabuki.utils.concat_models(models)
    combined.gen_stats().to_csv(tables_dir / f"{args.model}_stats.csv")
    rhat = pd.Series(hddm.analyze.gelman_rubin(models), name="r_hat")
    rhat.to_csv(tables_dir / f"{args.model}_rhat.csv")
    not_converged = rhat[rhat > RHAT_LIMIT]
 
    update_model_summary(tables_dir / "model_summary.csv", {
        "model": args.model, "samples": args.samples, "burn": args.burn, "chains": args.chains,
        "dic": round(float(combined.dic), 1), "n_parameters": len(rhat),
        "n_not_converged": len(not_converged), "not_converged": ";".join(not_converged.index),
        "fitted_at": datetime.now().isoformat(timespec="seconds"),
    })
    print(f"\n{args.model}: DIC {combined.dic:.1f}; {len(not_converged)} of {len(rhat)} parameters "
          f"with R-hat > {RHAT_LIMIT}")
    if len(not_converged):
        print("NOT CONVERGED:", ", ".join(not_converged.index[:10]))
 
 
if __name__ == "__main__":
    main()
 