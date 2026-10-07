#!/usr/bin/env python


import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

HERE = Path(__file__).resolve().parent
CHANCE = 0.5  # same / different -> 50 % guessing

# --- palette (validated reference palette, light mode) ---------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e6e5e1"
BLUE = "#2a78d6"    # categorical slot 1 -> accuracy
ORANGE = "#eb6834"  # categorical slot 2 -> reaction time
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CMAP = LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "text.color": INK,
        "axes.labelcolor": INK2,
        "axes.edgecolor": GRID,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
    }
)


def save(fig, out: Path, name: str) -> None:
    fig.savefig(out / name, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out / name)


def text_on(value: float, vmin: float, vmax: float) -> str:
    """White ink on dark cells, dark ink on light cells."""
    return "white" if (value - vmin) / (vmax - vmin) > 0.55 else INK


def style_axes(ax, grid_axis="y"):
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)


# --------------------------------------------------------------------------- #
# 1. Overall: accuracy and RT per participant                                 #
# --------------------------------------------------------------------------- #
def plot_overall(df: pd.DataFrame, out: Path) -> None:
    p = df["participant"].tolist()
    x = np.arange(len(p))
    fig, (a, b) = plt.subplots(1, 2, figsize=(max(8, 1.1 * len(p) + 5), 4))

    a.bar(x, df["accuracy"], width=0.6, color=BLUE)
    a.axhline(CHANCE, color=INK2, linestyle=(0, (4, 3)), linewidth=1)
    a.set_xlim(-0.6, len(p) - 0.4 + 0.7)
    a.text(len(p) - 0.35, CHANCE + 0.01, "chance", ha="left", va="bottom", color=INK2, fontsize=8)
    for xi, v, to in zip(x, df["accuracy"], df["n_timeouts"]):
        a.text(xi, v + 0.015, f"{v:.0%}", ha="center", color=INK, fontsize=9)
        if to:
            a.text(xi, 0.03, f"{to} timeout{'s' if to > 1 else ''}", ha="center",
                   color="white", fontsize=7, rotation=90, va="bottom")
    a.set_ylim(0, 1.08)
    a.set_yticks(np.arange(0, 1.01, 0.25))
    a.set_yticklabels([f"{t:.0%}" for t in a.get_yticks()])
    a.set_xticks(x, p)
    a.set_title("Accuracy")
    style_axes(a)

    b.bar(x, df["rt_median"], width=0.6, color=ORANGE)
    for xi, v in zip(x, df["rt_median"]):
        b.text(xi, v + 0.08, f"{v:.1f} s", ha="center", color=INK, fontsize=9)
    b.set_ylim(0, df["rt_median"].max() * 1.18)
    b.set_xticks(x, p)
    b.set_ylabel("seconds")
    b.set_title("Median reaction time (answered trials)")
    style_axes(b)

    fig.suptitle("Overall performance per participant", x=0.01, ha="left",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    save(fig, out, "overall.png")


# --------------------------------------------------------------------------- #
# 2. Sessions: small multiples (one panel per participant)                    #
# --------------------------------------------------------------------------- #
def plot_sessions(df: pd.DataFrame, out: Path, value: str, color: str, title: str,
                  ylabel: str, fname: str, pct: bool) -> None:
    ps = sorted(df["participant"].unique())
    ncol = min(4, len(ps))
    nrow = int(np.ceil(len(ps) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.2 * ncol, 2.6 * nrow + 0.6),
                             sharex=True, sharey=True, squeeze=False)
    ymax = df[value].max()
    for ax, pid in zip(axes.ravel(), ps):
        d = df[df["participant"] == pid].sort_values("session")
        ax.plot(d["session"], d[value], color=color, linewidth=2, marker="o",
                markersize=5, markeredgecolor=SURFACE, markeredgewidth=1.5)
        if pct:
            ax.axhline(CHANCE, color=INK2, linestyle=(0, (4, 3)), linewidth=1)
        ax.set_title(pid)
        style_axes(ax)
    for ax in axes.ravel()[len(ps):]:
        ax.set_visible(False)
    if pct:
        axes[0, 0].set_ylim(0.25, 1.05)
        axes[0, 0].set_yticks([0.25, 0.5, 0.75, 1.0])
        axes[0, 0].set_yticklabels(["25%", "50%", "75%", "100%"])
    else:
        axes[0, 0].set_ylim(0, ymax * 1.1)
    smax = int(df["session"].max())
    axes[0, 0].set_xticks(range(1, smax + 1))
    for ax in axes[-1]:
        ax.set_xlabel("session")
    for ax in axes[:, 0]:
        ax.set_ylabel(ylabel)
    fig.suptitle(title, x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout()
    save(fig, out, fname)


# --------------------------------------------------------------------------- #
# 3. Heatmaps                                                                 #
# --------------------------------------------------------------------------- #
def heatmap(ax, mat: pd.DataFrame, vmin, vmax, fmt, notes: pd.DataFrame | None = None,
            fontsize=9):
    data = np.ma.masked_invalid(mat.values.astype(float))
    cmap = CMAP.copy()
    cmap.set_bad(SURFACE)
    im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(mat.shape[1]), mat.columns)
    ax.set_yticks(range(mat.shape[0]), mat.index)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    # 2px surface gaps between cells
    ax.set_xticks(np.arange(-0.5, mat.shape[1]), minor=True)
    ax.set_yticks(np.arange(-0.5, mat.shape[0]), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat.values[i, j]
            if np.isnan(v):
                ax.text(j, i, "–", ha="center", va="center", color=INK2, fontsize=fontsize)
                continue
            label = fmt(v)
            if notes is not None and not np.isnan(notes.values[i, j]):
                label += f"\nn={int(notes.values[i, j])}"
            ax.text(j, i, label, ha="center", va="center",
                    color=text_on(v, vmin, vmax), fontsize=fontsize)
    return im


def plot_family(df: pd.DataFrame, out: Path) -> None:
    order = ["arithmetic", "attraction", "expansion", "occlusion", "recolor"]
    fams = [f for f in order if f in set(df["family"])] + sorted(set(df["family"]) - set(order))
    for value, vmin, vmax, fmt, title, cbl, fname in [
        ("accuracy", 0.3, 1.0, lambda v: f"{v:.0%}", "Accuracy by rule family",
         "accuracy", "family_accuracy.png"),
        ("rt_median", 1.0, 7.0, lambda v: f"{v:.1f}s", "Median RT by rule family (s)",
         "seconds", "family_rt.png"),
    ]:
        mat = df.pivot(index="participant", columns="family", values=value)[fams]
        fig, ax = plt.subplots(figsize=(1.5 * len(fams) + 1.5, 0.6 * len(mat) + 1.6))
        im = heatmap(ax, mat, vmin, vmax, fmt, fontsize=10)
        cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
        cb.set_label(cbl, color=INK2)
        cb.outline.set_visible(False)
        cb.ax.tick_params(length=0, colors=INK2)
        ax.set_title(title, pad=10)
        fig.tight_layout()
        save(fig, out, fname)


def plot_rules(df: pd.DataFrame, out: Path) -> None:
    # one row per (family, rule); NaN where a participant never saw that rule
    df = df.copy()
    df["row"] = df["family"] + " · " + df["rule"]
    acc = df.pivot(index="row", columns="participant", values="accuracy")
    n = df.pivot(index="row", columns="participant", values="n_trials")
    acc = acc.sort_index()
    n = n.loc[acc.index]
    fig, ax = plt.subplots(figsize=(1.0 * acc.shape[1] + 5.5, 0.34 * len(acc) + 1.6))
    im = heatmap(ax, acc, 0.3, 1.0, lambda v: f"{v:.0%}", notes=n, fontsize=7)
    # family separators
    fams = [r.split(" · ")[0] for r in acc.index]
    for i in range(1, len(fams)):
        if fams[i] != fams[i - 1]:
            ax.axhline(i - 0.5, color=INK2, linewidth=1.2)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("accuracy", color=INK2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, colors=INK2)
    ax.xaxis.tick_top()
    ax.set_title("Accuracy by rule (cells show n decision trials; – = rule not shown)",
                 pad=28)
    fig.tight_layout()
    save(fig, out, "rule_accuracy.png")


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path, default=HERE / "results",
                    help="folder with the CSVs from accuracy.py (default: ./results)")
    args = ap.parse_args()
    res = args.results
    out = res / "plots"
    out.mkdir(parents=True, exist_ok=True)

    overall = pd.read_csv(res / "overall.csv")
    sess = pd.read_csv(res / "by_session.csv")
    fam = pd.read_csv(res / "by_family.csv")
    rule = pd.read_csv(res / "by_rule.csv")

    plot_overall(overall, out)
    plot_sessions(sess, out, "accuracy", BLUE, "Accuracy across sessions", "accuracy",
                  "session_accuracy.png", pct=True)
    plot_sessions(sess, out, "rt_median", ORANGE, "Median reaction time across sessions",
                  "seconds", "session_rt.png", pct=False)
    # family table has no median RT; pull it from rt_mean as the stored statistic
    if "rt_median" not in fam.columns:
        fam["rt_median"] = fam["rt_mean"]
    plot_family(fam, out)
    plot_rules(rule, out)


if __name__ == "__main__":
    main()
