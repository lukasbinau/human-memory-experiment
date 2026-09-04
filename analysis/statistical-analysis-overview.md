# Statistical Analysis Overview

## Purpose

This document specifies the analysis pipeline for the Human Memory Mini Project. It is written for two uses:

1. Explain exactly what the group will calculate and why.
2. Serve as the implementation contract for the scripts in this directory.

The pipeline must work with both a Supabase export and the local synthetic export. Synthetic data is only for testing code and figures; it must never be described as participant results.

## Inputs

Supabase returns two tables. The local test file [synthetic_supabase_export.json](synthetic_supabase_export.json) mirrors this structure as:

```json
{
  "sessions": ["..."],
  "trials": ["..."]
}
```

### `sessions`

The analysis uses `id`, `participant_code`, `protocol_version`, `status`, `started_at`, and `completed_at`.

- `id` identifies a participant session and joins to `trials.session_id`.
- Only `status == "completed"` sessions are included in primary analyses.
- `participant_code` is personal data in real data. It must not appear in figures, report tables, or exported sharing files. The pipeline will replace it with a neutral participant ID such as `P01`.
- Any session whose code begins `SYNTHETIC_TEST_`, or whose protocol version contains `synthetic`, is excluded from real-data outputs by default.

### `trials`

The analysis uses `session_id`, `experiment_type`, `experiment_part`, `condition`, `trial_number`, `presented_sequence`, `raw_response`, `normalized_response`, `score`, `timing`, `task_data`, `completed`, and `created_at`.

The expected trial mapping is:

| Trial numbers | Experiment | Condition(s) |
|---|---|---|
| 1-4 | Free recall | baseline, fast, pause, working_memory |
| 5-10 | Serial recall: capacity | capacity, one length each from 4 to 9 |
| 11-12 | Serial recall: chunking | ungrouped, grouped |
| 13-15 | Serial recall: secondary task | control, articulatory_suppression, finger_tapping |

## Analysis Principles

- Preserve raw data. Never overwrite `raw_response` or the source export.
- Recalculate all derived measures from `presented_sequence` and `raw_response` using the backend scoring functions. Compare recalculated values with saved `score` values and flag disagreements.
- Use positional accuracy as the primary serial-recall outcome. Whole-sequence correctness is a useful secondary outcome, but it becomes close to zero at long lengths and can hide partial recall.
- Use a participant as the unit of resampling for confidence intervals. Trials from the same participant are related and should not be treated as independent people.
- Report effect estimates and $95\%$ confidence intervals. Do not rely only on whether a p-value crosses an arbitrary threshold.
- Make the direction of every contrast explicit. Positive values should consistently mean better recall in the first named condition or position group.

## Step 1: Load And Validate

The loader will accept either a JSON export from Supabase or the local synthetic export and produce `sessions` and `trials` tables in memory.

Before calculating results, validate the following:

1. All included trials have a `session_id` present in `sessions`.
2. Each completed session has exactly one completed trial for each trial number from 1 through 15.
3. Trials 1-4 are free recall and contain exactly 15 presented words.
4. Capacity trials 5-10 contain exactly one sequence each of lengths 4, 5, 6, 7, 8, and 9.
5. Trials 11 and 12 have the same 9-digit `presented_sequence` within a participant.
6. Trials 13-15 each have an 8-digit sequence and the expected secondary-task condition.
7. All expected fields exist in the saved `score` object.
8. The recalculated score agrees with the saved score. Any discrepancy is written to a data-quality report, rather than silently ignored.

A failed structural check stops the primary analysis. A score mismatch is reported and investigated before deciding whether to use the saved score or the recalculated score.

## Step 2: Create Tidy Analysis Tables

The raw Supabase rows are convenient for storage, but not for statistical calculations. The pipeline will create the following derived CSV files in an ignored/generated output directory.

### Free-recall item table

One row per presented word, so there are 15 rows per free-recall trial. Fields include:

`participant_id`, `trial_number`, `condition`, `word`, `serial_position`, `position_group`, and `recalled`.

`position_group` is calculated from `serial_position`:

| Positions | Group |
|---|---|
| 1-5 | primacy |
| 6-10 | middle |
| 11-15 | recency |

`recalled` is 1 when the normalized presented word appears in the normalized participant response, otherwise 0. Duplicate responses receive credit only once, matching the backend scorer.

### Free-recall trial table

One row per free-recall trial. It contains overall accuracy and the three group accuracies:

$$A_g = \frac{\text{number recalled in group } g}{5}$$

where $g$ is primacy, middle, or recency.

### Serial-recall trial table

One row per serial-recall trial. It contains:

- `sequence_length`
- `positional_accuracy`
- `whole_sequence_correct`
- `positional_matches`
- `omissions`, `intrusions`, `substitutions`, `repetitions`, and `transpositions`

The error categories may overlap. For example, a wrong digit can be both a substitution and a transposition. They must therefore be shown as separate descriptive measures and never summed as if they partition all errors.

## Step 3: Free-Recall Effects

All free-recall effects use the within-trial position-group accuracies rather than only total number of words recalled.

### Primacy And Recency

For each condition $c$, calculate:

$$\mathrm{PrimacyEffect}_c = A_{\mathrm{primacy},c} - A_{\mathrm{middle},c}$$

$$\mathrm{RecencyEffect}_c = A_{\mathrm{recency},c} - A_{\mathrm{middle},c}$$

Positive estimates mean the early or late positions were recalled better than the middle positions. Report the group mean and a $95\%$ confidence interval for each condition.

### Faster Presentation

The primary question is whether faster presentation weakens primacy. For each participant:

$$\Delta_{\mathrm{fast,primacy}} = \mathrm{PrimacyEffect}_{\mathrm{fast}} - \mathrm{PrimacyEffect}_{\mathrm{baseline}}$$

A negative value supports the predicted reduction in primacy. Also report the overall accuracy difference, $A_{\mathrm{overall,fast}} - A_{\mathrm{overall,baseline}}$, as a descriptive check that the fast condition was harder.

### Pause And Working-Memory Interference

For each participant, calculate:

$$\Delta_{\mathrm{pause,recency}} = \mathrm{RecencyEffect}_{\mathrm{pause}} - \mathrm{RecencyEffect}_{\mathrm{baseline}}$$

$$\Delta_{\mathrm{WM,recency}} = \mathrm{RecencyEffect}_{\mathrm{working\ memory}} - \mathrm{RecencyEffect}_{\mathrm{baseline}}$$

$$\Delta_{\mathrm{WM-pause,recency}} = \mathrm{RecencyEffect}_{\mathrm{working\ memory}} - \mathrm{RecencyEffect}_{\mathrm{pause}}$$

The expected direction is a modestly negative pause effect and a more negative working-memory effect. Because the pilot uses a fixed condition order, these comparisons can also reflect fatigue, practice, and carry-over effects; this limitation belongs in the report.

## Step 4: Serial-Recall Effects

### Capacity Curve

For each sequence length $L$ from 4 to 9, calculate mean positional accuracy:

$$\bar{A}_L = \frac{1}{N_L}\sum_{i=1}^{N_L} A_{i,L}$$

Plot $\bar{A}_L$ against $L$ with $95\%$ confidence intervals. The expected pattern is a declining curve. Also calculate the proportion of whole sequences correctly recalled at each length, but present it as a secondary plot or table because it is a much stricter outcome.

### Error Types

For capacity trials only, report the mean count per trial for each saved error category, optionally separated by short lengths (4-6) and long lengths (7-9). A stacked chart is only appropriate if it is clearly labelled as overlapping counts; otherwise use a grouped bar chart.

The purpose is descriptive: identify whether errors at longer lengths are mostly omissions, substitutions, transpositions, or repetitions. Do not claim the five categories sum to the total number of wrong positions.

### Chunking

The two chunking trials use the same sequence within a participant. This permits a paired effect estimate:

$$\Delta_{\mathrm{chunking}} = A_{\mathrm{grouped}} - A_{\mathrm{ungrouped}}$$

Positive values support chunking. Report each participant's paired points plus the mean difference and its $95\%$ confidence interval. As a data-quality check, confirm that the paired sequences are identical before calculating this contrast.

### Secondary Tasks

All secondary-task trials have length 8. Calculate the paired contrasts:

$$\Delta_{\mathrm{suppression}} = A_{\mathrm{articulatory\ suppression}} - A_{\mathrm{control}}$$

$$\Delta_{\mathrm{tapping}} = A_{\mathrm{finger\ tapping}} - A_{\mathrm{control}}$$

The expected result is $\Delta_{\mathrm{suppression}} < 0$ and $\Delta_{\mathrm{tapping}} \approx 0$. The phrase "$\approx 0$" means the estimate should be small and its confidence interval should be compatible with no meaningful decrement; it does not prove that tapping has exactly no effect.

`task_data.tap_count` is an exploratory compliance indicator. Summarize its distribution for the finger-tapping trial, but do not remove trials solely because of low tapping counts without a pre-specified exclusion rule.

## Step 5: Confidence Intervals

The primary confidence interval method will be a non-parametric participant bootstrap.

1. Draw $N$ participants with replacement, where $N$ is the number of completed included sessions.
2. Include all of each sampled participant's relevant trials, preserving paired conditions.
3. Recalculate the group-level statistic.
4. Repeat 10,000 times using a fixed random seed.
5. Use the 2.5th and 97.5th percentiles as the $95\%$ confidence interval.

For a paired contrast, calculate each participant's difference first and bootstrap those participant-level differences. This preserves the within-participant design.

With very few participants, the interval will be wide and unstable. That is an honest result and should be reported. The course permits pooled analysis as a simplification, but participant-level bootstrap intervals are preferred because they show participant variability rather than creating false precision from many correlated trials.

## Figures And Report Layout

The final report is limited to five pages including figures. Use four figures with clear captions:

1. Free-recall serial-position curves: recall probability by positions 1-15, one line per condition.
2. Free-recall effect estimates: primacy-minus-middle and recency-minus-middle by condition, with confidence intervals.
3. Serial capacity curve: positional accuracy by length 4-9, with confidence intervals; optionally add whole-sequence accuracy as a lighter secondary series.
4. Serial manipulation and errors: paired chunking and secondary-task contrasts with confidence intervals, plus a compact error-type panel.

Each figure must show the number of completed participants. Use descriptive captions that state the outcome, comparison direction, and confidence-interval method.

## Required Output Files

The future scripts should write these generated files under `analysis/output/`:

- `data_quality_report.csv`: validation results and score mismatches.
- `free_recall_items.csv`: item-level recall table.
- `free_recall_trials.csv`: trial-level group accuracies and effects.
- `serial_recall_trials.csv`: serial outcomes and error categories.
- `effect_estimates.csv`: every reported estimate, sample size, confidence interval, and expected direction.
- `figures/*.png`: publication-ready figures.
- `analysis_summary.md`: short automatically generated results summary for drafting the report.

These generated outputs should be reproducible from the input export and should not be manually edited.

## Implementation Order

1. Add dependencies and a configuration file for input/output paths, random seed, and synthetic-data inclusion.
2. Implement JSON/Supabase loading and session filtering.
3. Implement structural validation and score recalculation checks.
4. Build and save the three tidy tables.
5. Implement bootstrap helper functions and effect-estimate table.
6. Create the four figures.
7. Run the entire pipeline on synthetic data and assert expected qualitative results: positive baseline primacy/recency, negative fast-primacy contrast, negative working-memory recency contrast, declining capacity curve, positive chunking contrast, negative suppression contrast, and near-zero tapping contrast.
8. Run the unchanged pipeline on the real Supabase export, inspect the data-quality report, and write the report from the resulting figures and estimates.

## Interpretation And Limitations

The pilot uses one trial per condition and fixed block order. It can demonstrate that saving, scoring, and plotting work, but it is not well powered to establish reliable psychological effects. Differences may reflect fatigue, practice, list difficulty, strategy differences, or carry-over effects in addition to the intended manipulation.

For the main study, repeat each condition enough times to estimate within-person averages, use counterbalanced block order, retain the same analysis definitions, and update this document before collecting data. Do not alter definitions after inspecting outcomes without recording the change and explaining why.