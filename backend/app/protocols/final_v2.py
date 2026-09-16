import math
import random

from backend.app.protocols.final_v1 import DRAFT_CHUNKS


PROTOCOL_VERSION = "final-v2.1-draft"

FREE_RECALL_NORMAL_MS = 2000
FREE_RECALL_FAST_MS = 1000
FREE_RECALL_PAUSE_SECONDS = 15
CARD_GAME_SECONDS = 15
FREE_RECALL_RESPONSE_SECONDS = 90

SERIAL_BASELINE_LENGTHS = (6, 7, 8, 9)
SERIAL_ITEM_MS = 2000
SERIAL_BLANK_MS = 500
SERIAL_RESPONSE_SECONDS = 30
SECTION_BREAK_SECONDS = 120

DANISH_LETTER_POOL = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZÆØÅ")


def generate_letter_sequence(rng: random.Random, length: int) -> str:
    if length > len(DANISH_LETTER_POOL):
        raise ValueError("A serial sequence cannot repeat letters.")
    return "".join(rng.sample(DANISH_LETTER_POOL, length))


def build_free_recall_conditions(words: list[str]) -> list[dict]:
    if len(words) != 60:
        raise ValueError("The v2 protocol requires exactly 60 free-recall words.")
    if len(set(words)) != len(words):
        raise ValueError("Free-recall words must be unique within a session.")

    conditions = [
        {"name": "baseline", "label": "Baseline", "display_ms": FREE_RECALL_NORMAL_MS, "post_task": "none"},
        {"name": "fast", "label": "Fast presentation", "display_ms": FREE_RECALL_FAST_MS, "post_task": "none"},
        {"name": "pause", "label": "Pause", "display_ms": FREE_RECALL_NORMAL_MS, "post_task": "pause"},
        {"name": "working_memory", "label": "Memory game", "display_ms": FREE_RECALL_NORMAL_MS, "post_task": "card_game"},
    ]
    for index, condition in enumerate(conditions):
        condition["words"] = words[index * 15 : (index + 1) * 15]
        condition["trial_number"] = index + 1
    return conditions


def build_baseline_trials(rng: random.Random) -> list[dict]:
    return [
        build_serial_trial(
            rng,
            trial_number=index + 5,
            length=length,
            part="serial_baseline",
            condition=f"baseline_{length}",
            label=f"Baseline · {length} letters",
        )
        for index, length in enumerate(SERIAL_BASELINE_LENGTHS)
    ]


def calculate_adaptive_length(positional_matches: dict[int, int]) -> dict:
    if set(positional_matches) != set(SERIAL_BASELINE_LENGTHS):
        raise ValueError("Adaptive length requires baseline results for lengths 6, 7, 8, and 9.")

    accuracies = {}
    for length in SERIAL_BASELINE_LENGTHS:
        matches = positional_matches[length]
        if not 0 <= matches <= length:
            raise ValueError(f"Positional matches for length {length} must be between 0 and {length}.")
        accuracies[str(length)] = matches / length

    mean_accuracy = sum(accuracies.values()) / len(accuracies)
    scaled_length = mean_accuracy * 9
    rounded_length = math.floor(scaled_length)
    adaptive_length = max(6, min(9, rounded_length))
    return {
        "positional_matches": {str(length): positional_matches[length] for length in SERIAL_BASELINE_LENGTHS},
        "positional_accuracies": accuracies,
        "mean_accuracy": mean_accuracy,
        "scaled_length": scaled_length,
        "rounding": "floor",
        "adaptive_length": adaptive_length,
    }


def build_adaptive_trials(rng: random.Random, adaptive_length: int) -> list[dict]:
    if adaptive_length not in SERIAL_BASELINE_LENGTHS:
        raise ValueError("Adaptive length must be between 6 and 9.")

    trials = [
        build_serial_trial(
            rng,
            trial_number=9,
            length=adaptive_length,
            part="secondary_tasks",
            condition="articulatory_suppression",
            label="Articulatory suppression",
        ),
        build_serial_trial(
            rng,
            trial_number=10,
            length=adaptive_length,
            part="secondary_tasks",
            condition="finger_tapping",
            label="Finger tapping",
        ),
    ]

    chunks = [chunk for chunk, _ in rng.sample(DRAFT_CHUNKS, 3)]
    sequence = "".join(chunks)
    trials.append({
        "trial_number": 11,
        "part": "chunking",
        "condition": "grouped",
        "label": "Meaningful chunks",
        "length": 9,
        "sequence": sequence,
        "presentation_units": chunks,
        "unit_display_ms": SERIAL_ITEM_MS,
        "intervals": [SERIAL_BLANK_MS] * (len(chunks) - 1),
        "total_exposure_ms": len(chunks) * SERIAL_ITEM_MS,
        "chunks": chunks,
        "matched_baseline_trial_number": 8,
    })
    return trials


def build_serial_trial(
    rng: random.Random,
    *,
    trial_number: int,
    length: int,
    part: str,
    condition: str,
    label: str,
) -> dict:
    sequence = generate_letter_sequence(rng, length)
    return {
        "trial_number": trial_number,
        "part": part,
        "condition": condition,
        "label": label,
        "length": length,
        "sequence": sequence,
        "presentation_units": list(sequence),
        "unit_display_ms": SERIAL_ITEM_MS,
        "intervals": [SERIAL_BLANK_MS] * (length - 1),
        "total_exposure_ms": length * SERIAL_ITEM_MS,
    }