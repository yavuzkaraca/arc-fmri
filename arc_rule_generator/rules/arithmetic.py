import random

from arc_rule_generator.rules._common import make_grids, make_params, rand_between, COLORS


def generate_majority_takeover(count_range=(1, 6)):
    return _generate_dot_arithmetic_recolor(
        operation="majority_takeover",
        count_range=count_range
    )


def generate_minority_takeover(count_range=(1, 6)):
    return _generate_dot_arithmetic_recolor(
        operation="minority_takeover",
        count_range=count_range
    )


def generate_equalize_colors(count_range=(1, 6)):
    return _generate_dot_arithmetic_recolor(
        operation="equalize",
        count_range=count_range,
    )


def generate_increment_majority_color(count_range=None):
    return _generate_dot_arithmetic_recolor(
        operation="majority_increment",
        count_range=count_range or random.choice([(2, 3), (3, 4)]),
    )


def generate_increment_minority_color(count_range=None):
    return _generate_dot_arithmetic_recolor(
        operation="minority_increment",
        count_range=count_range or random.choice([(2, 3), (3, 4)]),
    )


def _generate_dot_arithmetic_recolor(operation, count_range):
    grid_input, _ = make_grids()

    n1, n2 = _sample_two_unique_counts(count_range)

    while (operation == "equalize" and
           ((n1 + n2) % 2 or abs(n1 - n2) < 4)):  # careful: poor count_range causes infinite loop
        n1, n2 = _sample_two_unique_counts(count_range)

    n_majority = max(n1, n2)
    n_minority = min(n1, n2)

    majority_color, minority_color = random.sample(COLORS[:2], 2)

    # One dot for each row and column.
    rows = random.sample(range(grid_input.rows), n_majority + n_minority)
    cols = random.sample(range(grid_input.cols), n_majority + n_minority)
    all_positions = list(zip(rows, cols))

    majority_positions = all_positions[:n_majority]
    minority_positions = all_positions[n_majority:]

    grid_input.set_multi_cells(majority_positions, majority_color)
    grid_input.set_multi_cells(minority_positions, minority_color)

    match operation:
        case "majority_takeover":
            source_positions = all_positions
            target_color = majority_color
            n_to_flip = len(all_positions)

        case "minority_takeover":
            source_positions = all_positions
            target_color = minority_color
            n_to_flip = len(all_positions)

        case "equalize":
            source_positions = majority_positions
            target_color = minority_color
            n_to_flip = (n_majority - n_minority) // 2

        case "majority_increment":
            source_positions = minority_positions
            target_color = majority_color
            n_to_flip = 1

        case "minority_increment":
            source_positions = majority_positions
            target_color = minority_color
            n_to_flip = 1

    grid_output = grid_input.copy()
    recolored_positions = sorted(source_positions)[:n_to_flip]
    grid_output.set_multi_cells(recolored_positions, target_color)

    params = make_params(
        event="recoloring",
        condition=["color", "counting"],
        stimulus="dots",
        colors=(majority_color, minority_color),
        n_objects=n_majority + n_minority,
        counting_type=_counting_type(n_majority, n_minority),
        target=operation,
        n_recolored=n_to_flip,
    )

    return grid_input, grid_output, params


def _sample_two_unique_counts(count_range):
    n1 = rand_between(*count_range)
    n2 = rand_between(*count_range)

    while n1 == n2:
        n2 = rand_between(*count_range)

    return n1, n2


def _counting_type(n_majority, n_minority, threshold=0.3):
    easiness = (n_majority - n_minority) / n_majority
    return "soft" if easiness >= threshold else "hard"
