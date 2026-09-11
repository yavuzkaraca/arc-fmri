"""
Build "session.json" for the fMRI experiment on MATLAB/PTB.

Make sure your generated stimulus dataset has:
- at least 2 rules in each family to enable comparison
- at least twice many decision trials as rule number in a family for rule coverage
- at least half many stimuli in each rule as decision trials (bc each trial presents two stimuli)
"""

import json
import random
from pathlib import Path

if __name__ == "__main__":

    stimulus_dataset_dir: str = "stimuli"  # rename the folder later
    output_dir: str = "."
    participant: str = "p01"  # must be "pXX" where X is a digit

    number_of_sessions: int = 8  # must be even number for balancing blocks
    number_of_decision_trials_per_block: int = 8  # decision trials > 2 * number of rules in a family

    # Counterbalance frame colors (yellow/cyan) for contexts
    if int(participant.removeprefix("p")) % 2 == 0:
        context_frame_colors = {"inference": "cyan", "application": "yellow"}
    else:
        context_frame_colors = {"inference": "yellow", "application": "cyan"}

    # ------------------------------------------------------------------ #
    # Setup                                                              #
    # ------------------------------------------------------------------ #

    stimulus_dataset_path = Path(stimulus_dataset_dir).resolve()
    base_dir = Path(output_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    # Collect pools: pools[family][rule] -> list of stimulus records (each record points to its combined image)
    pools: dict[str, dict[str, list[dict]]] = {}

    for rule_directory in stimulus_dataset_path.iterdir():
        for row in map(json.loads, (rule_directory / "stimuli.jsonl").read_text(encoding="utf-8").splitlines()):
            family = row["family"]
            rule = row["rule"]
            if family not in pools:
                pools[family] = {}
            if rule not in pools[family]:
                pools[family][rule] = []
            pools[family][rule].append(
                {
                    "id": row["id"],
                    "combined_path": rule_directory / f'{row["id"]}.combined.png',
                    "params": row["params"],
                }
            )

    families = list(pools)
    number_of_blocks_per_session = len(families)  # one block per family, every session

    # Running per-family context balance, carried across every session built in this run.
    context_tally: dict[str, dict[str, int]] = {
        family: {"inference": 0, "application": 0} for family in families
    }


    # ------------------------------------------------------------------ #
    # Nested functions                                                   #
    # ------------------------------------------------------------------ #

    def alternating_context_sequence(starting_context: str, length: int) -> list[str]:
        """
        e.g. ("inference", 5) -> ["inference", "application", "inference", "application", "inference"]
        """
        other_context = "application" if starting_context == "inference" else "inference"
        return [starting_context if i % 2 == 0 else other_context for i in range(length)]


    def assign_families_to_contexts(context_slots: list[str], rng: random.Random) -> list[tuple[str, str]]:
        """
        Decide, for this session, which family fills each context slot.
        Returns (family, context) pairs in slot order.

        Families most "owed" inference (fewest inference blocks relative to application blocks so far) fill the
        inference slots first; the rest fill the application slots. Ties are broken randomly.
        """
        n_inference_slots = context_slots.count("inference")

        shuffled_families = families[:]
        rng.shuffle(shuffled_families)  # random tie-break for equally-owed families

        ranked_by_inference_need = sorted(
            shuffled_families,
            key=lambda family: context_tally[family]["application"] - context_tally[family]["inference"],
            reverse=True,  # most owed inference first
        )

        inference_families = ranked_by_inference_need[:n_inference_slots]
        application_families = ranked_by_inference_need[n_inference_slots:]

        rng.shuffle(inference_families)  # randomize which slot within the group each family gets
        rng.shuffle(application_families)

        inference_iter = iter(inference_families)
        application_iter = iter(application_families)
        return [
            (next(inference_iter) if context == "inference" else next(application_iter), context)
            for context in context_slots
        ]


    def build_block(block_index: int, family: str, context: str, rng: random.Random) -> dict:
        """
        Build one block: single family, single context, one initial trial, followed by the decision trials.
        """
        used_stimulus_ids: set[str] = set()
        rules = [(family, rule) for rule in pools[family]]

        rule_path = build_rule_path(rules, number_of_decision_trials_per_block, context, rng)

        initial_family, initial_rule = rule_path[0]
        first, second = pick_pair(pools[initial_family][initial_rule], used_stimulus_ids, rng)
        trials = [make_trial_entry(initial_family, initial_rule, first, second, correct=None)]

        for index in range(1, len(rule_path)):
            family_i, rule_i = rule_path[index]
            compare_to = rule_path[0] if context == "application" else rule_path[index - 1]
            correct_label = "same" if (family_i, rule_i) == compare_to else "different"

            first, second = pick_pair(pools[family_i][rule_i], used_stimulus_ids, rng)
            trials.append(make_trial_entry(family_i, rule_i, first, second, correct=correct_label))

        return {
            "block_index": block_index,
            "family": family,
            "context": context,
            "frame_color": context_frame_colors[context],
            "trials": trials,
        }


    def build_rule_path(
            rules: list[tuple[str, str]],
            number_of_decisions: int,
            context: str,  # "inference" or "application"
            rng: random.Random,
    ) -> list[tuple[str, str]]:
        """
        Build the rule sequence for one block: respects same/different label
        Inference (swap): each trial compares to the previous trial's rule.
        Application (stable): each trial compares to the block's first (rule_path[0]).
        """

        rng.shuffle(rules)  # randomize rule priority (affects coverage order)

        labels = make_labels(number_of_decisions, max_run=3, rng=rng)

        first_rule = rng.choice(rules)
        rule_path = [first_rule]
        used_rules = {first_rule}

        for label in labels:
            previous_rule = rule_path[-1]
            compare_target = first_rule if context == "application" else previous_rule

            if label == "same":
                rule_path.append(compare_target)

            elif label == "different":
                candidates = [r for r in rules if r != compare_target and r not in used_rules]
                if not candidates:
                    # every other rule already used in this block -> allow reuse
                    candidates = [r for r in rules if r != compare_target]

                next_rule = rng.choice(candidates)
                rule_path.append(next_rule)
                used_rules.add(next_rule)

        return rule_path


    def make_labels(number_of_decisions: int, max_run: int, rng: random.Random) -> list[str]:
        """
        Generate a balanced same/different label sequence with a cap on repeated labels (prevents long streaks)
        """
        number_of_same_trials = number_of_decisions // 2
        number_of_different_trials = number_of_decisions - number_of_same_trials
        labels = ["same"] * number_of_same_trials + ["different"] * number_of_different_trials

        while True:
            rng.shuffle(labels)
            run_length = 1
            valid = True
            for i in range(1, len(labels)):
                if labels[i] == labels[i - 1]:
                    run_length += 1
                    if run_length > max_run:
                        valid = False
                        break
                else:
                    run_length = 1
            if valid:
                return labels


    def pick_pair(stimulus_pool: list[dict], used_stimulus_ids: set[str], rng: random.Random) -> tuple[dict, dict]:
        """
        Draw two unique stimuli from a rule pool (no reuse within the current block).
        """
        unused_records = [record for record in stimulus_pool if record["id"] not in used_stimulus_ids]
        rng.shuffle(unused_records)  # Randomize which unused items are selected.

        # detect if this is color attraction via params
        has_bigger_block = any("bigger_block" in r.get("params", {}) for r in unused_records)
        if has_bigger_block:
            first = next(r for r in unused_records if r["params"]["bigger_block"] == "red")
            second = next(r for r in unused_records if r["params"]["bigger_block"] == "blue")
        else:
            first, second = unused_records[0], unused_records[1]

        used_stimulus_ids.add(first["id"])
        used_stimulus_ids.add(second["id"])
        return first, second


    def make_trial_entry(family: str, rule: str, first: dict, second: dict, correct: str | None) -> dict:
        """
        Create the JSON trial entry
        """
        trial = {
            "imgs": [
                relative_path(first["combined_path"]),
                relative_path(second["combined_path"])
            ],
            "family": family,
            "rule": rule,
            "correct": correct or "",
            "stimuli": [
                {
                    "id": first["id"],
                    "params": first.get("params"),
                },
                {
                    "id": second["id"],
                    "params": second.get("params"),
                },
            ],
        }
        return trial

    def relative_path(image_path: Path) -> str:
        """
        Convert absolute file paths to paths relative to the session file location (portable across machines)
        """
        return str(image_path.resolve().relative_to(base_dir)).replace("\\", "/")


    # ------------------------------------------------------------------ #
    # Execution                                                          #
    # ------------------------------------------------------------------ #

    for session_index in range(1, number_of_sessions + 1):
        session_file_path = base_dir / f"session_{session_index:02d}.json"

        seed = int(participant.removeprefix("p")) * 100 + session_index
        rng = random.Random(seed)

        # Deterministic alternation guarantees an exact 50/50 split of session-starting
        # context across the whole run, on top of the per-family tally correction below.
        starting_context = "inference" if session_index % 2 == 1 else "application"
        context_slots = alternating_context_sequence(starting_context, number_of_blocks_per_session)

        family_context_pairs = assign_families_to_contexts(context_slots, rng)

        blocks = []
        next_block_index = 1
        for family, context in family_context_pairs:
            blocks.append(build_block(next_block_index, family, context, rng))
            context_tally[family][context] += 1
            next_block_index += 1

        number_of_trials_per_block = 1 + number_of_decision_trials_per_block  # +1 bc initial trial
        number_of_trials_total = number_of_blocks_per_session * number_of_trials_per_block

        session = {
            "participant": participant,
            "seed": seed,
            "starting_context": starting_context,
            "number_of_decision_trials_per_block": number_of_decision_trials_per_block,
            "number_of_trials_per_block": number_of_trials_per_block,
            "number_of_blocks": number_of_blocks_per_session,
            "number_of_trials_total": number_of_trials_total,
            "blocks": blocks,
        }

        session_file_path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
