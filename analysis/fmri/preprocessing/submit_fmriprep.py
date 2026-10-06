#!/usr/bin/env python3
"""Two-stage fMRIPrep pipeline for one subject:
  1. fmriprep_anat.slurm  -- anat-only + FreeSurfer recon-all, once.
  2. fmriprep_func.slurm  -- raw functional runs, plus NORDIC (rec-nordic) and
     NORDIC-with-phase (rec-nordicphase) runs if they exist for the subject, all
     submitted with --dependency=afterok on stage 1 so they start only
     once recon-all has finished, but run concurrently with each other
     from that point on (they're independent of one another; recon-all
     is the only part that would otherwise be duplicated).

Usage:
    ./submit_fmriprep.py <subject_number> [--dummy-scans N]
"""
import argparse
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_FILE = SCRIPT_DIR.parent / ".env"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subject_number", help="SLURM array index / subject number")
    parser.add_argument(
        "--dummy-scans",
        type=int,
        default=None,
        help="Override fMRIPrep's automatic non-steady-state-volume detection",
    )
    return parser.parse_args()


def sbatch(*args: str) -> str:
    """Run sbatch --parsable and return the job ID."""
    result = subprocess.run(
        ["sbatch", "--parsable", *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def main() -> None:
    args = parse_args()
    load_dotenv(ENV_FILE)
    hpc_log_dir = Path(os.environ["HPC_LOG_DIR"])
    hpc_log_dir.mkdir(parents=True, exist_ok=True)

    print(f"Submitting anat stage (T1w + FreeSurfer recon-all) for subject {args.subject_number}...")
    anat_jobid = sbatch(
        f"--array={args.subject_number}",
        f"--output={hpc_log_dir}/arc-fmri_anat_%a.out",
        f"--error={hpc_log_dir}/arc-fmri_anat_%a.err",
        f"--export=ALL,ENV_FILE={ENV_FILE}",
        str(SCRIPT_DIR / "fmriprep_anat.slurm"),
    )
    print(f"  -> job {anat_jobid}")

    # Only submit a NORDIC stage if that reconstruction exists for this subject.
    run_labels = ["raw"]
    sub_dir = Path(os.environ["BIDS_ROOT_DIR"]) / f"sub-{int(args.subject_number):02d}"
    for rec_label in ("nordic", "nordicphase"):
        if any(sub_dir.glob(f"**/func/*_rec-{rec_label}_*bold.nii.gz")):
            run_labels.append(rec_label)
        else:
            print(f"No rec-{rec_label} runs under {sub_dir}; skipping {rec_label} stage.")

    for run_label in run_labels:
        print(
            f"Submitting {run_label} functional stage for subject {args.subject_number} "
            f"(waiting on job {anat_jobid})..."
        )
        export = (
            f"ALL,ENV_FILE={ENV_FILE},RUN_LABEL={run_label},"
            f"BIDS_FILTER_FILE={SCRIPT_DIR / f'bids_filter_{run_label}.json'},"
            f"DUMMY_SCANS={args.dummy_scans if args.dummy_scans is not None else ''}"
        )
        func_jobid = sbatch(
            f"--array={args.subject_number}",
            f"--dependency=afterok:{anat_jobid}",
            f"--output={hpc_log_dir}/arc-fmri_func-{run_label}_%a.out",
            f"--error={hpc_log_dir}/arc-fmri_func-{run_label}_%a.err",
            f"--export={export}",
            str(SCRIPT_DIR / "fmriprep_func.slurm"),
        )
        print(f"  -> job {func_jobid}")


if __name__ == "__main__":
    main()
