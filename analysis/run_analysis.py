"""Validate and analyse Human Memory Experiment exports.

Run synthetic test data with:
    python analysis/run_analysis.py --include-synthetic

For real data, export the Supabase sessions and trials tables as one JSON object
with `sessions` and `trials` arrays, then pass its path with `--input`.
"""

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

from backend.app.scoring.free_recall import score_response as score_free_recall
from backend.app.scoring.free_recall import normalize_word
from backend.app.scoring.serial_recall import score_response as score_serial_recall


DEFAULT_INPUT = Path(__file__).with_name("synthetic_supabase_export.json")
BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_SEED = 20260904
FREE_CONDITIONS = ["baseline", "fast", "pause", "working_memory"]
ERROR_COLUMNS = ["omissions", "intrusions", "substitutions", "repetitions", "transpositions"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyse Human Memory Experiment data exports.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="JSON export with sessions and trials arrays.")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"), help="Directory for generated CSVs, figures, and summary.")
    parser.add_argument("--include-synthetic", action="store_true", help="Include SYNTHETIC_TEST sessions. Required for the local test export.")
    return parser.parse_args()


def load_export(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    with path.open(encoding="utf-8") as source:
        export = json.load(source)
    if set(export) != {"sessions", "trials"}:
        raise ValueError("Input JSON must contain exactly 'sessions' and 'trials' arrays.")
    return pd.DataFrame(export["sessions"]), pd.DataFrame(export["trials"])


def is_synthetic(session: pd.Series) -> pd.Series:
    codes = session["participant_code"].fillna("").str.startswith("SYNTHETIC_TEST_")
    versions = session["protocol_version"].fillna("").str.contains("synthetic", case=False)
    return codes | versions


def filter_sessions(sessions: pd.DataFrame, trials: pd.DataFrame, include_synthetic: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    included = sessions.loc[sessions["status"].eq("completed")].copy()
    if not include_synthetic:
        included = included.loc[~is_synthetic(included)].copy()
    included = included.sort_values("started_at").reset_index(drop=True)
    included["participant_id"] = [f"P{index:02d}" for index in range(1, len(included) + 1)]
    included_trials = trials.loc[trials["session_id"].isin(included["id"])].copy()
    return included, included_trials


def report_row(session_id: str | None, check: str, passed: bool, detail: str) -> dict:
    return {"session_id": session_id or "", "check": check, "passed": passed, "detail": detail}


def validate_data(sessions: pd.DataFrame, trials: pd.DataFrame) -> pd.DataFrame:
    reports = []
    session_ids = set(sessions["id"])
    orphan_count = int((~trials["session_id"].isin(session_ids)).sum())
    reports.append(report_row(None, "foreign_keys", orphan_count == 0, f"{orphan_count} trials reference an unknown included session."))

    expected_free_keys = {"recalled_count", "total_words", "accuracy", "recalled_words", "intrusions", "position_groups"}
    expected_serial_keys = {"presented_length", "response_length", "positional_matches", "positional_accuracy", "whole_sequence_correct", *ERROR_COLUMNS}
    expected_conditions = {1: "baseline", 2: "fast", 3: "pause", 4: "working_memory", 11: "ungrouped", 12: "grouped", 13: "control", 14: "articulatory_suppression", 15: "finger_tapping"}

    for session_id, group in trials.groupby("session_id"):
        by_number = group.set_index("trial_number", drop=False)
        numbers = sorted(group["trial_number"].tolist())
        reports.append(report_row(session_id, "trial_numbers", numbers == list(range(1, 16)), f"Found trial numbers {numbers}."))
        for number, condition in expected_conditions.items():
            actual = by_number.loc[number, "condition"] if number in by_number.index else None
            reports.append(report_row(session_id, f"condition_{number}", actual == condition, f"Expected {condition}; found {actual}."))
        if set(range(1, 16)).issubset(by_number.index):
            free_lengths = [len(by_number.loc[number, "presented_sequence"]) for number in range(1, 5)]
            reports.append(report_row(session_id, "free_recall_lengths", free_lengths == [15] * 4, f"Found word-list lengths {free_lengths}."))
            capacity_lengths = sorted(len(by_number.loc[number, "presented_sequence"]) for number in range(5, 11))
            reports.append(report_row(session_id, "capacity_lengths", capacity_lengths == list(range(4, 10)), f"Found sorted lengths {capacity_lengths}."))
            same_chunk_sequence = by_number.loc[11, "presented_sequence"] == by_number.loc[12, "presented_sequence"]
            reports.append(report_row(session_id, "chunking_sequence_pair", same_chunk_sequence, "Trials 11 and 12 must share a sequence."))
            secondary_lengths = [len(by_number.loc[number, "presented_sequence"]) for number in range(13, 16)]
            reports.append(report_row(session_id, "secondary_lengths", secondary_lengths == [8, 8, 8], f"Found lengths {secondary_lengths}."))

        for _, trial in group.iterrows():
            score = trial["score"]
            expected_keys = expected_free_keys if trial["experiment_type"] == "free_recall" else expected_serial_keys
            reports.append(report_row(session_id, f"score_shape_trial_{trial['trial_number']}", set(score or {}) == expected_keys, "Saved score keys must match the backend scorer."))
            recalculated = score_free_recall(trial["presented_sequence"], trial["raw_response"] or "") if trial["experiment_type"] == "free_recall" else score_serial_recall(trial["presented_sequence"], trial["raw_response"] or "")
            reports.append(report_row(session_id, f"score_match_trial_{trial['trial_number']}", score == recalculated, "Saved and recalculated scores must agree."))
    return pd.DataFrame(reports)


def position_group(position: int) -> str:
    return "primacy" if position <= 5 else "middle" if position <= 10 else "recency"


def build_free_recall_tables(sessions: pd.DataFrame, trials: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    participants = sessions.set_index("id")["participant_id"].to_dict()
    item_rows = []
    trial_rows = []
    for _, trial in trials.loc[trials["experiment_type"].eq("free_recall")].iterrows():
        sequence = trial["presented_sequence"]
        response_words = {normalize_word(word) for word in (trial["raw_response"] or "").replace(",", " ").replace(";", " ").split()}
        recalled = [normalize_word(word) in response_words for word in sequence]
        group_accuracy = {}
        for group_name, start, end in [("primacy", 0, 5), ("middle", 5, 10), ("recency", 10, 15)]:
            group_accuracy[group_name] = float(np.mean(recalled[start:end]))
        for index, (word, was_recalled) in enumerate(zip(sequence, recalled), start=1):
            item_rows.append({"participant_id": participants[trial["session_id"]], "session_id": trial["session_id"], "trial_number": trial["trial_number"], "condition": trial["condition"], "word": word, "serial_position": index, "position_group": position_group(index), "recalled": int(was_recalled)})
        trial_rows.append({"participant_id": participants[trial["session_id"]], "session_id": trial["session_id"], "trial_number": trial["trial_number"], "condition": trial["condition"], "overall_accuracy": float(np.mean(recalled)), "primacy_accuracy": group_accuracy["primacy"], "middle_accuracy": group_accuracy["middle"], "recency_accuracy": group_accuracy["recency"], "primacy_effect": group_accuracy["primacy"] - group_accuracy["middle"], "recency_effect": group_accuracy["recency"] - group_accuracy["middle"]})
    return pd.DataFrame(item_rows), pd.DataFrame(trial_rows)


def build_serial_table(sessions: pd.DataFrame, trials: pd.DataFrame) -> pd.DataFrame:
    participants = sessions.set_index("id")["participant_id"].to_dict()
    rows = []
    for _, trial in trials.loc[trials["experiment_type"].eq("serial_recall")].iterrows():
        score = trial["score"]
        rows.append({"participant_id": participants[trial["session_id"]], "session_id": trial["session_id"], "trial_number": trial["trial_number"], "experiment_part": trial["experiment_part"], "condition": trial["condition"], "sequence_length": len(trial["presented_sequence"]), "positional_accuracy": score["positional_accuracy"], "whole_sequence_correct": int(score["whole_sequence_correct"]), **{column: score[column] for column in ERROR_COLUMNS}, "tap_count": trial["task_data"].get("tap_count", 0)})
    return pd.DataFrame(rows)


def bootstrap_mean(values: pd.Series, rng: np.random.Generator) -> tuple[float, float, float]:
    data = values.dropna().to_numpy(dtype=float)
    if not len(data):
        return np.nan, np.nan, np.nan
    samples = rng.choice(data, size=(BOOTSTRAP_SAMPLES, len(data)), replace=True).mean(axis=1)
    return float(data.mean()), float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def make_estimate(name: str, family: str, values: pd.Series, expected_direction: str, rng: np.random.Generator) -> dict:
    estimate, ci_lower, ci_upper = bootstrap_mean(values, rng)
    return {"effect": name, "family": family, "n_participants": int(values.notna().sum()), "estimate": estimate, "ci_lower": ci_lower, "ci_upper": ci_upper, "expected_direction": expected_direction}


def effect_estimates(free_trials: pd.DataFrame, serial_trials: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    estimates = []
    for condition in FREE_CONDITIONS:
        subset = free_trials.loc[free_trials["condition"].eq(condition)]
        estimates.append(make_estimate(f"primacy_minus_middle_{condition}", "free_recall", subset["primacy_effect"], "positive", rng))
        estimates.append(make_estimate(f"recency_minus_middle_{condition}", "free_recall", subset["recency_effect"], "positive", rng))
    free_wide = free_trials.pivot(index="participant_id", columns="condition")
    estimates.extend([
        make_estimate("fast_minus_baseline_primacy_effect", "free_recall", free_wide["primacy_effect"]["fast"] - free_wide["primacy_effect"]["baseline"], "negative", rng),
        make_estimate("fast_minus_baseline_overall_accuracy", "free_recall", free_wide["overall_accuracy"]["fast"] - free_wide["overall_accuracy"]["baseline"], "negative", rng),
        make_estimate("pause_minus_baseline_recency_effect", "free_recall", free_wide["recency_effect"]["pause"] - free_wide["recency_effect"]["baseline"], "negative", rng),
        make_estimate("working_memory_minus_baseline_recency_effect", "free_recall", free_wide["recency_effect"]["working_memory"] - free_wide["recency_effect"]["baseline"], "negative", rng),
        make_estimate("working_memory_minus_pause_recency_effect", "free_recall", free_wide["recency_effect"]["working_memory"] - free_wide["recency_effect"]["pause"], "negative", rng),
    ])
    capacity = serial_trials.loc[serial_trials["experiment_part"].eq("capacity_and_errors")]
    for length, subset in capacity.groupby("sequence_length"):
        estimates.append(make_estimate(f"capacity_positional_accuracy_length_{length}", "serial_capacity", subset["positional_accuracy"], "decreasing with length", rng))
        estimates.append(make_estimate(f"capacity_whole_sequence_accuracy_length_{length}", "serial_capacity", subset["whole_sequence_correct"], "decreasing with length", rng))
    manipulation_conditions = ["ungrouped", "grouped", "control", "articulatory_suppression", "finger_tapping"]
    manipulation_trials = serial_trials.loc[serial_trials["condition"].isin(manipulation_conditions)]
    serial_wide = manipulation_trials.pivot(index="participant_id", columns="condition", values="positional_accuracy")
    estimates.extend([
        make_estimate("grouped_minus_ungrouped_positional_accuracy", "serial_manipulation", serial_wide["grouped"] - serial_wide["ungrouped"], "positive", rng),
        make_estimate("articulatory_suppression_minus_control_positional_accuracy", "serial_manipulation", serial_wide["articulatory_suppression"] - serial_wide["control"], "negative", rng),
        make_estimate("finger_tapping_minus_control_positional_accuracy", "serial_manipulation", serial_wide["finger_tapping"] - serial_wide["control"], "approximately zero", rng),
    ])
    return pd.DataFrame(estimates)


def style_axes(axis: plt.Axes) -> None:
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color="#d9ddd7", linewidth=0.8)
    axis.set_axisbelow(True)


def plot_free_serial_positions(items: pd.DataFrame, figures: Path, n_participants: int) -> None:
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    colors = {"baseline": "#1f6f78", "fast": "#c05621", "pause": "#5b7c45", "working_memory": "#8b3a62"}
    for condition in FREE_CONDITIONS:
        values = items.loc[items["condition"].eq(condition)].groupby("serial_position")["recalled"].mean()
        axis.plot(values.index, values.values, marker="o", label=condition.replace("_", " "), color=colors[condition])
    axis.set(xlabel="Word position", ylabel="Recall probability", xticks=range(1, 16), ylim=(0, 1.05), title=f"Free recall by serial position (N = {n_participants})")
    axis.legend(frameon=False, ncol=2)
    style_axes(axis)
    figure.tight_layout()
    figure.savefig(figures / "01_free_recall_serial_positions.png", dpi=220)
    plt.close(figure)


def plot_free_effects(estimates: pd.DataFrame, figures: Path, n_participants: int) -> None:
    selected = estimates.loc[estimates["effect"].str.startswith(("primacy_minus_middle", "recency_minus_middle"))].copy()
    labels = [name.replace("primacy_minus_middle_", "Primacy: ").replace("recency_minus_middle_", "Recency: ").replace("working_memory", "memory game") for name in selected["effect"]]
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    positions = np.arange(len(selected))
    errors = np.vstack((selected["estimate"] - selected["ci_lower"], selected["ci_upper"] - selected["estimate"]))
    axis.errorbar(selected["estimate"], positions, xerr=errors, fmt="o", color="#1f6f78", capsize=3)
    axis.axvline(0, color="#555555", linewidth=1)
    axis.set(yticks=positions, yticklabels=labels, xlabel="Recall probability difference from middle", title=f"Primacy and recency effects with 95% bootstrap CIs (N = {n_participants})")
    axis.invert_yaxis()
    style_axes(axis)
    figure.tight_layout()
    figure.savefig(figures / "02_free_recall_effects.png", dpi=220)
    plt.close(figure)


def plot_capacity(serial_trials: pd.DataFrame, estimates: pd.DataFrame, figures: Path, n_participants: int) -> None:
    capacity = estimates.loc[estimates["effect"].str.startswith("capacity_positional_accuracy")].copy()
    capacity["length"] = capacity["effect"].str.extract(r"_(\d+)$").astype(int)
    whole = estimates.loc[estimates["effect"].str.startswith("capacity_whole_sequence_accuracy")].copy()
    whole["length"] = whole["effect"].str.extract(r"_(\d+)$").astype(int)
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    for data, label, color in [(capacity, "Positional accuracy", "#1f6f78"), (whole, "Whole sequence correct", "#c05621")]:
        data = data.sort_values("length")
        axis.errorbar(data["length"], data["estimate"], yerr=[data["estimate"] - data["ci_lower"], data["ci_upper"] - data["estimate"]], marker="o", capsize=3, label=label, color=color)
    axis.set(xlabel="Sequence length", ylabel="Accuracy", xticks=range(4, 10), ylim=(0, 1.05), title=f"Serial-recall capacity curve (N = {n_participants})")
    axis.legend(frameon=False)
    style_axes(axis)
    figure.tight_layout()
    figure.savefig(figures / "03_serial_capacity.png", dpi=220)
    plt.close(figure)


def plot_serial_effects_and_errors(serial_trials: pd.DataFrame, estimates: pd.DataFrame, figures: Path, n_participants: int) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(10.4, 4.8), gridspec_kw={"width_ratios": [1, 1.15]})
    selected_names = ["grouped_minus_ungrouped_positional_accuracy", "articulatory_suppression_minus_control_positional_accuracy", "finger_tapping_minus_control_positional_accuracy"]
    selected = estimates.set_index("effect").loc[selected_names].reset_index()
    labels = ["Grouped - ungrouped", "Suppression - control", "Tapping - control"]
    errors = np.vstack((selected["estimate"] - selected["ci_lower"], selected["ci_upper"] - selected["estimate"]))
    axes[0].errorbar(selected["estimate"], np.arange(3), xerr=errors, fmt="o", capsize=3, color="#8b3a62")
    axes[0].axvline(0, color="#555555", linewidth=1)
    axes[0].set(yticks=np.arange(3), yticklabels=labels, xlabel="Positional-accuracy difference", title="Paired serial-recall effects")
    axes[0].invert_yaxis()
    style_axes(axes[0])
    errors_by_length = serial_trials.loc[serial_trials["experiment_part"].eq("capacity_and_errors")].assign(length_group=lambda data: np.where(data["sequence_length"] <= 6, "Short (4-6)", "Long (7-9)"))
    error_means = errors_by_length.groupby("length_group", observed=True)[ERROR_COLUMNS].mean().T
    error_means.plot.bar(ax=axes[1], color=["#5b7c45", "#c05621"], width=0.75)
    axes[1].set(xlabel="Overlapping error category", ylabel="Mean count per trial", title="Capacity-trial error profile")
    axes[1].tick_params(axis="x", rotation=35)
    axes[1].legend(title="Sequence length", frameon=False)
    style_axes(axes[1])
    figure.suptitle(f"Serial-recall manipulations and errors (N = {n_participants})", y=1.02)
    figure.tight_layout()
    figure.savefig(figures / "04_serial_effects_and_errors.png", dpi=220, bbox_inches="tight")
    plt.close(figure)


def write_summary(path: Path, sessions: pd.DataFrame, estimates: pd.DataFrame) -> None:
    lookup = estimates.set_index("effect")
    def result(name: str) -> str:
        row = lookup.loc[name]
        return f"{row['estimate']:.3f} [{row['ci_lower']:.3f}, {row['ci_upper']:.3f}]"
    capacity = estimates.loc[estimates["effect"].str.startswith("capacity_positional_accuracy")].copy()
    capacity["length"] = capacity["effect"].str.extract(r"_(\d+)$").astype(int)
    capacity = capacity.sort_values("length")
    path.write_text(
        "# Analysis Summary\n\n"
        f"Completed included sessions: {len(sessions)}. All confidence intervals are 95% participant-bootstrap intervals with {BOOTSTRAP_SAMPLES:,} resamples.\n\n"
        "## Free Recall\n\n"
        f"Baseline primacy-minus-middle: {result('primacy_minus_middle_baseline')}.\n\n"
        f"Baseline recency-minus-middle: {result('recency_minus_middle_baseline')}.\n\n"
        f"Fast minus baseline primacy effect: {result('fast_minus_baseline_primacy_effect')}.\n\n"
        f"Working-memory minus baseline recency effect: {result('working_memory_minus_baseline_recency_effect')}.\n\n"
        "## Serial Recall\n\n"
        f"Positional accuracy was {capacity.iloc[0]['estimate']:.3f} at length {capacity.iloc[0]['length']} and {capacity.iloc[-1]['estimate']:.3f} at length {capacity.iloc[-1]['length']}.\n\n"
        f"Grouped minus ungrouped accuracy: {result('grouped_minus_ungrouped_positional_accuracy')}.\n\n"
        f"Articulatory suppression minus control: {result('articulatory_suppression_minus_control_positional_accuracy')}.\n\n"
        f"Finger tapping minus control: {result('finger_tapping_minus_control_positional_accuracy')}.\n\n"
        "These values are descriptive. The pilot's fixed condition order and limited repetitions restrict causal conclusions.\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    sessions, trials = load_export(args.input)
    sessions, trials = filter_sessions(sessions, trials, args.include_synthetic)
    if sessions.empty:
        raise ValueError("No completed sessions remain. Use --include-synthetic for the synthetic test export.")
    args.output.mkdir(parents=True, exist_ok=True)
    figures = args.output / "figures"
    figures.mkdir(exist_ok=True)
    for old_figure in figures.glob("*.png"):
        old_figure.unlink()
    quality = validate_data(sessions, trials)
    quality.to_csv(args.output / "data_quality_report.csv", index=False)
    if not quality["passed"].all():
        failed = quality.loc[~quality["passed"]]
        raise ValueError(f"Data validation failed ({len(failed)} checks). See {args.output / 'data_quality_report.csv'}.")
    free_items, free_trials = build_free_recall_tables(sessions, trials)
    serial_trials = build_serial_table(sessions, trials)
    estimates = effect_estimates(free_trials, serial_trials)
    free_items.to_csv(args.output / "free_recall_items.csv", index=False)
    free_trials.to_csv(args.output / "free_recall_trials.csv", index=False)
    serial_trials.to_csv(args.output / "serial_recall_trials.csv", index=False)
    estimates.to_csv(args.output / "effect_estimates.csv", index=False)
    plot_free_serial_positions(free_items, figures, len(sessions))
    plot_free_effects(estimates, figures, len(sessions))
    plot_capacity(serial_trials, estimates, figures, len(sessions))
    plot_serial_effects_and_errors(serial_trials, estimates, figures, len(sessions))
    write_summary(args.output / "analysis_summary.md", sessions, estimates)
    print(f"Analysis complete: {len(sessions)} sessions, {len(trials)} trials. Outputs: {args.output}")


if __name__ == "__main__":
    main()