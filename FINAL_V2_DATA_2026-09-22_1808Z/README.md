# Final v2.1 Supabase snapshot

This folder is the latest anonymized export of all Supabase records for protocol
`final-v2.1-draft`. It was exported at **2026-09-22 18:08 UTC** and is intended
for sharing within the project group and for later analysis.

## Files

- `supabase_export_anonymized.json`: canonical data export preserving the native
  Supabase `sessions` and `trials` records, including nested JSON fields.
- `quality_assessment.json`: session-level validation and section-specific
  usability flags. It does not alter the canonical observations.
- `export_manifest.json`: source, protocol version, timestamp, and row counts.
- `README.md`: this schema and quality handoff.

The identifiable export and private participant mapping remain under the local,
Git-ignored `exports/` directory. They are not present on GitHub.

## Current snapshot

| Category | Count |
|---|---:|
| Sessions in `final-v2.1-draft` | 28 |
| Trial rows | 220 |
| Completed sessions | 18 |
| Started but incomplete sessions | 10 |
| Completed known test sessions | 1 |
| Completed real participants | 17 |
| Real participants usable in every section | 14 |

Since the preceding `FINAL_V2_DATA_2026-09-22` snapshot, four sessions and 44
trial rows were added. All four new sessions are completed real-participant
sessions and passed every section-level quality check.

Usable real-participant counts by section:

| Section | Count |
|---|---:|
| Free recall, trials 1–4 | 15 |
| Serial baseline, trials 5–8 | 17 |
| Articulatory suppression, trial 9 | 16 |
| Finger tapping, trial 10 | 15 |
| Grouped/chunking, trial 11 | 17 |

Apply quality decisions at the section level. A participant is not removed from
all analyses merely because one task is unusable.

## Anonymization

The export retains every Supabase column, while direct identifiers are replaced:

- `sessions.participant_code` becomes `P001`, `P002`, and so on.
- `sessions.id` and `trials.id` become deterministic anonymous UUIDs.
- `trials.session_id` points to the corresponding anonymous session UUID.

This preserves primary-key and foreign-key relationships. Participant IDs are
assigned chronologically across all sessions, including incomplete and test
sessions, so gaps are expected after filtering.

## Canonical structure

```json
{
  "sessions": [],
  "trials": []
}
```

### `sessions`

| Field | Meaning |
|---|---|
| `id` | Anonymous session UUID and primary key. |
| `participant_code` | Anonymous participant ID. |
| `protocol_version` | Protocol identifier. |
| `random_seed` | Seed used to reproduce presented stimuli. |
| `consent_given` | Whether consent was recorded. |
| `status` | `started` or `completed`. |
| `started_at` | Session creation timestamp in UTC. |
| `completed_at` | Completion timestamp or `null`. |

### `trials`

| Field | Meaning |
|---|---|
| `id` | Anonymous trial UUID and primary key. |
| `session_id` | Foreign key to `sessions.id`. |
| `experiment_type` | `free_recall` or `serial_recall`. |
| `experiment_part` | Broad protocol section. |
| `condition` | Internal condition identifier. |
| `trial_number` | Trial number from 1 through 11. |
| `presented_sequence` | Presented words or letters. |
| `raw_response` | Response as submitted. |
| `normalized_response` | Normalized scoring input. |
| `score` | Nested task-specific scoring metrics. |
| `timing` | Nested presentation and task timing settings. |
| `task_data` | Response timing, recovery, tapping, compliance, and chunk data. |
| `completed` | Whether the trial was finalized. |
| `created_at` | Trial-row creation timestamp in UTC. |

## Trial map

| Trial | Type | Condition |
|---:|---|---|
| 1 | Free recall | Baseline: 15 words at 2 seconds each |
| 2 | Free recall | Fast: 15 words at 1 second each |
| 3 | Free recall | 15-second post-list pause |
| 4 | Free recall | 15-second card-game interference task |
| 5–8 | Serial recall | Baselines of 6, 7, 8, and 9 letters |
| 9 | Serial recall | Articulatory suppression at adaptive length |
| 10 | Serial recall | Finger tapping at adaptive length |
| 11 | Serial recall | Three meaningful three-letter chunks |

The adaptive length for trials 9 and 10 is derived from trials 5–8, scaled to
nine letters, rounded down, and bounded to 6–9 letters.

## Scoring

Free recall is case-insensitive and ignores surrounding punctuation. Duplicate
words count once. Important `score` fields include `recalled_count`,
`total_words`, `accuracy`, `recalled_words`, `intrusions`, and the
`position_groups` breakdown.

Serial recall primarily uses position-wise accuracy. Important fields include
`positional_matches`, `presented_length`, `positional_accuracy`,
`whole_sequence_correct`, and the error counts.

## Quality flags

Join `quality_assessment.json` to `sessions` using anonymous `session_id`. Its
`usable` object contains independent flags for `complete_session`, `free_recall`,
`serial_baseline`, `articulatory_suppression`, `finger_tapping`, `chunking`, and
`all_sections`. Use the flag corresponding to the subset being analyzed. Do not
treat an unusable section as a score of zero.

Existing completed-session exceptions:

- `P007`: free recall is unusable due to the historical pending-input bug;
  suppression was reported as not performed; no tapping evidence was recorded.
  Serial baselines and chunking remain usable.
- `P009`: free recall is unusable due to the historical pending-input bug. All
  serial-recall sections remain usable.
- `P021`: finger tapping is unusable because no tapping evidence was recorded.
  Other sections remain usable.

The historical free-recall bug occurred when text remained in the input field
without the participant pressing **Add**. Before the 2026-09-18 fix, that pending
text was not submitted on finish or timeout. Those lost words cannot be recovered
from `raw_response` or `task_data.submissions`.

Known test sessions and incomplete sessions are retained in the canonical export
for completeness but have analysis eligibility flags set to false.

## Loading the snapshot

```python
import json
from pathlib import Path

directory = Path("FINAL_V2_DATA_2026-09-22_1808Z")
data = json.loads((directory / "supabase_export_anonymized.json").read_text(encoding="utf-8"))
quality = json.loads((directory / "quality_assessment.json").read_text(encoding="utf-8"))

sessions = data["sessions"]
trials = data["trials"]
quality_by_session = {row["session_id"]: row for row in quality["sessions"]}
```

Keep the canonical JSON unchanged. Perform filtering and reshaping in code or in
new derived files.

## Guidance for another AI assistant

1. Treat `supabase_export_anonymized.json` as immutable source data.
2. Preserve the sessions/trials distinction and join on `session_id`.
3. Restrict work to `protocol_version == "final-v2.1-draft"`.
4. Use the matching section-level flag from `quality_assessment.json`.
5. Never interpret historical empty free-recall records as genuine zero recall.
6. Exclude known test and incomplete sessions from participant summaries.
7. Recalculate scores with repository scoring functions when checking integrity.
8. Keep methodological and exclusion decisions explicit.