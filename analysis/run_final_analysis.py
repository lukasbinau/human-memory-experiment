"""Validate and analyse final-v1 Human Memory Experiment exports."""

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.protocols.final_v1 import PROTOCOL_VERSION
from backend.app.scoring.free_recall import normalize_word
from backend.app.scoring.free_recall import score_response as score_free_recall
from backend.app.scoring.serial_recall import score_response as score_serial_recall


BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_SEED = 20260911
FREE_CONDITIONS = ["working_memory", "pause", "fast", "baseline"]
SERIAL_CONDITIONS = ["articulatory_suppression", "finger_tapping", "control", "ungrouped", "grouped"]
ERROR_COLUMNS = ["omissions", "intrusions", "substitutions", "repetitions", "transpositions"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyse final-v1 experiment data.")
    parser.add_argument("--input", type=Path, required=True, help="JSON export containing sessions and trials arrays.")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("final_output"))
    parser.add_argument("--protocol-version", default=PROTOCOL_VERSION)
    return parser.parse_args()


def load_export(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    with path.open(encoding="utf-8") as source:
        export = json.load(source)
    if not {"sessions", "trials"}.issubset(export):
        raise ValueError("Input JSON must contain sessions and trials arrays.")
    return pd.DataFrame(export["sessions"]), pd.DataFrame(export["trials"])


def select_sessions(sessions: pd.DataFrame, trials: pd.DataFrame, protocol_version: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    included = sessions.loc[
        sessions["status"].eq("completed") & sessions["protocol_version"].eq(protocol_version)
    ].sort_values("started_at").copy()
    included["participant_id"] = [f"P{index:02d}" for index in range(1, len(included) + 1)]
    return included, trials.loc[trials["session_id"].isin(included["id"])].copy()


def validate_data(sessions: pd.DataFrame, trials: pd.DataFrame) -> pd.DataFrame:
    expected = {
        1: ("serial_recall", "articulatory_suppression", 15),
        2: ("serial_recall", "finger_tapping", 15),
        3: ("serial_recall", "control", 15),
        4: ("serial_recall", "ungrouped", 15),
        5: ("serial_recall", "grouped", 15),
        6: ("free_recall", "working_memory", 15),
        7: ("free_recall", "pause", 15),
        8: ("free_recall", "fast", 15),
        9: ("free_recall", "baseline", 15),
    }
    rows = []

    def add(session_id: str, check: str, passed: bool, detail: str) -> None:
        rows.append({"session_id": session_id, "check": check, "passed": passed, "detail": detail})

    for session_id in sessions["id"]:
        group = trials.loc[trials["session_id"].eq(session_id)].sort_values("trial_number")
        trial_numbers = group["trial_number"].tolist()
        valid_trial_numbers = trial_numbers == list(range(1, 10))
        add(session_id, "trial_numbers", valid_trial_numbers, f"Found {trial_numbers}.")
        if not valid_trial_numbers:
            continue
        by_number = group.set_index("trial_number", drop=False)
        for number, (experiment_type, condition, length) in expected.items():
            if number not in by_number.index:
                add(session_id, f"trial_{number}", False, "Trial is missing.")
                continue
            trial = by_number.loc[number]
            sequence = trial["presented_sequence"]
            structure_ok = trial["experiment_type"] == experiment_type and trial["condition"] == condition and len(sequence) == length
            add(session_id, f"trial_{number}", bool(structure_ok), f"Found {trial['experiment_type']}, {trial['condition']}, length {len(sequence)}.")
            recalculated = score_free_recall(sequence, trial["raw_response"] or "") if experiment_type == "free_recall" else score_serial_recall(sequence, trial["raw_response"] or "")
            saved_score = trial["score"] or {}
            shared_metrics = saved_score.keys() & recalculated.keys()
            score_matches = bool(shared_metrics) and all(saved_score[key] == recalculated[key] for key in shared_metrics)
            add(session_id, f"score_{number}", score_matches, "Every saved score metric must equal the current protocol scorer; newly derived metrics are recalculated from the raw response.")
        if {4, 5}.issubset(by_number.index):
            add(session_id, "chunk_sequence_pair", by_number.loc[4, "presented_sequence"] == by_number.loc[5, "presented_sequence"], "Trials 4 and 5 must use identical letters.")
            ungrouped_ms = (by_number.loc[4, "timing"] or {}).get("total_exposure_ms")
            grouped_ms = (by_number.loc[5, "timing"] or {}).get("total_exposure_ms")
            add(session_id, "chunk_exposure_pair", ungrouped_ms == grouped_ms == 15_000, f"Found {ungrouped_ms} ms and {grouped_ms} ms.")
    return pd.DataFrame(rows)


def build_free_tables(sessions: pd.DataFrame, trials: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    participant_ids = sessions.set_index("id")["participant_id"].to_dict()
    items = []
    trial_rows = []
    for _, trial in trials.loc[trials["experiment_type"].eq("free_recall")].iterrows():
        responses = {normalize_word(word) for word in (trial["raw_response"] or "").replace(",", " ").replace(";", " ").split()}
        recalled = [normalize_word(word) in responses for word in trial["presented_sequence"]]
        accuracies = {
            "primacy": float(np.mean(recalled[:5])),
            "middle": float(np.mean(recalled[5:10])),
            "recency": float(np.mean(recalled[10:15])),
        }
        for position, (word, was_recalled) in enumerate(zip(trial["presented_sequence"], recalled), start=1):
            items.append({
                "participant_id": participant_ids[trial["session_id"]], "trial_number": trial["trial_number"],
                "condition": trial["condition"], "word": word, "serial_position": position,
                "position_group": "primacy" if position <= 5 else "middle" if position <= 10 else "recency",
                "recalled": int(was_recalled),
            })
        trial_rows.append({
            "participant_id": participant_ids[trial["session_id"]], "trial_number": trial["trial_number"],
            "condition": trial["condition"], "overall_accuracy": float(np.mean(recalled)),
            **{f"{name}_accuracy": value for name, value in accuracies.items()},
            "primacy_effect": accuracies["primacy"] - accuracies["middle"],
            "recency_effect": accuracies["recency"] - accuracies["middle"],
        })
    return pd.DataFrame(items), pd.DataFrame(trial_rows)


def build_serial_table(sessions: pd.DataFrame, trials: pd.DataFrame) -> pd.DataFrame:
    participant_ids = sessions.set_index("id")["participant_id"].to_dict()
    rows = []
    for _, trial in trials.loc[trials["experiment_type"].eq("serial_recall")].iterrows():
        score = score_serial_recall(trial["presented_sequence"], trial["raw_response"] or "")
        rows.append({
            "participant_id": participant_ids[trial["session_id"]], "trial_number": trial["trial_number"],
            "condition": trial["condition"], "ordered_subsequence_accuracy": score["ordered_subsequence_accuracy"],
            "item_accuracy": score["item_accuracy"], "positional_accuracy": score["positional_accuracy"],
            "whole_sequence_correct": int(score["whole_sequence_correct"]), "tap_count": (trial["task_data"] or {}).get("tap_count", 0),
            **{column: score[column] for column in ERROR_COLUMNS},
        })
    return pd.DataFrame(rows)


def bootstrap(values: pd.Series, rng: np.random.Generator) -> tuple[float, float, float]:
    data = values.dropna().to_numpy(dtype=float)
    samples = rng.choice(data, size=(BOOTSTRAP_SAMPLES, len(data)), replace=True).mean(axis=1)
    return float(data.mean()), float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def build_effects(free_trials: pd.DataFrame, serial_trials: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    values = []

    def add(name: str, family: str, series: pd.Series) -> None:
        estimate, lower, upper = bootstrap(series, rng)
        values.append({"effect": name, "family": family, "n_participants": len(series.dropna()), "estimate": estimate, "ci_lower": lower, "ci_upper": upper})

    for condition in FREE_CONDITIONS:
        subset = free_trials.loc[free_trials["condition"].eq(condition)]
        add(f"primacy_minus_middle_{condition}", "free_recall", subset["primacy_effect"])
        add(f"recency_minus_middle_{condition}", "free_recall", subset["recency_effect"])
    free_wide = free_trials.pivot(index="participant_id", columns="condition")
    add("fast_minus_baseline_overall", "free_recall", free_wide["overall_accuracy"]["fast"] - free_wide["overall_accuracy"]["baseline"])
    add("fast_minus_baseline_primacy", "free_recall", free_wide["primacy_effect"]["fast"] - free_wide["primacy_effect"]["baseline"])
    add("pause_minus_baseline_recency", "free_recall", free_wide["recency_effect"]["pause"] - free_wide["recency_effect"]["baseline"])
    add("working_memory_minus_baseline_recency", "free_recall", free_wide["recency_effect"]["working_memory"] - free_wide["recency_effect"]["baseline"])
    serial_wide = serial_trials.pivot(index="participant_id", columns="condition", values="ordered_subsequence_accuracy")
    add("suppression_minus_control", "serial_recall", serial_wide["articulatory_suppression"] - serial_wide["control"])
    add("tapping_minus_control", "serial_recall", serial_wide["finger_tapping"] - serial_wide["control"])
    add("grouped_minus_ungrouped", "serial_recall", serial_wide["grouped"] - serial_wide["ungrouped"])
    return pd.DataFrame(values)


def plot_results(items: pd.DataFrame, serial_trials: pd.DataFrame, output: Path, participant_count: int) -> None:
    figures = output / "figures"
    figures.mkdir(exist_ok=True)
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    for condition in FREE_CONDITIONS:
        means = items.loc[items["condition"].eq(condition)].groupby("serial_position")["recalled"].mean()
        axis.plot(means.index, means.values, marker="o", label=condition.replace("_", " "))
    axis.set(xlabel="Word position", ylabel="Recall probability", ylim=(0, 1.05), xticks=range(1, 16), title=f"Free recall by serial position (N = {participant_count})")
    axis.legend(frameon=False, ncol=2)
    figure.tight_layout()
    figure.savefig(figures / "01_free_recall_positions.png", dpi=220)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    means = serial_trials.groupby("condition")["ordered_subsequence_accuracy"].mean().reindex(SERIAL_CONDITIONS)
    axis.bar([name.replace("_", " ") for name in means.index], means.values, color="#1f6f78")
    axis.set(ylabel="Mean ordered-subsequence accuracy", ylim=(0, 1.05), title=f"Letter serial recall (N = {participant_count})")
    axis.tick_params(axis="x", rotation=25)
    figure.tight_layout()
    figure.savefig(figures / "02_serial_recall_conditions.png", dpi=220)
    plt.close(figure)


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
    free_items, free_trials = build_free_tables(sessions, trials)
    serial_trials = build_serial_table(sessions, trials)
    effects = build_effects(free_trials, serial_trials)
    free_items.to_csv(args.output / "free_recall_items.csv", index=False)
    free_trials.to_csv(args.output / "free_recall_trials.csv", index=False)
    serial_trials.to_csv(args.output / "serial_recall_trials.csv", index=False)
    effects.to_csv(args.output / "effect_estimates.csv", index=False)
    plot_results(free_items, serial_trials, args.output, len(sessions))
    (args.output / "analysis_summary.md").write_text(
        f"# Final Protocol Analysis\n\nProtocol: `{args.protocol_version}`  \nCompleted participants: {len(sessions)}  \n"
        f"Trials: {len(trials)}\n\nEffect estimates and 95% participant-bootstrap intervals are in `effect_estimates.csv`.\n",
        encoding="utf-8",
    )
    print(f"Final analysis complete: {len(sessions)} sessions and {len(trials)} trials.")


if __name__ == "__main__":
    main()