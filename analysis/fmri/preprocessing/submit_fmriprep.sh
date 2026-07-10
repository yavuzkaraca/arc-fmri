#!/usr/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

set -o allexport
source "$SCRIPT_DIR/../.env"
set +o allexport

mkdir -p "$HPC_LOG_DIR"

sbatch \
    --output="$HPC_LOG_DIR/arc-fmri_preproc_%a.out" \
    --error="$HPC_LOG_DIR/arc-fmri_preproc_%a.err" \
    --export=ALL,ENV_FILE="$SCRIPT_DIR/../.env" \
    "$SCRIPT_DIR/fmriprep_arc-fmri.slurm"
