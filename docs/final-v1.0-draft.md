# Final Protocol v1.0 Draft

**Protocol identifier:** `final-v1.0-draft`
**Implemented:** 11 September 2026
**Status:** Superseded draft; still implemented in the app

This document remains the contract for the currently implemented app. The
group's replacement 11-trial design is documented in
[final-v2.0-draft.md](final-v2.0-draft.md) and is not yet implemented.

## Fixed Trial Order

| Trial | Experiment | Condition | Stimulus |
|---:|---|---|---|
| 1 | Serial recall | Articulatory suppression | 15 unique consonants |
| 2 | Serial recall | Finger tapping | 15 unique consonants |
| 3 | Serial recall | Control | 15 unique consonants |
| 4 | Chunking | Ungrouped | 15 letters shown individually |
| 5 | Chunking | Grouped | The same letters shown as five meaningful three-letter units |
| 6 | Free recall | Card matching | 15 words followed by the memory-card task |
| 7 | Free recall | Pause | 15 words followed by an unfilled pause |
| 8 | Free recall | Fast | 15 words at the fast rate |
| 9 | Free recall | Baseline | 15 words at the normal rate |

The order is intentionally fixed and places demanding serial conditions first. Practice, fatigue, and condition are therefore confounded and must be reported as a limitation.

## Approved Timing Constants

The source of truth is [backend/app/protocols/final_v1.py](../backend/app/protocols/final_v1.py).

| Setting | Approved value |
|---|---:|
| Normal free-recall word display | 2000 ms |
| Fast free-recall word display | 1000 ms |
| Pause condition | 15 s |
| Card-matching task | 15 s |
| Free-recall response | 90 s |
| Individual serial letter | 1000 ms |
| Grouped three-letter unit | 3000 ms |
| Serial-recall response | 30 s |

The group approved the 2000 ms normal rate, 1000 ms fast rate, and 15-second pause on 14 September 2026. Fast remains exactly half of normal.

## Serial Stimuli

Non-chunked sequences are permutations of `BDFGHJKLMNPRSTV`. Every trial therefore contains 15 unique consonants and uses the same item pool in a different order.

Chunk candidates are stored in [backend/app/data/final_v1_chunks.csv](../backend/app/data/final_v1_chunks.csv). On 14 September 2026, the group approved all thirteen candidates that passed technical review and occur in the approved 300-word Danish noun list. The remaining candidates stay excluded. The protocol loader requires both technical review and group approval.

Trials 4 and 5 use an identical flattened sequence. Trial 4 presents 15 individual letters for one second each. Trial 5 presents five three-letter units for three seconds each. Both provide exactly 15 seconds of visible exposure with no additional blank interval.

## Scoring and Storage

Participants enter only the letters they remember, in the order they believe the letters appeared. They may enter fewer than 15 letters and are instructed not to guess. Responses are uppercased and stripped of spaces and punctuation before scoring.

Ordered-subsequence accuracy is the primary serial-recall measure. It is the length of the longest recalled subsequence that preserves presentation order, divided by 15, so later remembered letters are not discarded after an omission. Item accuracy, strict positional accuracy, whole-sequence correctness, and exploratory error counts remain secondary measures. Raw responses, presentation units, exact timing, chunk identities, tapping count, and all derived scores are saved in Supabase. Free recall retains exact normalized word matching.

The session is marked `completed` only after trial 9. Existing `pilot-v1.0` and timing-test records retain their original protocol identifiers.

## Analysis

Run the final pipeline with:

```text
python analysis/run_final_analysis.py --input exports/final_export.json
```

It rejects sessions that do not contain the exact nine-trial structure, re-scores every response, verifies the paired chunk sequence and exposure time, and reports free-recall and serial-recall contrasts with participant-bootstrap confidence intervals.