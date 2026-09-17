import numpy as np
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

COLOR_VALUES = {
    "red":  (1.000, 0.365, 0.365),
    "blue": (0.532, 0.532, 1.000),
    "gray": (0.583, 0.583, 0.583),
    "green": (0.365, 0.646, 0.365),
    "yellow": (0.601, 0.601, 0.200),
}

def save_combined_grids(grid1, grid2, save_path="combined.png"):
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(grid1.cols + grid2.cols + 2, max(grid1.rows, grid2.rows)),
        gridspec_kw={"wspace": 0.25},
    )

    fig.patch.set_facecolor("gray")

    _draw_grid(axes[0], grid1)
    _draw_grid(axes[1], grid2)

    # Draw the arrow between input and output grids.
    fig.text(0.51, 0.5, "→", ha="center", va="center", fontsize=140, color="white", fontweight="bold")

    plt.savefig(save_path, dpi=100, bbox_inches="tight", pad_inches=0.03)
    plt.close()

def save_grid(grid, save_path="output.png"):
    fig, ax = plt.subplots(figsize=(grid.cols, grid.rows))
    fig.patch.set_facecolor("gray")

    _draw_grid(ax, grid)

    plt.savefig(save_path, dpi=100, bbox_inches="tight", pad_inches=0.03)
    plt.close()

def resolve_color(name):
    if name in COLOR_VALUES:
        return COLOR_VALUES[name]
    return mcolors.to_rgb(name)


def _draw_grid(ax, grid):
    rgb_grid = np.array([
        [resolve_color(grid.get_cell(row, col)) for col in range(grid.cols)]
        for row in range(grid.rows)
    ])

    ax.imshow(
        rgb_grid,
        origin="lower",  # so its like coordinate system (x = col, y = row)
        interpolation="none",
        extent=(0, grid.cols, 0, grid.rows),
    )

    for col in range(grid.cols + 1):
        ax.axvline(col, color="dimgray", linewidth=2)

    for row in range(grid.rows + 1):
        ax.axhline(row, color="dimgray", linewidth=2)

    ax.set_xlim(0, grid.cols)
    ax.set_ylim(0, grid.rows)
    ax.set_aspect("equal")
    ax.axis("off")