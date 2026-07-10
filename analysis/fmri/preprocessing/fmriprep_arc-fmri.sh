
PBS_O_WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set -o allexport
source $PBS_O_WORKDIR/../.env
set +o allexport


SUB_ID="sub-01"
echo $SUB_ID


docker run --rm --user "$(id -u):$(id -g)" \
    -v $FREESURFER_HOME/license.txt:/opt/freesurfer/license.txt:ro \
    -v $BIDS_ROOT_DIR:/data:ro \
    -v $BIDS_ROOT_DIR/derivatives:/out \
    -v $BIDS_ROOT_DIR/sourcedata/fmriprep_workdir:/workdir \
    nipreps/fmriprep:25.2.5 /data /out participant \
    --bold2anat-dof 6 \
    --output-spaces T1w fsaverage MNI152NLin2009cAsym:res-2 \
    --nthreads 96 \
    --omp-nthreads 48 \
    --mem-mb 8000 \
    --slice-time-ref .5 \
    --fs-license-file /opt/freesurfer/license.txt \
    --participant-label $SUB_ID \
    -w /workdir