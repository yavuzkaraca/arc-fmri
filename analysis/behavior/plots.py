#!/usr/bin/env python
"""Plot the behavioural data. Writes PNGs only (no CSVs).
 
Reads   data/behavior_trials.csv   (made by build_trials.py)
Writes  results/plots/*.png
 
File names:  <scope>_<metric>_by_<x>[_family].png
  scope   group    one value per participant, summarised ACROSS participants
          subject  one panel / bar / row per participant
  metric  accuracy | rt (reaction time)
  x       overall | session | session_family | family | rule
 
Confidence intervals
  group plots      mean +- t-interval across participants (participant = unit)
  subject accuracy Wilson 95 % interval on that session's trials
  subject RT       percentile-bootstrap 95 % interval of the session median
  overall bars     Wilson (accuracy) / t-interval over answered trials (mean RT)
Within-participant intervals treat trials as independent, so they are a bit optimistic.
 
Usage:  python plots.py [--data CSV] [--out DIR]
"""
 
import argparse
from dataclasses import dataclass
from pathlib import Path
 
import matplotlib
 
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.transforms import blended_transform_factory
from scipy import stats
 
HERE = Path(__file__).resolve().parent
CHANCE = 0.5  # same / different -> 50 % guessing
Z95 = stats.norm.ppf(0.975)
FAMILY_ORDER = ["arithmetic", "attraction", "expansion", "occlusion", "recolor"]
 
# --- palette (light mode) ----------------------------------------------------
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
BLUE = "#2a78d6"    # accuracy
ORANGE = "#eb6834"  # reaction time
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CMAP = LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)
DASH = (0, (4, 3))
LEGEND_STYLE = dict(frameon=False, labelcolor=INK2, fontsize=8.5, handlelength=1.8, columnspacing=1.2)
 
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": GRID,
    "xtick.color": INK2, "ytick.color": INK2, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
})
 
 
@dataclass(frozen=True)
class Metric:
    """What a session plot shows: columns, colour and axis style."""
    name: str    # used in titles
    value: str   # column with the point estimate
    lo: str      # columns with the subject-level interval
    hi: str
    color: str
    ylabel: str
    is_pct: bool
 
 
ACCURACY = Metric("Accuracy", "accuracy", "acc_lo", "acc_hi", BLUE, "accuracy", True)
RT = Metric("Median reaction time", "rt_median", "rt_median_lo", "rt_median_hi", ORANGE, "seconds", False)
 
 
# --------------------------------------------------------------------------- #
# Summaries and statistics                                                    #
# --------------------------------------------------------------------------- #
GROUPINGS = {
    "overall": ["participant"],
    "session": ["participant", "session"],
    "session_family": ["participant", "session", "family"],
    "family": ["participant", "family"],
    "rule": ["participant", "family", "rule"],
}
 
 
def summarise(trials: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Accuracy and RT statistics for every group in `by` (decision trials in, one row per group out)."""
    def summarise_group(g: pd.DataFrame) -> pd.Series:
        answered = g[~g["timeout"]]
        return pd.Series({
            "n_trials": len(g),
            "n_correct": int(g["is_correct"].sum()),
            "n_timeouts": int(g["timeout"].sum()),
            "accuracy": g["is_correct"].mean(),
            "rt_mean": answered["rt"].mean(),
            "rt_median": answered["rt"].median(),
            "rt_sd": answered["rt"].std(),
        })
 
    table = trials.groupby(by, sort=True).apply(summarise_group, include_groups=False).reset_index()
    counts = ["n_trials", "n_correct", "n_timeouts"]
    table[counts] = table[counts].astype(int)
    return table
 
 
def wilson_interval(n_correct, n_trials):
    """95 % Wilson score interval for a proportion."""
    k, n = np.asarray(n_correct, float), np.asarray(n_trials, float)
    p = k / n
    denom = 1 + Z95**2 / n
    centre = (p + Z95**2 / (2 * n)) / denom
    half = Z95 * np.sqrt(p * (1 - p) / n + Z95**2 / (4 * n**2)) / denom
    return np.clip(centre - half, 0, 1), np.clip(centre + half, 0, 1)
 
 
def t_interval(values) -> tuple[float, float, float, int]:
    """Mean, 95 % t-interval (lo, hi) and n of the non-NaN values; interval is NaN if n < 2."""
    v = np.asarray(values, float)
    v = v[~np.isnan(v)]
    n = len(v)
    if n == 0:
        return np.nan, np.nan, np.nan, 0
    mean = v.mean()
    if n < 2:
        return mean, np.nan, np.nan, n
    half = stats.t.ppf(0.975, n - 1) * v.std(ddof=1) / np.sqrt(n)
    return mean, mean - half, mean + half, n
 
 
def add_subject_intervals(table: pd.DataFrame) -> pd.DataFrame:
    """Add Wilson accuracy (acc_lo/hi) and t-interval mean RT (rt_lo/hi) columns."""
    table = table.copy()
    table["acc_lo"], table["acc_hi"] = wilson_interval(table["n_correct"], table["n_trials"])
    answered = (table["n_trials"] - table["n_timeouts"]).to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        half = stats.t.ppf(0.975, answered - 1) * table["rt_sd"] / np.sqrt(answered)
    table["rt_lo"], table["rt_hi"] = table["rt_mean"] - half, table["rt_mean"] + half
    return table
 
 
def bootstrap_median_rt(trials: pd.DataFrame, n_boot: int = 2000, seed: int = 0) -> pd.DataFrame:
    """Median RT per participant x session with a percentile-bootstrap 95 % interval."""
    rng = np.random.default_rng(seed)
    rows = []
    for (participant, session), g in trials[~trials["timeout"]].groupby(["participant", "session"]):
        rts = g["rt"].dropna().to_numpy()
        lo = hi = np.nan
        if len(rts) >= 2:
            medians = np.median(rng.choice(rts, size=(n_boot, len(rts)), replace=True), axis=1)
            lo, hi = np.percentile(medians, [2.5, 97.5])
        rows.append((participant, session, np.median(rts) if len(rts) else np.nan, lo, hi))
    return pd.DataFrame(rows, columns=["participant", "session", "rt_median", "rt_median_lo", "rt_median_hi"])
 
 
def across_participants(table: pd.DataFrame, value: str, by: list[str]) -> pd.DataFrame:
    """Mean across participants and 95 % t-interval per group; `table` has one row per participant per group."""
    def summarise_group(g: pd.DataFrame) -> pd.Series:
        mean, lo, hi, n = t_interval(g[value])
        return pd.Series({"mean": mean, "lo": lo, "hi": hi, "n": n})
 
    return table.groupby(by).apply(summarise_group, include_groups=False).reset_index()
 
 
def family_list(table: pd.DataFrame) -> list[str]:
    present = set(table["family"])
    return [f for f in FAMILY_ORDER if f in present] + sorted(present - set(FAMILY_ORDER))
 
 
# --------------------------------------------------------------------------- #
# Drawing helpers                                                             #
# --------------------------------------------------------------------------- #
def style_axes(ax) -> None:
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
 
 
def add_chance_line(ax, linewidth: float = 1.0) -> None:
    ax.axhline(CHANCE, color=INK2, linestyle=DASH, linewidth=linewidth, zorder=1)
 
 
def pct_axis(ax, low: float = 0.0, step: float = 0.25, ylim: tuple[float, float] | None = None) -> None:
    """Percent ticks from `low` to 100 %; y-limits default to a little padding around that."""
    ticks = np.arange(low, 1 + 1e-9, step)
    ax.set_yticks(ticks, [f"{t:.0%}" for t in ticks])
    ax.set_ylim(ylim or (max(low - 0.05, 0), 1.05))
 
 
def band_line(ax, x, y, lo, hi, color, *, line_width=2.0, marker_size=5.0, edge_width=1.2,
              ceiling=None) -> None:
    """A line with markers and a filled band joining the lower and upper interval ends."""
    lo = np.maximum(np.asarray(lo, float), 0)
    hi = np.asarray(hi, float)
    if ceiling is not None:
        hi = np.minimum(hi, ceiling)
    ax.fill_between(x, lo, hi, color=color, alpha=0.2, linewidth=0, zorder=2)
    ax.plot(x, y, color=color, linewidth=line_width, marker="o", markersize=marker_size,
            markeredgecolor=SURFACE, markeredgewidth=edge_width, zorder=3)
 
 
def bars_with_ci(ax, x, mean, lo, hi, color, width=0.6, capsize=3.5) -> None:
    mean, lo, hi = (np.asarray(a, float) for a in (mean, lo, hi))
    ax.bar(x, mean, width=width, color=color, zorder=2)
    ax.errorbar(x, mean, yerr=[np.clip(mean - lo, 0, None), np.clip(hi - mean, 0, None)], fmt="none",
                ecolor=INK, elinewidth=1.3, capsize=capsize, capthick=1.3, zorder=4)
 
 
def finish(fig, out: Path, fname: str, *, title: str | None = None, note: str | None = None,
           rect=(0, 0.04, 1, 1)) -> None:
    """Optional figure title, tight layout, left-aligned footnote, save."""
    if title:
        fig.suptitle(title, x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=rect)
    if note:
        fig.text(0.01, 0.005, note, ha="left", va="bottom", color=INK2, fontsize=7.5)
    fig.savefig(out / fname, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out / fname)
 
 
def group_legend_handles(color: str, with_chance: bool) -> list[Line2D]:
    handles = [
        Line2D([], [], color=color, linewidth=2.2, marker="o", markersize=5.5,
               markeredgecolor=SURFACE, label="mean across participants"),
        Line2D([], [], color=color, alpha=0.3, linewidth=8, label="95% CI across participants (t)"),
        Line2D([], [], color=INK2, alpha=0.4, linewidth=1.2, label="individual participant"),
    ]
    if with_chance:
        handles.append(Line2D([], [], linestyle=DASH, color=INK2, label="chance"))
    return handles
 
 
# --------------------------------------------------------------------------- #
# subject_accuracy_rt_overall.png                                             #
# --------------------------------------------------------------------------- #
OVERALL_NOTE = ("Error bars: 95% CI (accuracy: Wilson interval on pooled trials; "
                "RT: t-interval over answered trials)")
 
 
def plot_subject_overall(table: pd.DataFrame, out: Path) -> None:
    table = add_subject_intervals(table)
    participants = table["participant"].tolist()
    x = np.arange(len(participants))
    fig, (ax_acc, ax_rt) = plt.subplots(1, 2, figsize=(max(8, 1.1 * len(participants) + 5), 4.3))
 
    bars_with_ci(ax_acc, x, table["accuracy"], table["acc_lo"], table["acc_hi"], BLUE)
    add_chance_line(ax_acc)
    ax_acc.text(len(participants) - 0.35, CHANCE + 0.01, "chance", ha="left", va="bottom",
                color=INK2, fontsize=8)
    for xi, row in zip(x, table.itertuples()):
        ax_acc.text(xi, row.acc_hi + 0.015, f"{row.accuracy:.0%}", ha="center", fontsize=9)
        if row.n_timeouts:
            ax_acc.text(xi, 0.03, f"{row.n_timeouts} timeout{'s' if row.n_timeouts > 1 else ''}",
                        ha="center", va="bottom", color="white", fontsize=7, rotation=90)
    ax_acc.set_xlim(-0.6, len(participants) + 0.3)
    pct_axis(ax_acc, ylim=(0, 1.1))
    ax_acc.set_title("Accuracy")
 
    bars_with_ci(ax_rt, x, table["rt_mean"], table["rt_lo"], table["rt_hi"], ORANGE)
    for xi, row in zip(x, table.itertuples()):
        ax_rt.text(xi, row.rt_hi + 0.08, f"{row.rt_mean:.1f} s", ha="center", fontsize=9)
    ax_rt.set_ylim(0, table["rt_hi"].max() * 1.15)
    ax_rt.set_ylabel("seconds")
    ax_rt.set_title("Mean reaction time (answered trials)")
 
    for ax in (ax_acc, ax_rt):
        ax.set_xticks(x, participants)
        style_axes(ax)
    finish(fig, out, "subject_accuracy_rt_overall.png", title="Overall performance per participant",
           note=OVERALL_NOTE)
 
 
# --------------------------------------------------------------------------- #
# group_{accuracy,rt}_by_session.png, group_accuracy_by_session_family.png    #
# --------------------------------------------------------------------------- #
GROUP_NOTE = ("Each participant contributes one value per session; the band is the 95% t-interval "
              "across participants (n shown under each session).")
 
 
def plot_group_sessions(table: pd.DataFrame, metric: Metric, out: Path, by_family: bool = False) -> None:
    """Group mean per session with a 95 % t band across participants (+ faint individuals).
 
    One panel, or one panel per rule family when `by_family`.
    """
    panels = family_list(table) if by_family else [None]
    sessions = sorted(table["session"].unique())
    figsize = (3.3 * len(panels) + 0.8, 4.4) if by_family else (8.2, 4.8)
    fig, axes = plt.subplots(1, len(panels), figsize=figsize, sharex=True, sharey=True, squeeze=False)
 
    y_top = 0.0
    for ax, family in zip(axes[0], panels):
        panel = table if family is None else table[table["family"] == family]
        group = across_participants(panel, metric.value, ["session"]).sort_values("session")
        if metric.is_pct:
            add_chance_line(ax)
        for _, one in panel.groupby("participant"):
            one = one.sort_values("session")
            ax.plot(one["session"], one[metric.value], color=INK2, alpha=0.28, linewidth=0.9, zorder=1.5)
        band_line(ax, group["session"], group["mean"], group["lo"], group["hi"], metric.color,
                  line_width=2.2, marker_size=5.5, edge_width=1.4, ceiling=1.0 if metric.is_pct else None)
        style_axes(ax)
        n_per_session = group.set_index("session")["n"]
        ax.set_xticks(sessions, [f"{s}\nn={int(n_per_session.get(s, 0))}" for s in sessions])
        ax.set_xlabel("session")
        if family:
            ax.set_title(family)
        y_top = np.nanmax([y_top, group["hi"].max(), panel[metric.value].max()])
 
    first = axes[0, 0]
    first.set_ylabel(metric.ylabel)
    if metric.is_pct:
        pct_axis(first, low=0.0 if by_family else 0.25)
    else:
        first.set_ylim(0, y_top * 1.08)
 
    handles = group_legend_handles(metric.color, metric.is_pct)
    if by_family:
        fig.legend(handles=handles, loc="upper right", ncol=4, bbox_to_anchor=(0.995, 1.0), **LEGEND_STYLE)
        finish(fig, out, f"group_{metric.value.split('_')[0]}_by_session_family.png",
               title=f"{metric.name} across sessions, by rule family",
               note=GROUP_NOTE + " One block (8 trials) per family per session.", rect=(0, 0.06, 1, 0.93))
    else:
        first.set_title(f"{metric.name} across sessions" + ("" if metric.is_pct else " (participant medians)"), pad=34)
        first.legend(handles=handles, loc="lower left", ncol=4, bbox_to_anchor=(0.0, 1.0), **LEGEND_STYLE)
        finish(fig, out, f"group_{metric.value.split('_')[0]}_by_session.png",
               note=GROUP_NOTE, rect=(0, 0.05, 1, 1))
 
 
# --------------------------------------------------------------------------- #
# subject_{accuracy,rt}_by_session.png, subject_accuracy_by_session_family.png #
# --------------------------------------------------------------------------- #
def plot_subject_sessions(table: pd.DataFrame, metric: Metric, out: Path, fname: str, note: str,
                          by_family: bool = False) -> None:
    """One value per session with its 95 % interval ends joined into a band.
 
    Default: one panel per participant. `by_family`: participants as columns, rule families as rows.
    """
    participants = sorted(table["participant"].unique())
    families = family_list(table) if by_family else [None]
    if by_family:
        nrow, ncol = len(families), len(participants)
        figsize = (2.3 * ncol + 1.0, 1.75 * nrow + 1.3)
    else:
        ncol = min(4, len(participants))
        nrow = int(np.ceil(len(participants) / ncol))
        figsize = (3.2 * ncol, 2.6 * nrow + 0.9)
    fig, axes = plt.subplots(nrow, ncol, figsize=figsize, sharex=True, sharey=True, squeeze=False)
 
    if by_family:
        cells = [(axes[i, j], pid, fam) for i, fam in enumerate(families) for j, pid in enumerate(participants)]
    else:
        cells = [(ax, pid, None) for ax, pid in zip(axes.ravel(), participants)]
        for ax in axes.ravel()[len(participants):]:
            ax.set_visible(False)
 
    style = dict(line_width=1.4, marker_size=4, edge_width=1.0) if by_family else {}
    for ax, pid, family in cells:
        one = table[table["participant"] == pid]
        if family:
            one = one[one["family"] == family]
        one = one.sort_values("session")
        if metric.is_pct:
            add_chance_line(ax, 0.9 if by_family else 1.0)
        band_line(ax, one["session"], one[metric.value], one[metric.lo], one[metric.hi], metric.color,
                  ceiling=1.0 if metric.is_pct else None, **style)
        style_axes(ax)
        if family is None or family == families[0]:
            ax.set_title(pid)
        if family and pid == participants[0]:
            ax.set_ylabel(family, rotation=0, ha="right", va="center", labelpad=8, color=INK, fontsize=10)
 
    first = axes[0, 0]
    if metric.is_pct:
        if by_family:
            pct_axis(first, step=0.5, ylim=(-0.03, 1.05))
        else:
            pct_axis(first, low=0.25)
    else:
        first.set_ylim(0, np.nanmax(table[metric.hi]) * 1.08)
    first.set_xticks(range(1, int(table["session"].max()) + 1))
    for ax in axes[-1]:
        ax.set_xlabel("session")
    if not by_family:
        for ax in axes[:, 0]:
            ax.set_ylabel(metric.ylabel)
    suffix = ", per participant and rule family" if by_family else ", per participant"
    finish(fig, out, fname, title=f"{metric.name} across sessions{suffix}", note=note,
           rect=(0, 0.035 if by_family else 0.04, 1, 1))
 
 
WILSON_NOTE = "Band: 95% Wilson interval on that session's trials (treats trials as independent). Dashed: chance."
WILSON_FAMILY_NOTE = ("Band: 95% Wilson interval on that session's trials in the family, joined across sessions "
                      "(treats trials as independent; few trials per block, so wide). Dashed: chance.")
BOOTSTRAP_NOTE = "Band: 95% bootstrap interval of the median over that session's answered trials."
 
 
# --------------------------------------------------------------------------- #
# group_accuracy_by_family.png (beeswarm of participants)                     #
# --------------------------------------------------------------------------- #
def beeswarm_offsets(ys, min_dy=0.045, step=0.16, max_dx=0.48) -> np.ndarray:
    """Horizontal offsets so points with similar y don't overlap (centre first, then alternate)."""
    order = np.argsort(-np.asarray(ys))
    placed: list[tuple[float, float]] = []  # (dx, y)
    offsets = np.zeros(len(ys))
    candidates = [0.0] + [sign * step * k for k in range(1, 4) for sign in (1, -1)]
    for i in order:
        for dx in candidates:
            if all(abs(ys[i] - y) >= min_dy or abs(dx - d) >= step * 0.95 for d, y in placed):
                break
        else:  # crowded: squeeze in at the edge
            dx = max_dx
        placed.append((dx, ys[i]))
        offsets[i] = dx
    return offsets
 
 
def plot_group_accuracy_by_family(table: pd.DataFrame, out: Path) -> None:
    """One dot per participant per family (that participant's pooled accuracy), with the family mean."""
    families = family_list(table)
    fig, ax = plt.subplots(figsize=(2.6 * len(families) + 2.2, 5.0))
    add_chance_line(ax)
    for x0, family in enumerate(families):
        one = table[table["family"] == family].sort_values("participant")
        acc = one["accuracy"].to_numpy()
        xs = x0 + beeswarm_offsets(acc)
        ax.hlines(acc.mean(), x0 - 0.45, x0 + 0.45, color=INK, linewidth=2, zorder=2)
        ax.scatter(xs, acc, s=46, color=BLUE, edgecolor=SURFACE, linewidth=1.2, zorder=3)
        for xi, yi, pid in zip(xs, acc, one["participant"]):
            ax.text(xi + 0.05, yi, pid, va="center", ha="left", fontsize=7.5, color=INK2, zorder=4,
                    path_effects=[pe.withStroke(linewidth=3, foreground=SURFACE)])
 
    ax.set_xticks(range(len(families)), families)
    ax.set_xlim(-0.55, len(families) - 0.3)
    pct_axis(ax, ylim=(0, 1.05))
    ax.set_ylabel("accuracy (all trials of that family)")
    style_axes(ax)
    ax.legend(handles=[
        Line2D([], [], marker="o", linestyle="", color=BLUE, markeredgecolor=SURFACE, markersize=7,
               label="one participant"),
        Line2D([], [], color=INK, linewidth=2, label="mean across participants"),
        Line2D([], [], linestyle=DASH, color=INK2, label="chance"),
    ], loc="lower left", ncol=3, bbox_to_anchor=(0.0, -0.2), **{**LEGEND_STYLE, "fontsize": 9})
    ax.set_title("Accuracy by rule family", pad=10)
    finish(fig, out, "group_accuracy_by_family.png", rect=(0, 0, 1, 1))
 
 
# --------------------------------------------------------------------------- #
# subject_rt_by_family.png (heatmap)                                          #
# --------------------------------------------------------------------------- #
def text_color_on(value: float, vmin: float, vmax: float) -> str:
    """White ink on dark cells, dark ink on light cells."""
    return "white" if (value - vmin) / (vmax - vmin) > 0.55 else INK
 
 
def draw_heatmap(ax, matrix: pd.DataFrame, vmin: float, vmax: float, fmt, fontsize: int = 10):
    data = np.ma.masked_invalid(matrix.values.astype(float))
    cmap = CMAP.copy()
    cmap.set_bad(SURFACE)
    image = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    n_rows, n_cols = matrix.shape
    ax.set_xticks(range(n_cols), matrix.columns)
    ax.set_yticks(range(n_rows), matrix.index)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks(np.arange(-0.5, n_cols), minor=True)  # 2px gaps between cells
    ax.set_yticks(np.arange(-0.5, n_rows), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)
    for i in range(n_rows):
        for j in range(n_cols):
            v = matrix.values[i, j]
            if np.isnan(v):
                ax.text(j, i, "–", ha="center", va="center", color=INK2, fontsize=fontsize)
            else:
                ax.text(j, i, fmt(v), ha="center", va="center",
                        color=text_color_on(v, vmin, vmax), fontsize=fontsize)
    return image
 
 
def plot_subject_rt_by_family(table: pd.DataFrame, out: Path) -> None:
    families = family_list(table)
    matrix = table.pivot(index="participant", columns="family", values="rt_median")[families]
    fig, ax = plt.subplots(figsize=(1.5 * len(families) + 1.5, 0.6 * len(matrix) + 1.6))
    image = draw_heatmap(ax, matrix, 1.0, 7.0, lambda v: f"{v:.1f}s")
    colorbar = fig.colorbar(image, ax=ax, fraction=0.04, pad=0.02)
    colorbar.set_label("seconds", color=INK2)
    colorbar.outline.set_visible(False)
    colorbar.ax.tick_params(length=0, colors=INK2)
    ax.set_title("Median RT by rule family (s)", pad=10)
    finish(fig, out, "subject_rt_by_family.png", rect=(0, 0, 1, 1))
 
 
# --------------------------------------------------------------------------- #
# group_accuracy_by_rule.png                                                  #
# --------------------------------------------------------------------------- #
def plot_group_accuracy_by_rule(table: pd.DataFrame, out: Path) -> None:
    """Mean accuracy per rule across participants (bars grouped by family) with a 95 % t-interval.
 
    Each participant contributes one accuracy per rule. Rules seen by fewer than two
    participants have no interval and are left out.
    """
    rows, left_out, family_spans = [], [], []  # family_spans: (family, first_x, last_x)
    x = 0.0
    for family in family_list(table):
        first_x = x
        for rule in sorted(table.loc[table["family"] == family, "rule"].unique()):
            accuracies = table[(table["family"] == family) & (table["rule"] == rule)]["accuracy"].dropna().to_numpy()
            mean, lo, hi, n = t_interval(accuracies)
            if n < 2:
                left_out.append(f"{family}/{rule}")
                continue
            rows.append(dict(x=x, rule=rule, n=n, mean=mean, lo=max(lo, 0), hi=min(hi, 1), values=accuracies))
            x += 1
        if x > first_x:
            family_spans.append((family, first_x, x - 1))
            x += 0.9  # gap between families
    if left_out:
        print(f"group_accuracy_by_rule: left out (seen by < 2 participants): {', '.join(left_out)}")
    rules = pd.DataFrame(rows)
 
    fig, ax = plt.subplots(figsize=(0.58 * len(rules) + 2.5, 6.3))
    add_chance_line(ax)
    bars_with_ci(ax, rules["x"], rules["mean"], rules["lo"], rules["hi"], BLUE, width=0.68, capsize=3)
    for r in rules.itertuples():  # individual participants, spread sideways so ties stay visible
        jitter = np.linspace(-0.2, 0.2, len(r.values)) if len(r.values) > 1 else np.zeros(1)
        ax.scatter(r.x + jitter, r.values, s=13, color=SURFACE, edgecolor=INK2, linewidth=0.8, zorder=5)
        if r.n < rules["n"].max():  # flag rules that not every participant saw
            ax.text(r.x, r.hi + 0.025, f"n={r.n}", ha="center", fontsize=7, color=INK2)
 
    ax.set_xticks(rules["x"], rules["rule"])
    ax.tick_params(axis="x", labelrotation=40)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    ax.set_xlim(-0.8, rules["x"].max() + 0.8)
    pct_axis(ax, ylim=(0, 1.1))
    ax.set_ylabel("accuracy")
    style_axes(ax)
 
    # family labels under the rule labels
    transform = blended_transform_factory(ax.transData, ax.transAxes)
    line_y = -(0.07 + 0.0135 * rules["rule"].str.len().max())  # below the longest rotated label
    for family, first_x, last_x in family_spans:
        ax.plot([first_x - 0.4, last_x + 0.4], [line_y, line_y], transform=transform, color=INK2,
                linewidth=1.2, clip_on=False)
        ax.text((first_x + last_x) / 2, line_y - 0.025, family, transform=transform, ha="center",
                va="top", fontsize=10.5, fontweight="bold", color=INK)
 
    ax.legend(handles=[
        Line2D([], [], marker="s", linestyle="", color=BLUE, markersize=8, label="mean across participants"),
        Line2D([], [], marker="o", linestyle="", markerfacecolor=SURFACE, markeredgecolor=INK2,
               markersize=5, label="individual participant"),
        Line2D([], [], color=INK, linewidth=1.3, marker="_", markersize=8, label="95% CI across participants (t)"),
        Line2D([], [], linestyle=DASH, color=INK2, label="chance"),
    ], loc="upper left", ncol=4, bbox_to_anchor=(0.0, 1.1), **{**LEGEND_STYLE, "fontsize": 9})
    ax.set_title("Accuracy by rule", pad=34)
    finish(fig, out, "group_accuracy_by_rule.png", rect=(0, 0, 1, 1))
 
 
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=HERE / "data" / "behavior_trials.csv",
                        help="trial-level CSV from build_trials.py (default: ./data/behavior_trials.csv)")
    parser.add_argument("--out", type=Path, default=HERE / "results" / "plots",
                        help="output folder for the PNGs (default: ./results/plots)")
    args = parser.parse_args()
    if not args.data.is_file():
        raise SystemExit(f"{args.data} not found - run build_trials.py first")
    args.out.mkdir(parents=True, exist_ok=True)
 
    trials = pd.read_csv(args.data)
    tables = {name: summarise(trials, by) for name, by in GROUPINGS.items()}
    session_with_ci = add_subject_intervals(tables["session"])
    session_family_with_ci = add_subject_intervals(tables["session_family"])
    session_rt_with_ci = bootstrap_median_rt(trials)
 
    # subject level
    plot_subject_overall(tables["overall"], args.out)
    plot_subject_sessions(session_with_ci, ACCURACY, args.out, "subject_accuracy_by_session.png", WILSON_NOTE)
    plot_subject_sessions(session_rt_with_ci, RT, args.out, "subject_rt_by_session.png", BOOTSTRAP_NOTE)
    plot_subject_sessions(session_family_with_ci, ACCURACY, args.out,
                          "subject_accuracy_by_session_family.png", WILSON_FAMILY_NOTE, by_family=True)
    plot_subject_rt_by_family(tables["family"], args.out)
 
    # group level (participant = unit, band = 95 % t-interval across participants)
    plot_group_sessions(tables["session"], ACCURACY, args.out)
    plot_group_sessions(tables["session"], RT, args.out)
    plot_group_sessions(tables["session_family"], ACCURACY, args.out, by_family=True)
    plot_group_accuracy_by_family(tables["family"], args.out)
    plot_group_accuracy_by_rule(tables["rule"], args.out)
 
 
if __name__ == "__main__":
    main()
 