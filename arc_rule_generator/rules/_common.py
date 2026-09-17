import random

from arc_rule_generator.grid import Grid


GRID_SIZE = (12, 12)

COLORS = (
    "red",
    "blue",
    "yellow",
    "gray"
)


def make_grids():
    rows, cols = GRID_SIZE
    return Grid(rows, cols), Grid(rows, cols)


def make_params(event, condition, stimulus, colors, n_objects, **extra):
    return {
        "event": event,
        "condition": condition,
        "stimulus": stimulus,
        "colors": colors,
        "n_objects": n_objects,
        **extra
    }

def rand_between(a, b):
    return random.randint(a, b) if a < b else a
