"""Validate and summarize final-v2 Human Memory Experiment exports."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.protocols.final_v2 import DRAFT_CHUNKS, PROTOCOL_VERSION, calculate_adaptive_length
from backend.app.scoring.free_recall import score_response as score_free_recall
from backend.app.scoring.serial_recall import score_response as score_serial_recall


EXPECTED_TRIALS = {
    1: ("free_recall", "baseline", 15),
    2: ("free_recall", "fast", 15),
    3: ("free_recall", "pause", 15),
    4: ("free_recall", "working_memory", 15),
    5: ("serial_recall", "baseline_6", 6),
    6: ("serial_recall", "baseline_7", 7),
    7: ("serial_recall", "baseline_8", 8),
    8: ("serial_recall", "baseline_9", 9),
    9: ("serial_recall", "articulatory_suppression", None),
    10: ("serial_recall", "finger_tapping", None),
    11: ("serial_recall", "grouped", 9),
}


def load_export(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    with path.open(encoding="utf-8") as source:
        export = json.load(source)
    if not {"sessions", "trials"}.issubset(export):
        raise ValueError("Input JSON must contain sessions and trials arrays.")
    return pd.DataFrame(export["sessions"]), pd.DataFrame(export["trials"])


def select_sessions(
    sessions: pd.DataFrame,
    trials: pd.DataFrame,
    protocol_version: str = PROTOCOL_VERSION,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    included = sessions.loc[
        sessions["status"].eq("completed") & sessions["protocol_version"].eq(protocol_version)
    ].sort_values("started_at").copy()
    included["participant_id"] = [f"P{index:02d}" for index in range(1, len(included) + 1)]
    return included, trials.loc[trials["session_id"].isin(included["id"])].copy()


def validate_data(sessions: pd.DataFrame, trials: pd.DataFrame) -> pd.DataFrame:
    rows = []
    approved_chunks = {chunk for chunk, _ in DRAFT_CHUNKS}

    def add(session_id: str, check: str, passed: bool, detail: str) -> None:
        rows.append({"session_id": session_id, "check": check, "passed": bool(passed), "detail": detail})

    for session_id in sessions["id"]:
        group = trials.loc[trials["session_id"].eq(session_id)].sort_values("trial_number")
        numbers = group["trial_number"].tolist()
        add(session_id, "trial_numbers", numbers == list(range(1, 12)), f"Found {numbers}.")
        if numbers != list(range(1, 12)):
            continue

        by_number = group.set_index("trial_number", drop=False)
        baseline_matches = {}
        for number, (experiment_type, condition, fixed_length) in EXPECTED_TRIALS.items():
            trial = by_number.loc[number]
            sequence = trial["presented_sequence"]
            length = len(sequence)
            structure_ok = (
                trial["experiment_type"] == experiment_type
                and trial["condition"] == condition
                and (fixed_length is None or length == fixed_length)
            )
            add(session_id, f"trial_{number}", structure_ok, f"Found {trial['experiment_type']}, {trial['condition']}, length {length}.")
            recalculated = (
                score_free_recall(sequence, trial["raw_response"] or "")
                if experiment_type == "free_recall"
                else score_serial_recall("".join(sequence) if isinstance(sequence, list) else sequence, trial["raw_response"] or "")
            )
            saved = trial["score"] or {}
            shared = saved.keys() & recalculated.keys()
            add(session_id, f"score_{number}", bool(shared) and all(saved[key] == recalculated[key] for key in shared), "Saved metrics must match rescoring.")
            if number in range(5, 9):
                baseline_matches[number + 1] = recalculated["positional_matches"]
                add(session_id, f"unique_letters_{number}", len(set(sequence)) == length, "Letters must not repeat within a sequence.")

        derivation = calculate_adaptive_length(baseline_matches)
        adaptive_length = derivation["adaptive_length"]
        add(session_id, "adaptive_lengths", len(by_number.loc[9, "presented_sequence"]) == len(by_number.loc[10, "presented_sequence"]) == adaptive_length, f"Expected {adaptive_length} letters.")
        for number in (9, 10):
            task_data = by_number.loc[number, "task_data"] or {}
            add(session_id, f"matched_baseline_{number}", task_data.get("matched_baseline_trial_number") == adaptive_length - 1, f"Expected trial {adaptive_length - 1}.")

        chunk_sequence = by_number.loc[11, "presented_sequence"]
        chunk_data = by_number.loc[11, "task_data"] or {}
        chunks = chunk_data.get("chunks", [])
        add(session_id, "chunk_words", len(chunks) == 3 and set(chunks).issubset(approved_chunks), f"Found {chunks}.")
        add(session_id, "chunk_flattening", "".join(chunks) == chunk_sequence, "Chunk words must match the presented sequence.")
    return pd.DataFrame(rows)


def build_trial_tables(sessions: pd.DataFrame, trials: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    participant_ids = sessions.set_index("id")["participant_id"].to_dict()
    free_rows = []
    serial_rows = []
    for _, trial in trials.iterrows():
        participant_id = participant_ids[trial["session_id"]]
        if trial["experiment_type"] == "free_recall":
            score = score_free_recall(trial["presented_sequence"], trial["raw_response"] or "")
            free_rows.append({
                "participant_id": participant_id,
                "trial_number": trial["trial_number"],
                "condition": trial["condition"],
                "recalled_count": score["recalled_count"],
                "accuracy": score["accuracy"],
                **{f"{name}_accuracy": values["accuracy"] for name, values in score["position_groups"].items()},
            })
        else:
            sequence = trial["presented_sequence"]
            score = score_serial_recall("".join(sequence) if isinstance(sequence, list) else sequence, trial["raw_response"] or "")
            serial_rows.append({
                "participant_id": participant_id,
                "trial_number": trial["trial_number"],
                "condition": trial["condition"],
                "presented_length": score["presented_length"],
                "positional_matches": score["positional_matches"],
                "positional_accuracy": score["positional_accuracy"],
                "whole_sequence_correct": score["whole_sequence_correct"],
                **{name: score[name] for name in ("omissions", "intrusions", "substitutions", "repetitions", "transpositions")},
            })
    return pd.DataFrame(free_rows), pd.DataFrame(serial_rows)


def build_effects(free_trials: pd.DataFrame, serial_trials: pd.DataFrame) -> pd.DataFrame:
    effects = []
    for participant_id, group in free_trials.groupby("participant_id"):
        by_condition = group.set_index("condition")
        baseline = by_condition.loc["baseline"]
        effects.extend([
            {"participant_id": participant_id, "effect": "fast_minus_baseline", "estimate": by_condition.loc["fast", "accuracy"] - baseline["accuracy"]},
            {"participant_id": participant_id, "effect": "pause_minus_baseline", "estimate": by_condition.loc["pause", "accuracy"] - baseline["accuracy"]},
            {"participant_id": participant_id, "effect": "working_memory_minus_baseline", "estimate": by_condition.loc["working_memory", "accuracy"] - baseline["accuracy"]},
        ])
    for participant_id, group in serial_trials.groupby("participant_id"):
        by_trial = group.set_index("trial_number")
        adaptive_length = int(by_trial.loc[9, "presented_length"])
        matched_baseline = adaptive_length - 1
        effects.extend([
            {"participant_id": participant_id, "effect": "suppression_minus_matched_baseline", "estimate": by_trial.loc[9, "positional_accuracy"] - by_trial.loc[matched_baseline, "positional_accuracy"]},
            {"participant_id": participant_id, "effect": "tapping_minus_matched_baseline", "estimate": by_trial.loc[10, "positional_accuracy"] - by_trial.loc[matched_baseline, "positional_accuracy"]},
            {"participant_id": participant_id, "effect": "chunking_minus_baseline_9", "estimate": by_trial.loc[11, "positional_accuracy"] - by_trial.loc[8, "positional_accuracy"]},
        ])
    return pd.DataFrame(effects)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and analyse final-v2 experiment data.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("final_v2_output"))
    parser.add_argument("--protocol-version", default=PROTOCOL_VERSION)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sessions, trials = load_export(args.input)
    sessions, trials = select_sessions(sessions, trials, args.protocol_version)
    if sessions.empty:
        raise ValueError(f"No completed {args.protocol_version} sessions were found.")
    args.output.mkdir(parents=True, exist_ok=True)
    quality = validate_data(sessions, trials)
    quality.to_csv(args.output / "data_quality_report.csv", index=False)
    if not quality["passed"].all():
        raise ValueError(f"Data validation failed. See {args.output / 'data_quality_report.csv'}.")
    free_trials, serial_trials = build_trial_tables(sessions, trials)
    effects = build_effects(free_trials, serial_trials)
    free_trials.to_csv(args.output / "free_recall_trials.csv", index=False)
    serial_trials.to_csv(args.output / "serial_recall_trials.csv", index=False)
    effects.to_csv(args.output / "participant_effects.csv", index=False)
    print(f"V2 analysis complete: {len(sessions)} sessions and {len(trials)} trials.")


if __name__ == "__main__":
    main()