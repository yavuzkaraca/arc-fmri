#!/usr/bin/bash
set -o allexport
source ../.env
set +o allexport

##### SUB-00 #####
# 2026-04-27
dcm2bids \
    -d $SOURCE_DATA_DIR/2NH5-5UKW/NII \
    -p sub-00 \
    -c dcm2bids_config_sub-00.json \
    -o $BIDS_ROOT_DIR \
    --auto_extract_entities \
    --skip_dcm2niix \
    --force_dcm2bids

##### SUB-01 #####

# --- ses-01 --- #
# 2026-05-11

dcm2bids \
    -d $SOURCE_DATA_DIR/GQNB-QVYL/NII \
    -p sub-01 \
    -s ses-01 \
    -c dcm2bids_config_sub-01_ses-01.json \
    -o $BIDS_ROOT_DIR \
    --auto_extract_entities \
    --skip_dcm2niix \
    --force_dcm2bids

# --- ses-03 --- #
# 2026-06-10

dcm2bids \
    -d $SOURCE_DATA_DIR/DBO7-2Y3V/NII \
    -p sub-01 \
    -s ses-03 \
    -c dcm2bids_config_sub-01_ses-03.json \
    -o $BIDS_ROOT_DIR \
    --auto_extract_entities \
    --skip_dcm2niix \
    --force_dcm2bids

    