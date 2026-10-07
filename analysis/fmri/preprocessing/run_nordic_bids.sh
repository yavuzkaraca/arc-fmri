#!/usr/bin/env bash
# One-command NORDIC launcher (headless MATLAB, no GUI interaction).
#
#   ./run_nordic_bids.sh                 # all subjects
#   ./run_nordic_bids.sh sub-03          # one subject
#   ./run_nordic_bids.sh sub-01 sub-07   # several subjects
#
# Run this from the folder that contains NORDIC_denoising.m, run_nordic_bids.m
# and NIFTI_NORDIC.m (and where ../.env holds BIDS_ROOT_DIR).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set -o allexport
source "$SCRIPT_DIR/../.env"
set +o allexport

if [ "$#" -eq 0 ]; then
    ARG="'all'"
else
    # Build a MATLAB cellstr: {'sub-01','sub-07'}
    ARG="{"
    for s in "$@"; do ARG="${ARG}'${s}',"; done
    ARG="${ARG%,}}"
fi

matlab -nodisplay -nosplash -batch "cd('$ANALYSIS_DIR/preprocessing/'), run_nordic_bids(${ARG})"
