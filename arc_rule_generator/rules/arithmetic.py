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

    all_positions = random.sample(
        grid_input.get_coordinates(),
        n_majority + n_minority,
    )

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



NEIGHBORS = tuple(
    (dr, dc)
    for dr in range(-2, 3)
    for dc in range(-2, 3)
    if (dr, dc) != (0, 0)
)


def generate_majority_in_small_overtakes():
    return _generate_cluster_takeover("small", "majority")


def generate_minority_in_small_overtakes():
    return _generate_cluster_takeover("small", "minority")


def generate_majority_in_big_overtakes():
    return _generate_cluster_takeover("big", "majority")


def generate_minority_in_big_overtakes():
    return _generate_cluster_takeover("big", "minority")


def _generate_cluster_takeover(source_cluster, effective_color):
    grid_input, _ = make_grids()
    big_counts = random.choice(((3, 4), (2, 5)))
    small_positions, big_positions = _place_clusters(
        grid_input, n_small=3, n_big=sum(big_counts)
    )

    clusters = {
        "small": _color_cluster(grid_input, small_positions, (1, 2)),
        "big": _color_cluster(grid_input, big_positions, big_counts),
    }
    target_cluster = "big" if source_cluster == "small" else "small"
    source = clusters[source_cluster]
    target = clusters[target_cluster]
    target_color = source[f"{effective_color}_color"]

    grid_output = grid_input.copy()
    grid_output.set_multi_cells(target["positions"], target_color)

    params = make_params(
        event="recoloring",
        condition=["color", "counting"],
        stimulus="clustered_dots",
        colors=COLORS[:2],
        n_objects=3 + sum(big_counts),
        counting_type=_counting_type(
            source["n_majority"], source["n_minority"]
        ),
        n_recolored=sum(
            grid_input.get_cell(row, col) != target_color
            for row, col in target["positions"]
        ),
    )
    return grid_input, grid_output, params


def _color_cluster(grid, positions, counts):
    minority_color, majority_color = random.sample(COLORS[:2], 2)
    n_minority, n_majority = counts
    positions = random.sample(positions, len(positions))
    grid.set_multi_cells(positions[:n_minority], minority_color)
    grid.set_multi_cells(positions[n_minority:], majority_color)
    return {
        "positions": positions,
        "minority_color": minority_color,
        "majority_color": majority_color,
        "n_minority": n_minority,
        "n_majority": n_majority,
    }


def _place_clusters(grid, n_small, n_big):
    """Choose distant centers with room for two circular patches."""
    small_radius, big_radius = 2.0, 2.5
    centers = [
        (small, big)
        for small in grid.get_coordinates()
        if 2 <= small[0] < grid.rows - 2
           and 2 <= small[1] < grid.cols - 2
        for big in grid.get_coordinates()
        if 2 <= big[0] < grid.rows - 2
           and 2 <= big[1] < grid.cols - 2
           and _distance_squared(small, big) >= (small_radius + big_radius + 4) ** 2
    ]
    if not centers:
        raise ValueError("Grid is too small for two separated circular patches.")

    small_center, big_center = random.choice(centers)
    small = _grow_cluster(small_center, n_small, small_radius)
    big = _grow_cluster(big_center, n_big, big_radius)
    return small, big


def _grow_cluster(center, n_dots, radius):
    """Spread dots within a circular patch, strongly discouraging shared edges."""
    extent = int(radius)
    patch = {
        (center[0] + dr, center[1] + dc)
        for dr in range(-extent, extent + 1)
        for dc in range(-extent, extent + 1)
        if dr * dr + dc * dc <= radius * radius
    }
    cells = {center}
    for _ in range(n_dots - 1):
        candidates = sorted({
            (row + dr, col + dc)
            for row, col in cells
            for dr, dc in NEIGHBORS
        } & patch - cells)
        weights = [
            0.1 ** sum(
                abs(row - r) + abs(col - c) == 1
                for r, c in cells
            ) * min(_distance_squared((row, col), cell) for cell in cells)
            for row, col in candidates
        ]
        cells.add(random.choices(candidates, weights=weights, k=1)[0])
    return sorted(cells)


def _distance_squared(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _counting_type(n_majority, n_minority, threshold=0.3):
    easiness = (n_majority - n_minority) / n_majority
    return "soft" if easiness >= threshold else "hard"
