# Protocol Versions

Experiment data must always be analysed within one protocol version. Trial numbers and conditions are not comparable across versions without an explicit conversion.

| Version | Status | Description |
|---|---|---|
| `pilot-v1.0` | Historical | Original 15-trial study with digit serial recall, six capacity lengths, two timing-based chunking trials, and three secondary-task trials. |
| `timing-test-v1` | Historical prototype | Eight presentation speeds followed by subjective ratings. Never used as main-study data. |
| `timing-test-v2` | Active utility | Reusable menu of ten free-recall timing pairs. Sessions remain incomplete for main-study filtering. |
| `final-v1.0-draft` | Superseded draft | Nine-trial configuration with fixed 15-letter serial trials. Not frozen for data collection. |
| `final-v1.0` | Never frozen | Reserved identifier that was not used for a frozen protocol. |
| `final-v2.0-draft` | Superseded draft | Implemented 11-trial configuration using half-up adaptive rounding and trial-boundary recovery. |
| `final-v2.1-draft` | Active draft | Uses floor rounding, Danish participant copy, and phase-aware refresh recovery with attempt metadata. |
| `final-v2.0` | Not yet frozen | Reserved for data collection after implementation and validation of the revised design. |

## Change Log

### `final-v2.1-draft`

- Changed adaptive-length rounding from half-up to floor before clamping to 6–9.
- Added server-authoritative active attempts and phase-aware refresh recovery.
- Regenerate stimuli after refresh during presentation; preserve stimuli and restart the answer period after refresh on the response screen.
- Save `attempt_number` and `refresh_count` in trial metadata.
- Changed all participant-facing text to Danish and removed technical letter-case wording.

### `final-v2.0-draft` — 15 September 2026

- Restored four serial-baseline lengths in ascending order: 6, 7, 8, and 9 letters.
- Made articulatory-suppression and finger-tapping lengths adaptive to each participant's baseline.
- Defined adaptive length as mean positional accuracy across the four baselines, scaled to nine letters, rounded half upward, and clamped to 6–9.
- Changed chunking to three meaningful three-letter words and comparison with the nine-letter baseline.
- Set serial letters and chunk words to 2000 ms with 500 ms inter-unit blanks.
- Restored free recall as the first experiment part in baseline, fast, pause, and working-memory order.
- Defined an 11-trial session: four free recall, four serial baseline, and three subsequent serial trials.
- Changed the primary serial outcome from ordered-subsequence accuracy to positional accuracy.
- Finalized participant flow and operational decisions in [final-v2.0-draft.md](final-v2.0-draft.md).
- Prepared the version-preserving rebuild in [final-v2.0-build-plan.md](final-v2.0-build-plan.md).

### `final-v1.0-draft` — 11 September 2026

- Reduced the main experiment from 15 to 9 trials.
- Replaced serial digits and variable lengths with 15-letter sequences.
- Added consonant-only suppression, tapping, and control trials.
- Added paired ungrouped/grouped trials using the same five recognizable three-letter Danish words.
- Equalized chunking exposure at 15 seconds per condition.
- Reordered the study to place serial secondary-task trials first.
- Retained the card-matching working-memory task.
- Centralized adjustable free-recall timing constants.
- Added letter-compatible scoring while preserving legacy digit scoring.
- Added a separate final-protocol analysis pipeline.

## Historical v1 Freeze Checklist

This checklist was not completed before the design was superseded:

- [x] Record the selected normal, fast, and pause timings.
- [x] Obtain group approval for every chunk candidate used in data collection.
- Complete desktop and mobile pilot sessions.
- Verify all nine database rows and the final analysis data-quality report.
- Record the deployed Git and Hugging Face commit identifiers.

## v2 Freeze Checklist

Before freezing the active v2 draft:

- Resolve and approve the open decisions in [final-v2.0-draft.md](final-v2.0-draft.md).
- Implement the revised protocol without changing historical protocol behavior.
- Complete desktop and mobile pilot sessions.
- Verify all 11 database rows, adaptive-length metadata, and baseline links.
- Pass the revised analysis data-quality checks.
- Record the deployed Git and Hugging Face commit identifiers.