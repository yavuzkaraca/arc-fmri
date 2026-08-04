#!/usr/bin/bash
set -euo pipefail

# Resolve .env relative to this script's own location rather than the
# caller's current directory, so the script works no matter where it's
# invoked from (repo root, bids-conversion/, a SLURM job, etc.).
# To revert to the old cwd-relative behaviour, replace the two lines below
# with: source ../.env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set -o allexport
source "$SCRIPT_DIR/../.env"
set +o allexport

# After each dcm2bids run, warn about any files left unmatched in
# tmp_dcm2bids (i.e. sidecars with no, or more than one, matching
# description in the config) so a bad criteria pattern doesn't silently
# drop a sequence.
check_unmatched() {
    local unmatched
    unmatched=$(find "$BIDS_ROOT_DIR/tmp_dcm2bids" -maxdepth 1 -name '*.nii.gz' 2>/dev/null | wc -l)
    if [ "$unmatched" -gt 0 ]; then
        echo "WARNING: $unmatched unmatched file(s) left in $BIDS_ROOT_DIR/tmp_dcm2bids — check your config criteria." >&2
    fi
}

# ##### SUB-00 #####
# # 2026-04-27
# dcm2bids \
#     -d $SOURCE_DATA_DIR/2NH5-5UKW/NII \
#     -p sub-00 \
#     -c $ANALYSIS_DIR/bids-conversion/dcm2bids_config_sub-00.json \
#     -o $BIDS_ROOT_DIR \
#     --auto_extract_entities \
#     --skip_dcm2niix \
#     --force_dcm2bids

##### SUB-01 #####

# --- ses-01 --- #
# 2026-05-11

dcm2bids \
    -d $SOURCE_DATA_DIR/GQNB-QVYL/NII \
    -p sub-01 \
    -s ses-01 \
    -c $ANALYSIS_DIR/bids-conversion/dcm2bids_config_sub-01_ses-01.json \
    -o $BIDS_ROOT_DIR \
    --auto_extract_entities \
    --skip_dcm2niix \
    --force_dcm2bids \
    --clobber
check_unmatched

# --- ses-03 --- #
# 2026-06-10

dcm2bids \
    -d $SOURCE_DATA_DIR/DBO7-2Y3V/NII \
    -p sub-01 \
    -s ses-03 \
    -c $ANALYSIS_DIR/bids-conversion/dcm2bids_config_sub-01_ses-03.json \
    -o $BIDS_ROOT_DIR \
    --auto_extract_entities \
    --skip_dcm2niix \
    --force_dcm2bids \
    --clobber
check_unmatched

##### SUB-03 #####

# --- ses-01 --- #
# 2026-08-04

dcm2bids \
    -d $SOURCE_DATA_DIR/UYZF-NBPO/NII \
    -p sub-03 \
    -s ses-01 \
    -c $ANALYSIS_DIR/bids-conversion/dcm2bids_config_sub-03_ses-01.json \
    -o $BIDS_ROOT_DIR \
    --auto_extract_entities \
    --skip_dcm2niix \
    --force_dcm2bids \
    --clobber
check_unmatched
