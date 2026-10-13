#!/usr/bin/env python
"""Draw every behavioural plot from the tables in results/. Nothing is computed here.

Reads   results/descriptive/tables/*.csv      (made by descriptive.py)
        results/ddm/tables/<model>_stats.csv (made by fit_ddm.py)
Writes  results/descriptive/plots/*.png
        results/ddm/plots/*.png

Descriptive file names:  <scope>_<metric>_by_<x>[_family].png
  scope   group    one value per participant, summarised ACROSS participants
          subject  one panel / bar / row per participant
  metric  accuracy | rt (reaction time)
  x       overall | session | session_family | family | rule
DDM file names:  <model>_parameters_by_participant | <model>_drift_by_family | <model>_effects

Usage:  python plot.py [all | descriptive | ddm] [--results DIR]
"""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.transforms import blended_transform_factory

from common import CHANCE, RESULTS_DIR, family_list

# --- palette (light mode) ----------------------------------------------------
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
BLUE = "#2a78d6"    # accuracy, drift rate
ORANGE = "#eb6834"  # reaction time, non-decision time
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
    """What a session plot shows: table columns, colour and axis style."""
    slug: str    # used in file names
    name: str    # used in titles
    value: str   # column with the point estimate (also the `metric` label in group tables)
    lo: str      # columns with the subject-level interval
    hi: str
    color: str
    ylabel: str
    is_pct: bool


ACCURACY = Metric("accuracy", "Accuracy", "accuracy", "acc_lo", "acc_hi", BLUE, "accuracy", True)
RT = Metric("rt", "Median reaction time", "rt_median", "rt_median_lo", "rt_median_hi", ORANGE, "seconds", False)


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
    """A line with markers; with `lo`/`hi`, also a filled band joining the interval ends."""
    if lo is not None:
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


def finish(fig, out_dir: Path, fname: str, *, title: str | None = None, note: str | None = None,
           rect=(0, 0.04, 1, 1)) -> None:
    """Optional figure title, tight layout, left-aligned footnote, save."""
    if title:
        fig.suptitle(title, x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=rect)
    if note:
        fig.text(0.01, 0.005, note, ha="left", va="bottom", color=INK2, fontsize=7.5)
    fig.savefig(out_dir / fname, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out_dir / fname)


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


def plot_subject_overall(table: pd.DataFrame, out_dir: Path) -> None:
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
    finish(fig, out_dir, "subject_accuracy_rt_overall.png", title="Overall performance per participant",
           note=OVERALL_NOTE)


# --------------------------------------------------------------------------- #
# group_{accuracy,rt}_by_session.png, group_{accuracy,rt}_by_session_family.png #
# --------------------------------------------------------------------------- #
GROUP_NOTE = ("Each participant contributes one value per session; the band is the 95% t-interval "
              "across participants (n shown under each session).")


def plot_group_sessions(subject: pd.DataFrame, group: pd.DataFrame, metric: Metric, out_dir: Path,
                        by_family: bool = False) -> None:
    """Group mean per session with the 95 % band across participants (+ faint individuals).

    `subject` and `group` are the matching _subject / _group tables. One panel, or one panel
    per rule family when `by_family`.
    """
    group = group[group["metric"] == metric.value]
    panels = family_list(subject) if by_family else [None]
    sessions = sorted(subject["session"].unique())
    figsize = (3.3 * len(panels) + 0.8, 4.4) if by_family else (8.2, 4.8)
    fig, axes = plt.subplots(1, len(panels), figsize=figsize, sharex=True, sharey=True, squeeze=False)

    y_top = 0.0
    for ax, family in zip(axes[0], panels):
        people = subject if family is None else subject[subject["family"] == family]
        panel = (group if family is None else group[group["family"] == family]).sort_values("session")
        if metric.is_pct:
            add_chance_line(ax)
        for _, one in people.groupby("participant"):
            one = one.sort_values("session")
            ax.plot(one["session"], one[metric.value], color=INK2, alpha=0.28, linewidth=0.9, zorder=1.5)
        band_line(ax, panel["session"], panel["mean"], panel["lo"], panel["hi"], metric.color,
                  line_width=2.2, marker_size=5.5, edge_width=1.4, ceiling=1.0 if metric.is_pct else None)
        style_axes(ax)
        n_per_session = panel.set_index("session")["n"]
        ax.set_xticks(sessions, [f"{s}\nn={int(n_per_session.get(s, 0))}" for s in sessions])
        ax.set_xlabel("session")
        if family:
            ax.set_title(family)
        y_top = np.nanmax([y_top, panel["hi"].max(), people[metric.value].max()])

    first = axes[0, 0]
    first.set_ylabel(metric.ylabel)
    if metric.is_pct:
        pct_axis(first, low=0.0 if by_family else 0.25)
    else:
        first.set_ylim(0, y_top * 1.08)

    handles = group_legend_handles(metric.color, metric.is_pct)
    if by_family:
        fig.legend(handles=handles, loc="upper right", ncol=4, bbox_to_anchor=(0.995, 1.0), **LEGEND_STYLE)
        finish(fig, out_dir, f"group_{metric.slug}_by_session_family.png",
               title=f"{metric.name} across sessions, by rule family",
               note=GROUP_NOTE + " One block (8 trials) per family per session.", rect=(0, 0.06, 1, 0.93))
    else:
        suffix = "" if metric.is_pct else " (participant medians)"
        first.set_title(f"{metric.name} across sessions{suffix}", pad=34)
        first.legend(handles=handles, loc="lower left", ncol=4, bbox_to_anchor=(0.0, 1.0), **LEGEND_STYLE)
        finish(fig, out_dir, f"group_{metric.slug}_by_session.png", note=GROUP_NOTE, rect=(0, 0.05, 1, 1))


# --------------------------------------------------------------------------- #
# subject_{accuracy,rt}_by_session.png, subject_{accuracy,rt}_by_session_family.png #
# --------------------------------------------------------------------------- #
WILSON_NOTE = "Band: 95% Wilson interval on that session's trials (treats trials as independent). Dashed: chance."
BOOTSTRAP_NOTE = "Band: 95% bootstrap interval of the median over that session's answered trials."
FAMILY_BLOCK_NOTE = {
    "accuracy": "Each point is one block of 8 trials of that family in that session (fraction correct). Dashed: chance.",
    "rt": "Each point is one block of 8 trials of that family in that session (median RT of answered trials).",
}


def plot_subject_sessions(table: pd.DataFrame, metric: Metric, out_dir: Path, fname: str, note: str,
                          by_family: bool = False) -> None:
    """One value per session. Default: one panel per participant with its 95 % interval joined
    into a band. `by_family`: participants as columns, rule families as rows, plain points
    (one block of 8 trials each, so an interval would add nothing).
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
        band = (None, None) if by_family else (one[metric.lo], one[metric.hi])
        band_line(ax, one["session"], one[metric.value], *band, metric.color,
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
        first.set_ylim(0, np.nanmax(table[metric.value if by_family else metric.hi]) * 1.08)
    first.set_xticks(range(1, int(table["session"].max()) + 1))
    for ax in axes[-1]:
        ax.set_xlabel("session")
    if not by_family:
        for ax in axes[:, 0]:
            ax.set_ylabel(metric.ylabel)
    suffix = ", per participant and rule family" if by_family else ", per participant"
    finish(fig, out_dir, fname, title=f"{metric.name} across sessions{suffix}", note=note,
           rect=(0, 0.035 if by_family else 0.04, 1, 1))


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


def plot_group_accuracy_by_family(subject: pd.DataFrame, group: pd.DataFrame, out_dir: Path) -> None:
    """One dot per participant per family (that participant's pooled accuracy), with the family mean."""
    families = family_list(subject)
    means = group[group["metric"] == "accuracy"].set_index("family")["mean"]
    fig, ax = plt.subplots(figsize=(2.6 * len(families) + 2.2, 5.0))
    add_chance_line(ax)
    for x0, family in enumerate(families):
        one = subject[subject["family"] == family].sort_values("participant")
        acc = one["accuracy"].to_numpy()
        xs = x0 + beeswarm_offsets(acc)
        ax.hlines(means[family], x0 - 0.45, x0 + 0.45, color=INK, linewidth=2, zorder=2)
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
    finish(fig, out_dir, "group_accuracy_by_family.png", rect=(0, 0, 1, 1))


# --------------------------------------------------------------------------- #
# group_accuracy_by_rule.png                                                  #
# --------------------------------------------------------------------------- #
def plot_group_accuracy_by_rule(subject: pd.DataFrame, group: pd.DataFrame, out_dir: Path) -> None:
    """Mean accuracy per rule across participants (bars grouped by family) with the 95 % t-interval.

    Rules seen by fewer than two participants have no interval and are left out.
    """
    group = group[group["metric"] == "accuracy"]
    rows, left_out, family_spans = [], [], []  # family_spans: (family, first_x, last_x)
    x = 0.0
    for family in family_list(group):
        first_x = x
        for r in group[group["family"] == family].sort_values("rule").itertuples():
            if r.n < 2:
                left_out.append(f"{family}/{r.rule}")
                continue
            values = subject[(subject["family"] == family) & (subject["rule"] == r.rule)]["accuracy"].dropna().to_numpy()
            rows.append(dict(x=x, rule=r.rule, n=r.n, mean=r.mean, lo=max(r.lo, 0), hi=min(r.hi, 1), values=values))
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
    finish(fig, out_dir, "group_accuracy_by_rule.png", rect=(0, 0, 1, 1))


def plot_descriptive(results_dir: Path) -> None:
    tables_dir = results_dir / "descriptive" / "tables"
    plots_dir = results_dir / "descriptive" / "plots"
    names = ["overall_subject", "session_subject", "session_group", "session_family_subject",
             "session_family_group", "family_subject", "family_group", "rule_subject", "rule_group"]
    missing = [n for n in names if not (tables_dir / f"{n}.csv").is_file()]
    if missing:
        raise SystemExit(f"missing tables in {tables_dir}: {', '.join(missing)} - run descriptive.py first")
    t = {n: pd.read_csv(tables_dir / f"{n}.csv") for n in names}
    plots_dir.mkdir(parents=True, exist_ok=True)

    plot_subject_overall(t["overall_subject"], plots_dir)
    plot_subject_sessions(t["session_subject"], ACCURACY, plots_dir, "subject_accuracy_by_session.png", WILSON_NOTE)
    plot_subject_sessions(t["session_subject"], RT, plots_dir, "subject_rt_by_session.png", BOOTSTRAP_NOTE)
    for metric in (ACCURACY, RT):
        plot_subject_sessions(t["session_family_subject"], metric, plots_dir,
                              f"subject_{metric.slug}_by_session_family.png",
                              FAMILY_BLOCK_NOTE[metric.slug], by_family=True)
        plot_group_sessions(t["session_subject"], t["session_group"], metric, plots_dir)
        plot_group_sessions(t["session_family_subject"], t["session_family_group"], metric, plots_dir,
                            by_family=True)
    plot_group_accuracy_by_family(t["family_subject"], t["family_group"], plots_dir)
    plot_group_accuracy_by_rule(t["rule_subject"], t["rule_group"], plots_dir)


# --------------------------------------------------------------------------- #
# DDM: <model>_parameters_by_participant, <model>_drift_by_family, <model>_effects #
# All intervals are 95 % posterior credible intervals (2.5 % - 97.5 % quantiles). #
# v drift rate (evidence quality), a boundary separation (caution), t non-decision time (s). #
# --------------------------------------------------------------------------- #
DDM_PARAMETERS = {  # name -> (title, colour)
    "v": ("Drift rate v (evidence quality)", BLUE),
    "a": ("Boundary separation a (caution)", INK2),
    "t": ("Non-decision time t (s)", ORANGE),
}
DDM_NOTE = "Points: posterior means. Lines and bands: 95% credible intervals."


def posterior(stats: pd.DataFrame, name: str) -> tuple[float, float, float]:
    row = stats.loc[name]
    return row["mean"], row["2.5q"], row["97.5q"]


def subject_names(stats: pd.DataFrame, parameter: str, condition: str | None = None) -> dict[str, str]:
    """{participant: row name} of the per-participant posteriors of a parameter (optionally per condition)."""
    cond = rf"\({re.escape(condition)}\)" if condition else ""
    pattern = re.compile(rf"^{parameter}_subj{cond}\.(p\d+)$")
    return {m.group(1): name for name in stats.index if (m := pattern.match(name))}


def interval_dots(ax, x, mean, lo, hi, color, size=34) -> None:
    ax.vlines(x, lo, hi, color=color, linewidth=1.4, alpha=0.6, zorder=2)
    ax.scatter(x, mean, s=size, color=color, edgecolor=SURFACE, linewidth=1.0, zorder=3)


def plot_ddm_parameters_by_participant(stats: pd.DataFrame, model: str, out_dir: Path) -> None:
    """One panel per parameter: each participant's posterior with the group mean as a band."""
    participants = sorted(subject_names(stats, "a"))
    fig, axes = plt.subplots(1, 3, figsize=(3.0 * 3 + 1.5, 4.0))
    for ax, (parameter, (title, color)) in zip(axes, DDM_PARAMETERS.items()):
        names = subject_names(stats, parameter)
        if parameter in stats.index:
            mean, lo, hi = posterior(stats, parameter)
            ax.axhspan(lo, hi, color=color, alpha=0.15, linewidth=0, zorder=1)
            ax.axhline(mean, color=color, linewidth=1.2, alpha=0.8, zorder=2)
        for x, pid in enumerate(participants):
            if pid in names:
                interval_dots(ax, x, *posterior(stats, names[pid]), color)
        ax.set_xticks(range(len(participants)), participants, rotation=45)
        ax.set_title(title)
        style_axes(ax)
    finish(fig, out_dir, f"{model}_parameters_by_participant.png",
           title="Drift diffusion parameters per participant", note=DDM_NOTE)


def plot_ddm_drift_by_family(stats: pd.DataFrame, model: str, out_dir: Path) -> None:
    """Drift rate per rule family: group posterior (black) and each participant (lines join participants)."""
    families = [m.group(1) for name in stats.index if (m := re.match(r"^v\((.+)\)$", name))]
    participants = sorted({p for f in families for p in subject_names(stats, "v", f)})
    fig, ax = plt.subplots(figsize=(1.8 * len(families) + 2.0, 4.6))
    for pid in participants:
        means = [posterior(stats, subject_names(stats, "v", f)[pid])[0] for f in families]
        ax.plot(range(len(families)), means, color=INK2, alpha=0.3, linewidth=0.9, zorder=1)
        ax.scatter(range(len(families)), means, s=22, color=BLUE, alpha=0.8, edgecolor=SURFACE,
                   linewidth=0.8, zorder=2)
    for x, family in enumerate(families):
        mean, lo, hi = posterior(stats, f"v({family})")
        ax.vlines(x, lo, hi, color=INK, linewidth=3, zorder=4)
        ax.scatter(x, mean, s=60, color=INK, edgecolor=SURFACE, linewidth=1.2, zorder=5)
    ax.set_xticks(range(len(families)), families)
    ax.set_xlim(-0.5, len(families) - 0.5)
    ax.set_ylabel("drift rate v")
    style_axes(ax)
    finish(fig, out_dir, f"{model}_drift_by_family.png", title="Drift rate by rule family",
           note=DDM_NOTE + " Black: group posterior; blue: participants.")


def effect_label(name: str) -> str:
    parameter, rest = name.split("_", 1)
    if rest == "session_z":
        return f"{parameter}: per SD of session number"
    match = re.match(r"C\(family\)\[T\.(.+)\]", rest)
    return f"{parameter}: {match.group(1)} vs first family" if match else f"{parameter}: {rest}"


def plot_ddm_effects(stats: pd.DataFrame, model: str, out_dir: Path) -> None:
    """Forest plot of the group-level regression coefficients (intercepts left out)."""
    names = [n for n in stats.index if re.match(r"^[vat]_(session_z|C\(family\)\[T\..+\])$", n)]
    fig, ax = plt.subplots(figsize=(8.5, 0.5 * len(names) + 1.8))
    ys = np.arange(len(names))[::-1]
    for y, name in zip(ys, names):
        mean, lo, hi = posterior(stats, name)
        color = DDM_PARAMETERS[name[0]][1]
        excludes_zero = lo > 0 or hi < 0
        ax.hlines(y, lo, hi, color=color, linewidth=2, zorder=2)
        ax.scatter(mean, y, s=60, facecolor=color if excludes_zero else SURFACE, edgecolor=color,
                   linewidth=1.6, zorder=3)
    ax.axvline(0, color=INK2, linestyle=DASH, linewidth=1, zorder=1)
    ax.set_yticks(ys, [effect_label(n) for n in names])
    ax.set_xlabel("effect on the parameter (a filled dot means the interval excludes 0)")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    finish(fig, out_dir, f"{model}_effects.png", title="Group-level effects", note=DDM_NOTE)


def plot_ddm(results_dir: Path) -> None:
    tables_dir = results_dir / "ddm" / "tables"
    plots_dir = results_dir / "ddm" / "plots"
    stats_files = sorted(tables_dir.glob("*_stats.csv"))
    if not stats_files:
        raise SystemExit(f"no *_stats.csv in {tables_dir} - run fit_ddm.py first")
    plots_dir.mkdir(parents=True, exist_ok=True)
    summary_path = tables_dir / "model_summary.csv"
    summary = pd.read_csv(summary_path).set_index("model") if summary_path.is_file() else None

    for path in stats_files:
        model = path.name[: -len("_stats.csv")]
        stats = pd.read_csv(path, index_col=0)
        print(f"\n=== {model} ===")
        if summary is not None and model in summary.index and summary.loc[model, "n_not_converged"] > 0:
            print(f"WARNING: {int(summary.loc[model, 'n_not_converged'])} parameters have R-hat > 1.1 "
                  "- the chains have not converged, do not interpret these plots yet")
        if subject_names(stats, "a") and subject_names(stats, "t") and subject_names(stats, "v"):
            plot_ddm_parameters_by_participant(stats, model, plots_dir)
        if any(re.match(r"^v\(.+\)$", n) for n in stats.index):
            plot_ddm_drift_by_family(stats, model, plots_dir)
        if any(re.match(r"^[vat]_session_z$", n) for n in stats.index):
            plot_ddm_effects(stats, model, plots_dir)


# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("analysis", nargs="?", default="all", choices=["all", "descriptive", "ddm"])
    parser.add_argument("--results", type=Path, default=RESULTS_DIR, help="results folder")
    args = parser.parse_args()
    if args.analysis in ("all", "descriptive"):
        plot_descriptive(args.results)
    if args.analysis in ("all", "ddm"):
        try:
            plot_ddm(args.results)
        except SystemExit as e:
            if args.analysis == "ddm":
                raise
            print(f"\nskipping DDM plots: {e}")


if __name__ == "__main__":
    main()
