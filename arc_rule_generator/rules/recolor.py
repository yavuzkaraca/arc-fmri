import random

from arc_rule_generator.rules._common import make_grids, make_params, rand_between, COLORS

SHAPE_DIRECTIONS = {
    "plus": ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)),
    "cross": ((0, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)),
}


def generate_color_inversion(object_num=(3, 5)):
    grid_input, grid_output, placed = _generate_cross_plus_input(object_num)

    for _, cells, color in placed:
        output_color = COLORS[1] if color == COLORS[0] else COLORS[0]
        grid_output.set_multi_cells(cells, output_color)

    params = make_params(
        event="recoloring",
        condition="color",
        stimulus="cross_plus",
        colors=COLORS[:2],
        n_objects=len(placed),
    )

    return grid_input, grid_output, params


def generate_touching_edges_recolor(object_num=(3, 5)):
    grid_input, grid_output, placed = _generate_cross_plus_input(object_num)

    for i, (_, cells, _) in enumerate(placed):
        touches_other = any(
            _objects_touch(cells, other_cells)
            for j, (_, other_cells, _) in enumerate(placed)
            if i != j
        )

        output_color = COLORS[0] if touches_other else COLORS[1]
        grid_output.set_multi_cells(cells, output_color)

    params = make_params(
        event="recoloring",
        condition=["shape", "neighbor"],
        stimulus="cross_plus",
        colors=COLORS[:2],
        n_objects=len(placed),
    )

    return grid_input, grid_output, params


def generate_shape_color_mapping(object_num=(3, 5)):
    grid_input, grid_output, placed = _generate_cross_plus_input(object_num)

    shape_colors = {
        "cross": COLORS[0],
        "plus": COLORS[1],
    }

    for shape, cells, _ in placed:
        grid_output.set_multi_cells(cells, shape_colors[shape])

    params = make_params(
        event="recoloring",
        condition="shape",
        stimulus="cross_plus",
        colors=COLORS[:2],
        n_objects=len(placed),
    )

    return grid_input, grid_output, params


def _generate_cross_plus_input(object_num):
    """
    Generate cross/plus objects guaranteeing:
    - at least one edge-touching pair
    - at least one object without edge contact
    - same-shaped objects with different colors
    - edge-touching objects with different colors and different shapes

    If avoid_corner_only is True, reject corner-only contact between
    objects, so isolated objects have neither edge nor corner contact.
    """
    while True:
        n_objects = rand_between(*object_num)

        grid_input, grid_output = make_grids()
        placed = _place_cross_plus_objects(grid_input, n_objects)

        if len(placed) != n_objects:
            continue

        if _has_corner_only_contact(placed):
            continue

        if not _has_touching_pair_and_isolated_object(placed):
            continue

        if not _has_touching_different_shapes(placed):
            continue

        while True:
            colored = [
                (shape, cells, random.choice(COLORS[:2]))
                for shape, cells in placed
            ]

            if (
                _has_same_shape_different_colors(colored)
                and _has_touching_different_shapes_and_colors(colored)
            ):
                break

        for _, cells, color in colored:
            grid_input.set_multi_cells(cells, color)

        return grid_input, grid_output, colored


def _place_cross_plus_objects(grid, n_objects):
    candidates = grid.get_interior_cells()
    random.shuffle(candidates)

    used = set()
    placed = []

    for _ in range(n_objects):
        shape = random.choice(("cross", "plus"))

        for center in candidates:
            cells = _shape_cells(center, SHAPE_DIRECTIONS[shape])

            if any(cell in used for cell in cells):
                continue

            used.update(cells)
            placed.append((shape, cells))
            break

    return placed


def _shape_cells(center, directions):
    row, col = center

    return [
        (row + d_row, col + d_col)
        for d_row, d_col in directions
    ]


def _objects_touch(cells1, cells2):
    """Return True if two objects touch along an edge."""
    cells2 = set(cells2)

    for row, col in cells1:
        for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (row + d_row, col + d_col) in cells2:
                return True

    return False


def _has_corner_only_contact(placed):
    """Return True if any two objects touch diagonally but not along an edge."""
    for i, (_, cells1) in enumerate(placed):
        for _, cells2 in placed[i + 1:]:
            if _objects_touch(cells1, cells2):
                continue

            cells2 = set(cells2)

            if any(
                (row + d_row, col + d_col) in cells2
                for row, col in cells1
                for d_row, d_col in (
                    (1, 1), (1, -1), (-1, 1), (-1, -1)
                )
            ):
                return True

    return False


def _has_touching_pair_and_isolated_object(placed):
    touched = [False] * len(placed)

    for i, (_, cells1) in enumerate(placed):
        for j in range(i + 1, len(placed)):
            _, cells2 = placed[j]

            if _objects_touch(cells1, cells2):
                touched[i] = True
                touched[j] = True

    return any(touched) and any(not is_touched for is_touched in touched)


def _has_same_shape_different_colors(placed):
    return any(
        shape1 == shape2 and color1 != color2
        for i, (shape1, _, color1) in enumerate(placed)
        for shape2, _, color2 in placed[i + 1:]
    )


def _has_touching_different_shapes(placed):
    return any(
        shape1 != shape2 and _objects_touch(cells1, cells2)
        for i, (shape1, cells1) in enumerate(placed)
        for shape2, cells2 in placed[i + 1:]
    )


def _has_touching_different_shapes_and_colors(placed):
    return any(
        shape1 != shape2
        and color1 != color2
        and _objects_touch(cells1, cells2)
        for i, (shape1, cells1, color1) in enumerate(placed)
        for shape2, cells2, color2 in placed[i + 1:]
    )