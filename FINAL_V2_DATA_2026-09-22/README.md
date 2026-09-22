# Final v2.1 Supabase snapshot

This directory contains an anonymized snapshot of all Supabase records for
protocol `final-v2.1-draft`, exported on 2026-09-22. It is intended for sharing
within the project group and for later analysis. No statistical comparison is
prescribed here; analysis choices should follow the research question.

## Files

- `supabase_export_anonymized.json`: canonical data export. It preserves the
  Supabase `sessions` and `trials` table structure, including nested JSON fields.
- `quality_assessment.json`: separate session-level eligibility and validation
  flags. It does not alter observations in the canonical export.
- `export_manifest.json`: snapshot provenance, protocol version, and row counts.

The identifiable source snapshot and the mapping between participant names and
anonymous IDs are stored locally under `exports/`, which is excluded by
`.gitignore`. They must not be committed or shared through GitHub.

## Snapshot summary

At export time the database contained:

| Category | Count |
|---|---:|
| Sessions in `final-v2.1-draft` | 24 |
| Trial rows | 176 |
| Completed sessions | 14 |
| Started but incomplete sessions | 10 |
| Completed known test sessions | 1 |
| Completed real participants | 13 |
| Real participants usable in every section | 10 |

Usable real-participant counts by section:

| Section | Count |
|---|---:|
| Free recall, trials 1–4 | 11 |
| Serial baseline, trials 5–8 | 13 |
| Articulatory suppression, trial 9 | 12 |
| Finger tapping, trial 10 | 11 |
| Grouped/chunking, trial 11 | 13 |

Counts differ by section because quality decisions are applied at the narrowest
appropriate level. A participant is not removed from every analysis merely
because one task is unusable.

## Anonymization

The export retains every Supabase column. Direct identifiers were replaced:

- `sessions.participant_code` is replaced by `P001`, `P002`, and so on.
- `sessions.id` and `trials.id` are replaced with deterministic UUIDs.
- `trials.session_id` is replaced with the corresponding anonymized session UUID.

This preserves the primary-key/foreign-key relationship between both tables.
Absolute timestamps are retained because they are part of the table format and
can be useful for diagnosing duration and deployment cohorts. Do not attempt to
re-identify participants from timestamps or response content.

Participant IDs are assigned chronologically across all sessions, including
incomplete and test sessions. Gaps are therefore expected after filtering.

## Canonical JSON structure

The top-level shape matches the existing analysis loader:

```json
{
  "sessions": [],
  "trials": []
}
```

### `sessions` fields

| Field | Meaning |
|---|---|
| `id` | Anonymized session UUID; primary key. |
| `participant_code` | Anonymous participant ID such as `P006`. |
| `protocol_version` | Protocol identifier; always `final-v2.1-draft` here. |
| `random_seed` | Seed used to reproduce that participant's stimuli. |
| `consent_given` | Whether consent was recorded. |
| `status` | `started` or `completed`. |
| `started_at` | Session creation timestamp in UTC. |
| `completed_at` | Completion timestamp, or `null` for incomplete sessions. |

### `trials` fields

| Field | Meaning |
|---|---|
| `id` | Anonymized trial UUID; primary key. |
| `session_id` | Anonymized foreign key to `sessions.id`. |
| `experiment_type` | `free_recall` or `serial_recall`. |
| `experiment_part` | Broad protocol section. |
| `condition` | Internal condition identifier. This was not shown to participants. |
| `trial_number` | Trial number from 1 through 11. |
| `presented_sequence` | Presented words or letters; JSON array or string by task. |
| `raw_response` | Participant response as submitted. |
| `normalized_response` | Normalized response used for scoring. |
| `score` | Nested task-specific scoring metrics. |
| `timing` | Nested presentation and task timing configuration. |
| `task_data` | Nested response timing, recovery, tapping, compliance, and chunk data. |
| `completed` | Whether the trial response was finalized. |
| `created_at` | Trial-row creation timestamp in UTC. |

## Trial map

| Trial | Type | Condition |
|---:|---|---|
| 1 | Free recall | Baseline, 15 words at 2 seconds each |
| 2 | Free recall | Fast presentation, 15 words at 1 second each |
| 3 | Free recall | 15-second post-list pause |
| 4 | Free recall | 15-second card-game interference task |
| 5 | Serial recall | Baseline, 6 letters |
| 6 | Serial recall | Baseline, 7 letters |
| 7 | Serial recall | Baseline, 8 letters |
| 8 | Serial recall | Baseline, 9 letters |
| 9 | Serial recall | Articulatory suppression at adaptive length |
| 10 | Serial recall | Finger tapping at adaptive length |
| 11 | Serial recall | Three meaningful three-letter chunks |

The adaptive length for trials 9 and 10 is derived from positional accuracy in
trials 5–8, scaled to nine letters, rounded down, and bounded to 6–9 letters.

## Scoring fields

Free recall is case-insensitive and punctuation around words is ignored.
Duplicate recalled words count once. Important fields under `score` include
`recalled_count`, `total_words`, `accuracy`, `recalled_words`, `intrusions`, and
the `primacy`, `middle`, and `recency` groups under `position_groups`.

Serial recall primarily uses position-wise accuracy. Important fields include
`positional_matches`, `presented_length`, `positional_accuracy`,
`whole_sequence_correct`, `omissions`, `intrusions`, `substitutions`,
`repetitions`, and `transpositions`.

## Quality assessment

Join `quality_assessment.json` to `sessions` using its anonymized `session_id`.
The `usable` object contains independent booleans for:

- `complete_session`
- `free_recall`
- `serial_baseline`
- `articulatory_suppression`
- `finger_tapping`
- `chunking`
- `all_sections`

Use the flag matching the data subset being analyzed. Do not treat an unusable
section as a score of zero.

Known completed-session exceptions in this snapshot:

- `P007`: free recall is unusable because all four responses were lost by the
  historical pending-input bug. Articulatory suppression is unusable because
  the participant reported not performing it. Finger tapping is unusable because
  no taps were recorded. Serial baselines and chunking remain usable.
- `P009`: free recall is unusable because all four responses were lost by the
  historical pending-input bug. All serial-recall sections remain usable.
- `P021`: finger tapping is unusable because no tapping evidence was recorded.
  The other sections remain usable.

The pending-input bug occurred when a participant typed words into the free-
recall field but did not press **Add** before finishing or timing out. The text
remaining in the input field was not submitted. The application was fixed on
2026-09-18 to include pending input automatically. Lost responses cannot be
reconstructed because neither `raw_response` nor `task_data.submissions`
contains them.

Known test sessions and incomplete sessions are retained in the canonical
snapshot for completeness but have all analysis eligibility flags set to false.

## Loading the data

Python example:

```python
import json
from pathlib import Path

directory = Path("FINAL_V2_DATA_2026-09-22")
data = json.loads((directory / "supabase_export_anonymized.json").read_text(encoding="utf-8"))
quality = json.loads((directory / "quality_assessment.json").read_text(encoding="utf-8"))

sessions = data["sessions"]
trials = data["trials"]
quality_by_session = {row["session_id"]: row for row in quality["sessions"]}
```

Before using a trial subset, filter to completed non-test sessions and apply the
corresponding `usable` flag. Preserve the canonical JSON file unchanged and
perform transformations in code or in new derived files.

## Repeating the export

From the repository root, with Supabase credentials in the local `.env` file:

```powershell
python analysis/export_final_v2_supabase.py --snapshot-date YYYY-MM-DD
```

This creates an ignored identifiable snapshot under `exports/` and a shareable
anonymized snapshot in a `FINAL_V2_DATA_YYYY-MM-DD/` folder at the repository
root. Review the generated quality report
and privacy checks before committing a future snapshot.

## Context for another AI assistant

When assisting with this dataset:

1. Treat `supabase_export_anonymized.json` as immutable source data.
2. Preserve the distinction between sessions and trials and join on `session_id`.
3. Restrict work to `protocol_version == "final-v2.1-draft"`.
4. Use `quality_assessment.json` to select eligible records per task section.
5. Never interpret the historical empty free-recall records as genuine zero recall.
6. Never include known test or incomplete sessions in participant summaries.
7. Recalculate saved scores with the repository scoring functions when checking integrity.
8. Keep methodological choices explicit rather than silently changing exclusions.