"""Paths and constants shared by the behavioural analysis scripts.

Layout (this file lives in analysis/behavior/src/):
  data/                       trial-level inputs, git-ignored
  results/<analysis>/tables/  CSV summaries written by the analysis scripts
  results/<analysis>/plots/   PNGs written by plot.py
  results/ddm/fits/<model>/   raw HDDM chains (large)
"""
from __future__ import annotations

from pathlib import Path

BEHAVIOR_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BEHAVIOR_DIR / "data"
RESULTS_DIR = BEHAVIOR_DIR / "results"
TRIALS_CSV = DATA_DIR / "behavior_trials.csv"
DDM_TRIALS_CSV = DATA_DIR / "ddm_trials.csv"

CHANCE = 0.5  # same / different -> 50 % guessing
FAMILY_ORDER = ["arithmetic", "attraction", "expansion", "occlusion", "recolor"]


def family_list(table) -> list[str]:
    """Rule families present in `table`, in the canonical order (unknown ones last, sorted)."""
    present = set(table["family"])
    return [f for f in FAMILY_ORDER if f in present] + sorted(present - set(FAMILY_ORDER))
