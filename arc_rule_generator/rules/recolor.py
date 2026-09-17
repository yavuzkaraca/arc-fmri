import random

from arc_rule_generator.rules._common import make_grids, COLORS, make_params


def generate_color_inversion():
    grid_input, grid_output, placed, params = _generate_cross_plus_input()

    for _, cells, color in placed:
        output_color = COLORS[1] if color == COLORS[0] else COLORS[0]
        grid_output.set_multi_cells(cells, output_color)
    params["condition"] = "color"

    return grid_input, grid_output, params


def generate_touching_edges_recolor():
    grid_input, grid_output, placed, params = _generate_cross_plus_input()

    for i, (_, cells, _) in enumerate(placed):
        # First two objects touch; the third is isolated.
        output_color = COLORS[0] if i < 2 else COLORS[1]
        grid_output.set_multi_cells(cells, output_color)

    params["condition"] = ["shape", "neighbor"]

    return grid_input, grid_output, params


def generate_shape_color_mapping():
    grid_input, grid_output, placed, params = _generate_cross_plus_input()

    for shape, cells, _ in placed:
        output_color = COLORS[0] if shape == "cross" else COLORS[1]
        grid_output.set_multi_cells(cells, output_color)

    params["condition"] = "shape"

    return grid_input, grid_output, params


def _generate_cross_plus_input():
    grid_input, grid_output = make_grids()
    repeated_shape, other_shape = random.sample(("cross", "plus"), 2)
    first_color, second_color = random.sample(COLORS[:2], 2)

    # Minimal contact, corner fitting, or maximum contact.
    row_offset, column_offset = random.choice(((1, 3), (2, 2), (0, 2)))
    if random.choice((False, True)):
        row_offset, column_offset = column_offset, row_offset
    row_offset *= random.choice((-1, 1))
    column_offset *= random.choice((-1, 1))

    centers = grid_input.get_interior_cells()
    first_center = random.choice([
        (row, column) for row, column in centers
        if (row + row_offset, column + column_offset) in centers
    ])
    second_center = (first_center[0] + row_offset, first_center[1] + column_offset)

    # Center separation of 4 leaves a gap between the 3x3 shape boxes.
    isolated_center = random.choice([
        (row, column) for row, column in centers
        if all(
            abs(row - pair_row) >= 4 or abs(column - pair_column) >= 4
            for pair_row, pair_column in (first_center, second_center)
        )
    ])
    placed = [
        (repeated_shape, _shape_cells(first_center, repeated_shape), first_color),
        (other_shape, _shape_cells(second_center, other_shape), second_color),
        (repeated_shape, _shape_cells(isolated_center, repeated_shape), second_color),
    ]
    for _, cells, color in placed:
        grid_input.set_multi_cells(cells, color)

    params = make_params(
        event="recoloring",
        condition="undefined",  # will be overwritten from specific rule
        stimulus="cross_plus",
        colors=COLORS[:2],
        n_objects=3,
    )

    return grid_input, grid_output, placed, params



def _shape_cells(center, shape):
    SHAPE_DIRECTIONS = {
        "plus": ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)),
        "cross": ((0, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)),
    }

    row, col = center
    return [
        (row + dr, col + dc)
        for dr, dc in SHAPE_DIRECTIONS[shape]
    ]
