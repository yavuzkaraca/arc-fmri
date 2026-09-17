import random

from arc_rule_generator.rules._common import make_grids, make_params, COLORS


def generate_majority_takeover():
    return _generate_dot_arithmetic_recolor(2)


def generate_middle_takeover():
    return _generate_dot_arithmetic_recolor(1)


def generate_minority_takeover():
    return _generate_dot_arithmetic_recolor(0)


def _generate_dot_arithmetic_recolor(rank):
    grid_input, _ = make_grids()

    while True:  # get smth like (1,2,3) or (1,4,5)
        counts = sorted(random.sample(range(1, 7), 3))
        if sum(counts) <= 12:
            break

    colors = random.sample(COLORS[:3], 3)

    # One dot for each col and row, like numbers in sudoku :D
    n_dots = sum(counts)
    rows = random.sample(range(grid_input.rows), n_dots)
    cols = random.sample(range(grid_input.cols), n_dots)
    all_positions = list(zip(rows, cols))

    start = 0
    for color, count in zip(colors, counts):
        grid_input.set_multi_cells(all_positions[start:start + count], color)
        start += count

    grid_output = grid_input.copy()
    grid_output.set_multi_cells(all_positions, colors[rank])

    params = make_params(
        event="recoloring",
        condition=["color", "counting"],
        stimulus="dots",
        colors=colors,
        n_objects=sum(counts),
        counting_type=_counting_type(counts, rank),
        n_recolored=sum(counts) - counts[rank],
    )
    return grid_input, grid_output, params


def _counting_type(counts, rank, threshold=0.3):
    minority, middle, majority = counts

    lower_boundary = (middle - minority) / middle
    upper_boundary = (majority - middle) / majority

    if rank == 0:
        easiness = lower_boundary
    elif rank == 2:
        easiness = upper_boundary
    else:
        easiness = min(lower_boundary, upper_boundary)

    return "soft" if easiness >= threshold else "hard"
