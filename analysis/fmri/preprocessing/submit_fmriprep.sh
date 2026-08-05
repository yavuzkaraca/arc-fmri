#!/usr/bin/bash
# Two-stage fMRIPrep pipeline for one subject:
#   1. fmriprep_anat.slurm  -- anat-only + FreeSurfer recon-all, once.
#   2. fmriprep_func.slurm  -- raw and NORDIC functional runs, both
#      submitted with --dependency=afterok on stage 1 so they start only
#      once recon-all has finished, but run concurrently with each other
#      from that point on (they're independent of one another; recon-all
#      is the only part that would otherwise be duplicated).
#
# Usage:
#   ./submit_fmriprep.sh <subject_number> [--dummy-scans N]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set -o allexport
source "$SCRIPT_DIR/../.env"
set +o allexport

usage() {
    echo "Usage: $0 <subject_number> [--dummy-scans N]" >&2
    exit 1
}

[ "$#" -ge 1 ] || usage
SUBJECT_NUM="$1"; shift

DUMMY_SCANS=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --dummy-scans) DUMMY_SCANS="$2"; shift 2 ;;
        *) usage ;;
    esac
done

mkdir -p "$HPC_LOG_DIR"

# echo "Submitting anat stage (T1w + FreeSurfer recon-all) for subject $SUBJECT_NUM..."
# ANAT_JOBID=$(sbatch --parsable \
#     --array="$SUBJECT_NUM" \
#     --output="$HPC_LOG_DIR/arc-fmri_anat_%a.out" \
#     --error="$HPC_LOG_DIR/arc-fmri_anat_%a.err" \
#     --export=ALL,ENV_FILE="$SCRIPT_DIR/../.env" \
#     "$SCRIPT_DIR/fmriprep_anat.slurm")
# echo "  -> job $ANAT_JOBID"

for RUN_LABEL in raw nordic; do
    # echo "Submitting $RUN_LABEL functional stage for subject $SUBJECT_NUM (waiting on job $ANAT_JOBID)..."
    # FUNC_JOBID=$(sbatch --parsable \
    #     --array="$SUBJECT_NUM" \
    #     --dependency=afterok:"$ANAT_JOBID" \
    #     --output="$HPC_LOG_DIR/arc-fmri_func-${RUN_LABEL}_%a.out" \
    #     --error="$HPC_LOG_DIR/arc-fmri_func-${RUN_LABEL}_%a.err" \
    #     --export=ALL,ENV_FILE="$SCRIPT_DIR/../.env",RUN_LABEL="$RUN_LABEL",BIDS_FILTER_FILE="$SCRIPT_DIR/bids_filter_${RUN_LABEL}.json",DUMMY_SCANS="$DUMMY_SCANS" \
    #     "$SCRIPT_DIR/fmriprep_func.slurm")

    FUNC_JOBID=$(sbatch --parsable \
        --array="$SUBJECT_NUM" \
        --output="$HPC_LOG_DIR/arc-fmri_func-${RUN_LABEL}_%a.out" \
        --error="$HPC_LOG_DIR/arc-fmri_func-${RUN_LABEL}_%a.err" \
        --export=ALL,ENV_FILE="$SCRIPT_DIR/../.env",RUN_LABEL="$RUN_LABEL",BIDS_FILTER_FILE="$SCRIPT_DIR/bids_filter_${RUN_LABEL}.json",DUMMY_SCANS="$DUMMY_SCANS" \
        "$SCRIPT_DIR/fmriprep_func.slurm")

    echo "  -> job $FUNC_JOBID"
done
