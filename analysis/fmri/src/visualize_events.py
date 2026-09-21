"""QC visualization for BIDS _events.tsv files produced by parse_mat_events.py.

For each _events.tsv found under BIDS_ROOT_DIR, renders a two-panel PNG:
top panel is a trial timeline (colored by trial_type, hatched for incorrect
responses), bottom panel is response_time per trial on the same time axis.
Meant as a quick visual sanity check that onsets/durations/accuracy look
right before trusting the TSVs in a GLM.

Safe to re-run: each PNG is regenerated deterministically from its events.tsv.
"""

import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv

COLOR_INFERENCE = "#2a78d6"   # categorical slot 1 (blue)
COLOR_APPLICATION = "#1baf7a"  # categorical slot 2 (aqua)
COLOR_MUTED = "#898781"
COLOR_GRIDLINE = "#e1e0d9"
COLOR_BASELINE = "#c3c2b7"
COLOR_TEXT = "#0b0b0b"

TRIAL_TYPE_COLORS = {"inference": COLOR_INFERENCE, "application": COLOR_APPLICATION}


def plot_run(events: pd.DataFrame, title: str, out_path: Path):
    fig, (ax_timeline, ax_rt) = plt.subplots(
        2, 1, figsize=(14, 4), sharex=True, height_ratios=[1, 1.2],
        gridspec_kw={"hspace": 0.15},
    )

    # --- top panel: trial timeline ---
    for _, row in events.iterrows():
        color = TRIAL_TYPE_COLORS[row["trial_type"]]
        hatch = "////" if row["accuracy"] == 0 else None
        ax_timeline.broken_barh(
            [(row["onset"], row["duration"])], (0, 1),
            facecolor=color, edgecolor="white", linewidth=0.5,
            hatch=hatch, alpha=0.9,
        )

    for block_start in events.groupby("block_id")["onset"].min():
        ax_timeline.axvline(block_start, color=COLOR_GRIDLINE, linewidth=0.8, zorder=0)

    ax_timeline.set_ylim(0, 1)
    ax_timeline.set_yticks([])
    ax_timeline.spines[["left", "top", "right"]].set_visible(False)
    ax_timeline.spines["bottom"].set_color(COLOR_BASELINE)
    ax_timeline.set_title(title, fontsize=11, color=COLOR_TEXT, loc="left")

    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=c, label=t)
        for t, c in TRIAL_TYPE_COLORS.items()
    ]
    legend_handles.append(
        plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor=COLOR_MUTED,
                       hatch="////", label="incorrect response")
    )
    ax_timeline.legend(
        handles=legend_handles, loc="upper left", bbox_to_anchor=(1.005, 1.05),
        frameon=False, fontsize=9,
    )

    # --- bottom panel: response time per trial ---
    decision = events[events["accuracy"] != "n/a"].copy()
    decision = decision[decision["response_time"] != "n/a"]
    for trial_type, color in TRIAL_TYPE_COLORS.items():
        sub = decision[decision["trial_type"] == trial_type]
        ax_rt.scatter(
            sub["onset"], sub["response_time"].astype(float),
            s=22, color=color, alpha=0.9, edgecolor="white", linewidth=0.4,
            zorder=3,
        )

    ax_rt.set_ylabel("response time (s)", fontsize=9, color=COLOR_MUTED)
    ax_rt.set_xlabel("time since scan onset (s)", fontsize=9, color=COLOR_MUTED)
    ax_rt.tick_params(colors=COLOR_MUTED, labelsize=8)
    ax_rt.spines[["top", "right"]].set_visible(False)
    ax_rt.spines[["left", "bottom"]].set_color(COLOR_BASELINE)
    ax_rt.grid(axis="y", color=COLOR_GRIDLINE, linewidth=0.6, zorder=0)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    load_dotenv()
    bids_root = Path(os.environ["BIDS_ROOT_DIR"])
    qc_dir = bids_root / "derivatives" / "events_qc"

    events_files = sorted(
        p for p in bids_root.glob("sub-*/ses-*/func/*_events.tsv")
        if not p.name.startswith("._")
    )
    print(f"Found {len(events_files)} events.tsv file(s).")

    for events_path in events_files:
        events = pd.read_csv(events_path, sep="\t")
        rel = events_path.relative_to(bids_root)
        out_path = qc_dir / rel.with_suffix(".png")
        plot_run(events, title=events_path.stem, out_path=out_path)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
