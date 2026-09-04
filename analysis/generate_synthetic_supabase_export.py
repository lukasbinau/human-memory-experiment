import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid5

from backend.app.scoring.free_recall import score_response as score_free_recall
from backend.app.scoring.serial_recall import score_response as score_serial_recall


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = Path(__file__).with_name("synthetic_supabase_export.json")
NAMESPACE = UUID("4a6a9b8c-e7ad-49f3-85d0-97f8f05dc3d4")
RANDOM_SEED = 20260904
PROFILES = {
    "strong": {
        "free": {
            "baseline": (0.82, 0.48, 0.80),
            "fast": (0.64, 0.41, 0.76),
            "pause": (0.78, 0.45, 0.60),
            "working_memory": (0.62, 0.36, 0.36),
        },
        "serial": {4: 0.98, 5: 0.91, 6: 0.84, 7: 0.73, 8: 0.61, 9: 0.47},
    },
    "typical": {
        "free": {
            "baseline": (0.69, 0.34, 0.68),
            "fast": (0.48, 0.29, 0.61),
            "pause": (0.65, 0.32, 0.48),
            "working_memory": (0.53, 0.27, 0.25),
        },
        "serial": {4: 0.94, 5: 0.82, 6: 0.69, 7: 0.55, 8: 0.40, 9: 0.24},
    },
    "variable": {
        "free": {
            "baseline": (0.63, 0.31, 0.58),
            "fast": (0.42, 0.30, 0.56),
            "pause": (0.59, 0.29, 0.41),
            "working_memory": (0.46, 0.25, 0.24),
        },
        "serial": {4: 0.87, 5: 0.73, 6: 0.58, 7: 0.42, 8: 0.28, 9: 0.15},
    },
    "low_span": {
        "free": {
            "baseline": (0.52, 0.24, 0.49),
            "fast": (0.35, 0.21, 0.45),
            "pause": (0.48, 0.22, 0.34),
            "working_memory": (0.37, 0.19, 0.18),
        },
        "serial": {4: 0.78, 5: 0.60, 6: 0.45, 7: 0.30, 8: 0.19, 9: 0.10},
    },
}


def load_words() -> list[str]:
    with (ROOT / "hukommelseseksperiment_300_ord.csv").open(encoding="utf-8-sig", newline="") as source:
        return [row["ord"].strip() for row in csv.DictReader(source) if row["ord"].strip()]


def timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def choose_words(words: list[str], probabilities: tuple[float, float, float], rng: random.Random) -> list[str]:
    recalled = []
    for position, word in enumerate(words):
        probability = probabilities[position // 5] + rng.uniform(-0.12, 0.12)
        if rng.random() < max(0.05, min(0.95, probability)):
            recalled.append(word)
    return recalled


def make_serial_response(sequence: str, accuracy: float, rng: random.Random) -> str:
    recalled = list(sequence)
    for index, digit in enumerate(recalled):
        if rng.random() > accuracy:
            if index + 1 < len(recalled) and rng.random() < 0.32:
                recalled[index], recalled[index + 1] = recalled[index + 1], recalled[index]
            else:
                alternatives = [candidate for candidate in "0123456789" if candidate != digit]
                recalled[index] = rng.choice(alternatives)
    if len(recalled) > 4 and rng.random() < 0.20:
        recalled.pop(rng.randrange(len(recalled)))
    if rng.random() < 0.05:
        recalled.append(rng.choice("0123456789"))
    return "".join(recalled)


def session_rows(index: int, words: list[str], rng: random.Random) -> tuple[dict, list[dict]]:
    profile_name = list(PROFILES)[index % len(PROFILES)]
    profile = PROFILES[profile_name]
    session_id = str(uuid5(NAMESPACE, f"synthetic-session-{index}"))
    started_at = datetime(2026, 9, 4, 9, 0, tzinfo=timezone.utc) + timedelta(minutes=28 * index)
    completed_at = started_at + timedelta(minutes=19 + rng.randint(0, 8))
    session = {
        "id": session_id,
        "participant_code": f"SYNTHETIC_TEST_{profile_name.upper()}_{index + 1:02d}",
        "protocol_version": "pilot-v1.0-synthetic",
        "random_seed": rng.randrange(0, 2**31),
        "consent_given": True,
        "status": "completed",
        "started_at": timestamp(started_at),
        "completed_at": timestamp(completed_at),
    }
    trials = []
    sampled_words = rng.sample(words, 60)
    free_conditions = [
        ("baseline", 2000, "none"),
        ("fast", 1000, "none"),
        ("pause", 2000, "pause"),
        ("working_memory", 2000, "card_game"),
    ]
    for trial_number, (condition, display_ms, post_task) in enumerate(free_conditions, start=1):
        sequence = sampled_words[(trial_number - 1) * 15 : trial_number * 15]
        recalled = choose_words(sequence, profile["free"][condition], rng)
        if rng.random() < 0.18:
            recalled.append(rng.choice(["hund", "træ", "bog"]))
        raw_response = ", ".join(recalled)
        submissions = [
            {"word": word, "submittedAt": 1800 + position * rng.randint(850, 2600)}
            for position, word in enumerate(recalled)
        ]
        trials.append({
            "id": str(uuid5(NAMESPACE, f"{session_id}-trial-{trial_number}")),
            "session_id": session_id,
            "experiment_type": "free_recall",
            "experiment_part": "free_recall",
            "condition": condition,
            "trial_number": trial_number,
            "presented_sequence": sequence,
            "raw_response": raw_response,
            "normalized_response": raw_response.strip().lower(),
            "score": score_free_recall(sequence, raw_response),
            "timing": {"display_ms": display_ms, "post_task": post_task},
            "task_data": {"submissions": submissions},
            "completed": True,
            "created_at": timestamp(started_at + timedelta(minutes=trial_number)),
        })
    capacity_lengths = list(range(4, 10))
    rng.shuffle(capacity_lengths)
    serial_specs = [(length, "capacity_and_errors", "capacity") for length in capacity_lengths]
    chunk_sequence = "".join(str(rng.randrange(10)) for _ in range(9))
    serial_specs.extend([
        (chunk_sequence, "chunking", "ungrouped"),
        (chunk_sequence, "chunking", "grouped"),
    ])
    serial_specs.extend((8, "secondary_tasks", condition) for condition in ["control", "articulatory_suppression", "finger_tapping"])
    for offset, (sequence_or_length, experiment_part, condition) in enumerate(serial_specs, start=5):
        sequence = sequence_or_length if isinstance(sequence_or_length, str) else "".join(str(rng.randrange(10)) for _ in range(sequence_or_length))
        length = len(sequence)
        accuracy = profile["serial"].get(length, profile["serial"][9])
        if condition == "grouped":
            accuracy = min(0.92, accuracy + 0.22)
        elif condition == "articulatory_suppression":
            accuracy = max(0.05, accuracy - 0.24)
        elif condition == "finger_tapping":
            accuracy = max(0.05, accuracy - 0.03)
        accuracy = max(0.03, min(0.98, accuracy + rng.uniform(-0.10, 0.10)))
        response = make_serial_response(sequence, accuracy, rng)
        trials.append({
            "id": str(uuid5(NAMESPACE, f"{session_id}-trial-{offset}")),
            "session_id": session_id,
            "experiment_type": "serial_recall",
            "experiment_part": experiment_part,
            "condition": condition,
            "trial_number": offset,
            "presented_sequence": sequence,
            "raw_response": response,
            "normalized_response": "".join(digit for digit in response if digit.isdigit()),
            "score": score_serial_recall(sequence, response),
            "timing": {"display_ms": 1000, "interval_ms": 500},
            "task_data": {"tap_count": rng.randint(12, 20) if condition == "finger_tapping" else 0},
            "completed": True,
            "created_at": timestamp(started_at + timedelta(minutes=5 + offset)),
        })
    return session, trials


def main() -> None:
    rng = random.Random(RANDOM_SEED)
    words = load_words()
    sessions = []
    trials = []
    for index in range(24):
        session, session_trials = session_rows(index, words, rng)
        sessions.append(session)
        trials.extend(session_trials)
    OUTPUT_PATH.write_text(
        json.dumps({"sessions": sessions, "trials": trials}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(sessions)} sessions and {len(trials)} trials to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()