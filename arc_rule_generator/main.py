import json
from pathlib import Path

from stimulus import Stimulus
from visualize import save_combined_grids

from rules.arithmetic import (
    generate_minority_takeover,
    generate_majority_takeover,
    generate_equalize_colors,
    generate_increment_majority_color,
    generate_increment_minority_color,
)
from rules.attraction import (
    generate_color_attraction,
    generate_size_attraction,
    generate_color_repulsion,
    generate_falling_blocks,
    generate_floating_blocks,
)
from rules.expansion import (
    generate_star_expansion_single_step,
    generate_star_expansion_ray,
    generate_plus_expansion_single_step,
    generate_plus_expansion_ray,
    generate_3arm_star_expansion_ray,
)
from rules.occlusion import (
    generate_occlusion_reversal,
    generate_occlusion_mirror_x,
    generate_occlusion_mirror_y,
    generate_occlusion_rotate_90,
    generate_occlusion_rotate_180,
)
from rules.recolor import (
    generate_shape_color_mapping,
    generate_touching_edges_recolor,
    generate_color_inversion,
)


RULES = {
    "occlusion.occlusion_reversal": generate_occlusion_reversal,
    "occlusion.mirror_x": generate_occlusion_mirror_x,
    "occlusion.mirror_y": generate_occlusion_mirror_y,
    "occlusion.rotate_90": generate_occlusion_rotate_90,
    "occlusion.rotate_180": generate_occlusion_rotate_180,

    "attraction.color_attraction": generate_color_attraction,
    "attraction.size_attraction": generate_size_attraction,
    "attraction.falling_blocks": generate_falling_blocks,
    "attraction.floating_blocks": generate_floating_blocks,
    "attraction.color_repulsion": generate_color_repulsion,

    "expansion.star_step": generate_star_expansion_single_step,
    "expansion.star_ray": generate_star_expansion_ray,
    "expansion.plus_step": generate_plus_expansion_single_step,
    "expansion.plus_ray": generate_plus_expansion_ray,
    "expansion.3_arm_star_ray": generate_3arm_star_expansion_ray,

    "arithmetic.minority_takeover": generate_minority_takeover,
    "arithmetic.majority_takeover": generate_majority_takeover,
    "arithmetic.equalize_colors": generate_equalize_colors,
    "arithmetic.increment_majority_color": generate_increment_majority_color,
    "arithmetic.increment_minority_color": generate_increment_minority_color,

    "recolor.shape_color_mapping": generate_shape_color_mapping,
    "recolor.touching_edges_recolor": generate_touching_edges_recolor,
    "recolor.color_inversion": generate_color_inversion,
}


def main(n):
    for rule, generator in RULES.items():
        for _ in range(n):
            generate_stimulus(rule, generator)


def generate_stimulus(rule, generator, out_root="stimuli"):
    base = Path(out_root) / rule
    base.mkdir(parents=True, exist_ok=True)

    jsonl_path = base / "stimuli.jsonl"
    idx = sum(1 for _ in jsonl_path.open(encoding="utf-8")) + 1 if jsonl_path.exists() else 1

    inp, out, params = (*generator(), {})[:3]

    stim_id = f"{rule}.t{idx}"
    save_combined_grids(inp, out, str(base / f"{stim_id}.combined.png"))

    stimulus = Stimulus(
        id=stim_id,
        family=rule.split(".", 1)[0],
        rule=rule.rsplit(".", 1)[-1],
        params=params,
    )

    with jsonl_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(stimulus.to_json_dict(), ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main(50)