#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=12
#SBATCH --mem=8G
#SBATCH --time=24:00:00
#SBATCH --job-name=arc-fmri_func
# --output/--error/--array/--dependency are set by submit_fmriprep.sh
#
# Stage 2 of 2: functional processing for one reconstruction (raw or
# NORDIC), submitted with --dependency=afterok on fmriprep_anat.slurm so it
# only starts once that subject's FreeSurfer recon-all has actually
# finished. Always skips recon-all itself (--fs-no-reconall) and reuses the
# anat stage's output (--fs-subjects-dir) instead of recomputing it -- the
# raw and NORDIC runs are otherwise fully independent of each other and can
# run concurrently once the anat stage completes.
#
# Env vars set by submit_fmriprep.sh:
#   RUN_LABEL         -- "raw", "nordic" or "nordicphase"; keeps this run's working
#                        directory separate from the other reconstruction's
#                        concurrent run (a shared nipype workdir is not
#                        safe for two processes writing at once)
#   BIDS_FILTER_FILE  -- path to a bids-filter-file selecting which
#                        reconstruction's bold runs to process
#   DUMMY_SCANS       -- optional; overrides fMRIPrep's automatic
#                        non-steady-state-volume detection when set

set -euo pipefail

set -o allexport
source "$ENV_FILE"
set +o allexport

SUB_ID=$(printf "sub-%02d" $SLURM_ARRAY_TASK_ID)
echo "$SUB_ID ($RUN_LABEL functional, reusing existing FreeSurfer recon)"

FMRIPREP_ARGS=(
    --bold2anat-dof 6
    --output-spaces T1w fsaverage MNI152NLin2009cAsym:res-2
    --nthreads 96
    --omp-nthreads 48
    --mem-mb 8000
    --slice-time-ref .5
    --fs-license-file /opt/freesurfer/license.txt
    --participant-label $SUB_ID
    -w /workdir
    --fs-no-reconall
    --fs-subjects-dir /out/sourcedata/freesurfer
    --bids-filter-file "/preprocessing/$(basename "$BIDS_FILTER_FILE")"
)

if [ -n "${DUMMY_SCANS:-}" ]; then
    FMRIPREP_ARGS+=(--dummy-scans "$DUMMY_SCANS")
fi

# docker run --rm --user "$(id -u):$(id -g)" \
#     -v $FREESURFER_HOME/license.txt:/opt/freesurfer/license.txt:ro \
#     -v $BIDS_ROOT_DIR:/data:ro \
#     -v $BIDS_ROOT_DIR/derivatives:/out \
#     -v $BIDS_ROOT_DIR/sourcedata/fmriprep_workdir/$RUN_LABEL:/workdir \
#     -v $ANALYSIS_DIR/preprocessing:/preprocessing:ro \
#     nipreps/fmriprep:25.2.5 /data /out participant \
#     "${FMRIPREP_ARGS[@]}"

mkdir -p "$BIDS_ROOT_DIR/sourcedata/fmriprep_workdir/$SUB_ID/$RUN_LABEL"

docker run --rm --user "$(id -u):$(id -g)" \
    -v $FREESURFER_HOME/license.txt:/opt/freesurfer/license.txt:ro \
    -v $BIDS_ROOT_DIR:/data:ro \
    -v $BIDS_ROOT_DIR/derivatives:/out \
    -v $BIDS_ROOT_DIR/sourcedata/fmriprep_workdir/$SUB_ID/$RUN_LABEL:/workdir \
    -v $ANALYSIS_DIR/preprocessing:/preprocessing:ro \
    nipreps/fmriprep:25.2.5 /data /out participant \
    "${FMRIPREP_ARGS[@]}"
