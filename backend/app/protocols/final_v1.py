import csv
import random
from pathlib import Path


PROTOCOL_VERSION = "final-v1.0-draft"

FREE_RECALL_NORMAL_MS = 2000
FREE_RECALL_FAST_MS = 1000
FREE_RECALL_PAUSE_SECONDS = 15
CARD_GAME_SECONDS = 15
FREE_RECALL_RESPONSE_SECONDS = 90

SERIAL_LENGTH = 15
SERIAL_ITEM_MS = 1000
SERIAL_CHUNK_MS = 3000
SERIAL_RESPONSE_SECONDS = 30

# Fifteen common Danish consonants. Shuffling the complete pool prevents
# repetitions and sharply limits accidental Danish word formation.
CONSONANT_POOL = tuple("BDFGHJKLMNPRSTV")
CHUNK_POOL_PATH = Path(__file__).resolve().parents[1] / "data" / "final_v1_chunks.csv"


def load_draft_chunks() -> tuple[tuple[str, str], ...]:
    with CHUNK_POOL_PATH.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    chunks = tuple(
        (row["chunk"].upper(), row["english_meaning"])
        for row in rows
        if row["technical_review"] == "passed" and row["group_approval"] == "approved"
    )
    if len(chunks) < 5:
        raise ValueError("The final protocol requires at least five verified chunk candidates.")
    if len({chunk for chunk, _ in chunks}) != len(chunks):
        raise ValueError("Chunk candidates must be unique.")
    if any(len(chunk) != 3 or not chunk.isalpha() for chunk, _ in chunks):
        raise ValueError("Every chunk candidate must contain exactly three letters.")
    return chunks


DRAFT_CHUNKS = load_draft_chunks()


def generate_consonant_sequence(rng: random.Random) -> str:
    letters = list(CONSONANT_POOL)
    rng.shuffle(letters)
    return "".join(letters)


def generate_chunk_sequence(rng: random.Random) -> tuple[str, list[str]]:
    chunks = [chunk for chunk, _ in rng.sample(DRAFT_CHUNKS, 5)]
    return "".join(chunks), chunks


def build_serial_trials(rng: random.Random) -> list[dict]:
    conditions = [
        ("articulatory_suppression", "Articulatory suppression"),
        ("finger_tapping", "Finger tapping"),
        ("control", "Serial baseline"),
    ]
    trials = []
    for trial_number, (condition, label) in enumerate(conditions, start=1):
        sequence = generate_consonant_sequence(rng)
        trials.append({
            "trial_number": trial_number,
            "part": "serial_letters",
            "condition": condition,
            "label": label,
            "length": SERIAL_LENGTH,
            "sequence": sequence,
            "presentation_units": list(sequence),
            "unit_display_ms": SERIAL_ITEM_MS,
            "intervals": [0] * (SERIAL_LENGTH - 1),
            "total_exposure_ms": SERIAL_LENGTH * SERIAL_ITEM_MS,
        })

    chunk_sequence, chunks = generate_chunk_sequence(rng)
    trials.extend([
        {
            "trial_number": 4,
            "part": "chunking",
            "condition": "ungrouped",
            "label": "Letters shown individually",
            "length": SERIAL_LENGTH,
            "sequence": chunk_sequence,
            "presentation_units": list(chunk_sequence),
            "unit_display_ms": SERIAL_ITEM_MS,
            "intervals": [0] * (SERIAL_LENGTH - 1),
            "total_exposure_ms": SERIAL_LENGTH * SERIAL_ITEM_MS,
            "chunks": chunks,
        },
        {
            "trial_number": 5,
            "part": "chunking",
            "condition": "grouped",
            "label": "Letters shown in groups",
            "length": SERIAL_LENGTH,
            "sequence": chunk_sequence,
            "presentation_units": chunks,
            "unit_display_ms": SERIAL_CHUNK_MS,
            "intervals": [0] * (len(chunks) - 1),
            "total_exposure_ms": len(chunks) * SERIAL_CHUNK_MS,
            "chunks": chunks,
        },
    ])
    return trials


def build_free_recall_conditions(words: list[str]) -> list[dict]:
    if len(words) != 60:
        raise ValueError("The final protocol requires exactly 60 free-recall words.")
    conditions = [
        {"name": "working_memory", "label": "Memory game", "display_ms": FREE_RECALL_NORMAL_MS, "post_task": "card_game"},
        {"name": "pause", "label": "Pause", "display_ms": FREE_RECALL_NORMAL_MS, "post_task": "pause"},
        {"name": "fast", "label": "Fast presentation", "display_ms": FREE_RECALL_FAST_MS, "post_task": "none"},
        {"name": "baseline", "label": "Baseline", "display_ms": FREE_RECALL_NORMAL_MS, "post_task": "none"},
    ]
    for index, condition in enumerate(conditions):
        condition["words"] = words[index * 15 : (index + 1) * 15]
        condition["trial_number"] = index + 6
    return conditions