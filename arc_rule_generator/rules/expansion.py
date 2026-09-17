import random

from arc_rule_generator.rules._common import make_grids, make_params, rand_between, COLORS


def generate_star_expansion_single_step(star_num=(1, 4)):
    return _generate_expansion(
        object_count_range=star_num,
        directions=((1, 1), (1, -1), (-1, 1), (-1, -1)),
        mode="step",
    )


def generate_star_expansion_ray(star_num=(1, 3)):
    return _generate_expansion(
        object_count_range=star_num,
        directions=((1, 1), (1, -1), (-1, 1), (-1, -1)),
        mode="ray",
    )


def generate_plus_expansion_single_step(plus_num=(1, 4)):
    return _generate_expansion(
        object_count_range=plus_num,
        directions=((1, 0), (-1, 0), (0, 1), (0, -1)),
        mode="step",
    )


def generate_plus_expansion_ray(plus_num=(1, 3)):
    return _generate_expansion(
        object_count_range=plus_num,
        directions=((1, 0), (-1, 0), (0, 1), (0, -1)),
        mode="ray",
    )


def generate_3arm_star_expansion_ray(star_num=(1, 3)):
    return _generate_expansion(
        object_count_range=star_num,
        directions=((1, 1), (1, -1), (-1, -1)),
        mode="ray",
    )


def generate_8_arm_star_expansion_ray(star_num=(1, 2)):
    return _generate_expansion(
        object_count_range=star_num,
        directions=((1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)),
        mode="ray",
    )


def _generate_expansion(object_count_range, directions, mode):
    grid_input, grid_output = make_grids()

    n = rand_between(*object_count_range)
    centers = random.sample(grid_input.get_interior_cells(), n)

    grid_input.set_multi_cells(centers, COLORS[0])

    if mode == "step":
        _apply_single_step(grid_output, centers, directions)
        stimulus = "step_expansion"

    elif mode == "ray":
        _apply_ray(grid_output, centers, directions)
        stimulus = "ray_expansion"

    grid_output.set_multi_cells(centers, COLORS[0])

    params = make_params(
        event="expansion",
        condition="shape",
        stimulus=stimulus,
        colors=COLORS[:2],
        n_objects=n,
    )

    return grid_input, grid_output, params


def _apply_single_step(grid_output, centers, directions):
    for row, col in centers:
        for d_row, d_col in directions:
            grid_output.set_cell(row + d_row, col + d_col, COLORS[1])


def _apply_ray(grid_output, centers, directions):
    rows, cols = grid_output.rows, grid_output.cols

    for row, col in centers:
        for d_row, d_col in directions:
            current_row = row + d_row
            current_col = col + d_col

            while 0 <= current_row < rows and 0 <= current_col < cols:
                grid_output.set_cell(current_row, current_col, COLORS[1])
                current_row += d_row
                current_col += d_col
