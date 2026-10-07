# ARC-fMRI

## Purpose

This project investigates how the choice of fMRI acquisition protocol affects
data quality, using visual puzzles from the Abstraction and Reasoning Corpus
(ARC) as stimuli. Participants alternate between two trial types — inferring
a transformation rule (`inference`) and applying a previously shown rule
(`application`) — while several MRI sequences (differing in voxel size,
reconstruction, and other acquisition parameters) are compared against each
other on metrics like tSNR and GLM-derived contrast sensitivity, to inform
which protocol is best suited for future studies of this kind.

## Environment setup

1. Create the conda environment from `environment.yml`:
   ```bash
   conda env create -f environment.yml
   conda activate ARC-fMRI
   ```
2. Create a `.env` file in the project root (never committed — see
   `.gitignore`) defining the server paths used throughout the codebase:
   ```
   DATA_DIR="/path/to/project/storage"
   BIDS_ROOT_DIR="${DATA_DIR}/bids"
   SOURCE_DATA_DIR="${BIDS_ROOT_DIR}/sourcedata"
   ANALYSIS_DIR="/path/to/this/repo"
   HPC_LOG_DIR="${DATA_DIR}/logs"
   FREESURFER_LICENSE="/path/to/freesurfer/license.txt"
   ```
   Use `${VAR}` (not bare `$VAR`) for any interpolation — this form is read
   correctly both when the file is `source`d by bash scripts and when it's
   loaded by Python's `python-dotenv`.
3. fMRIPrep and NORDIC denoising run via Docker and MATLAB respectively,
   not through the conda environment — both need to be available on
   whichever machine runs the preprocessing scripts.

## Processing steps

Run in order; each stage is safe to re-run (existing outputs are detected
and skipped or deterministically regenerated, so nothing needs to be run
exactly once).

1. **DICOM → BIDS conversion** (`bids-conversion/`). For each new
   subject/session, inspect the raw series with `dcm2bids_helper` (or `jq`
   against already-converted sidecars) to identify the right `SeriesDescription`
   / `SeriesNumber` / `PhaseEncodingDirection` criteria, write a
   `dcm2bids_config_sub-XX_ses-YY.json`, and add an invocation block to
   `convert_to_bids.sh`.
2. **NORDIC denoising** (`preprocessing/run_nordic_bids.sh sub-XX`) — writes
   `rec-nordic` BOLD copies alongside the raw runs in each subject's `func/`
   folder.
3. **fMRIPrep preprocessing** (`preprocessing/submit_fmriprep.sh <subject_number>
   [--dummy-scans N]`) — a two-stage SLURM pipeline: FreeSurfer recon-all
   runs once per subject, then the raw and NORDIC reconstructions are each
   preprocessed independently, reusing that recon rather than repeating it.
4. **Behavioural events → BIDS `_events.tsv`** (`src/`):
   `mat2json_trials.m` converts the Psychtoolbox `.mat` logs to JSON (needed
   because MATLAB `string` objects aren't readable from Python), then
   `parse_mat_events.py` matches each log to its BIDS run by acquisition
   timestamp and writes the events files. `visualize_events.py` renders a
   QC timeline per run — worth a look before trusting the output.
5. **Analysis** (`notebooks/`) — first-level GLMs and protocol comparisons,
   e.g. `glm_protocol_comparison.ipynb`.
