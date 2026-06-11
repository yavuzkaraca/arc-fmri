# ARC-fMRI Analysis

## Project purpose

This repository contains analysis code for an fMRI study using the Abstraction and Reasoning Corpus (ARC) as stimuli. The central goal is to compare fMRI data acquired under **different fMRI protocols/sequences** — evaluating which protocol yields the best data quality via tSNR, efficient SNR, and GLM-based t-values.

Downstream analyses include:
- Per-protocol tSNR maps and statistical comparisons (t-tests)
- First-level GLMs with stimulus-derived regressors (HRF-convolved onsets/durations)
- Protocol comparison at the ROI and whole-brain level

## Environment

Conda environment defined in `environment.yml` (name: `ARC-fMRI`, Python 3.13).

The environment already exists on this machine. To recreate from scratch:
```bash
conda env remove -n ARC-fMRI
conda env create -f environment.yml
```

## Server paths and privacy

All paths to data directories on the server are stored in `.env` (never committed to git).
`.env.example` shows the required variables with empty values — copy it to `.env` and fill in the paths.

**Never hardcode server paths in scripts or notebooks. Never commit `.env`.**

Load paths in Python:
```python
from dotenv import load_dotenv
import os
load_dotenv()
bids_root = os.environ["BIDS_ROOT"]
```

Key path variables: `BIDS_ROOT`, `RAW_DATA_DIR`, `MAT_FILES_DIR`, `FMRIPREP_OUTPUT_DIR`, `FMRIPREP_SIF`, `FREESURFER_LICENSE`.

## Data conventions

- Raw fMRI data is organised in **BIDS format**. `pybids.BIDSLayout` is the entry point for enumerating runs.
- **Some scans were aborted or failed.** A scan manifest CSV (to be created) with a `status` column (`ok / aborted / excluded`) gates all downstream steps — only `status=ok` runs are processed.
- Stimulus onset/duration/condition data is stored in **MATLAB `.mat` files** (location: `MAT_FILES_DIR`). Use `scipy.io.loadmat` for files saved under MATLAB < v7.3, `mat73.loadmat` for v7.3+ (HDF5). These are converted to BIDS `_events.tsv` files for use with nilearn's GLM.

## Preprocessing (fmriprep)

fmriprep is **not** installed in the conda environment. It runs as a **Singularity/Apptainer container** (`FMRIPREP_SIF`). Docker is not available on this HPC cluster.

Each fMRI protocol is preprocessed separately using a `--bids-filter-file` to restrict which BIDS runs fmriprep processes. fmriprep handles differing TRs, voxel sizes, and slice timing automatically per run.

The conda environment is used only for **post-fmriprep** analysis (nilearn, statistics, visualisation).

## Planned source files

- `src/parse_mat_events.py` — converts `.mat` stimulus files to BIDS `_events.tsv`
- `scripts/run_fmriprep.sh` — SLURM submission template for fmriprep
