#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=12
#SBATCH --mem=8G
#SBATCH --time=24:00:00
#SBATCH --job-name=arc-fmri_preproc
#SBATCH --array=1
# --output/--error are set by submit_fmriprep.sh (needs HPC_LOG_DIR from .env,
# which isn't available yet when #SBATCH directives are parsed)

set -euo pipefail

set -o allexport
source "$ENV_FILE"
set +o allexport

SUB_ID=$(printf "sub-%02d" $SLURM_ARRAY_TASK_ID)
echo $SUB_ID

docker run --rm --user "$(id -u):$(id -g)" \
    -v $FREESURFER_HOME/license.txt:/opt/freesurfer/license.txt:ro \
    -v $BIDS_ROOT_DIR:/data:ro \
    -v $BIDS_ROOT_DIR/derivatives:/out \
    -v $BIDS_ROOT_DIR/sourcedata/fmriprep_workdir:/workdir \
    -v $ANALYSIS_DIR/preprocessing:/preprocessing:ro \
    nipreps/fmriprep:25.2.5 /data /out participant \
    --bold2anat-dof 6 \
    --output-spaces T1w fsaverage MNI152NLin2009cAsym:res-2 \
    --nthreads 96 \
    --omp-nthreads 48 \
    --mem-mb 8000 \
    --slice-time-ref .5 \
    --fs-license-file /opt/freesurfer/license.txt \
    --participant-label $SUB_ID \
    -w /workdir \
    --fs-no-reconall \
    --bids-filter-file /preprocessing/bids_filter_nordic.json