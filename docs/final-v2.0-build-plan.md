# Final Protocol v2.0 Build Plan

**Target protocol:** `final-v2.0-draft`  
**Prepared:** 16 September 2026  
**Status:** Ready for implementation

This plan implements [final-v2.0-draft.md](final-v2.0-draft.md) without
changing historical `pilot-v1.0`, timing-test, or `final-v1.0-draft` behavior.

## 1. Implementation Principles

- Keep FastAPI, vanilla Vite, Supabase, and the existing scoring modules.
- Add versioned v2 protocol and API paths instead of rewriting v1 behavior.
- Let the backend generate stimuli, calculate adaptive length, score responses,
  and determine session completion.
- Treat client-provided stimuli and trial metadata as untrusted: validate them
  against server-owned session state before saving scores.
- Keep raw responses immutable. Derived scores and local spelling-review output
  remain reproducible and versioned.

## 2. Backend Protocol

Create `backend/app/protocols/final_v2.py` with:

- all approved timing and trial constants;
- four free-recall conditions numbered 1–4;
- serial baseline generators for lengths 6, 7, 8, and 9;
- Danish-letter sampling without replacement within each sequence;
- three-word chunk generation from approved chunk candidates;
- the adaptive-length formula as one tested pure function;
- secondary-task generation using new sequences at the adaptive length.

The adaptive trials cannot be finalized at session start because their length
depends on trials 5–8. Generate trials 1–8 initially, then generate trials 9–11
after all four baseline scores have been saved.

## 3. API and Persistence

Add v2-specific endpoints for:

1. starting a session and returning trials 1–8 plus settings;
2. scoring free-recall trials;
3. scoring serial-baseline trials;
4. obtaining adaptive trials after trial 8;
5. scoring secondary-task and chunking trials;
6. retrieving aggregate final totals after trial 11;
7. retrieving resumable session state after refresh.

Use the existing `sessions` and `trials` tables. Define stable JSON contracts:

- `timing`: intended durations, observed timestamps, timeout status;
- `task_data`: submissions, card events, taps, suppression confirmation,
  adaptive derivation, matched baseline trial, and completion reason;
- `score`: exact scoring fields returned by the scoring modules.

Make trial writes idempotent with an upsert or explicit duplicate response on
the existing `(session_id, trial_number)` unique key. A retry must return the
stored result rather than create a second trial or fail ambiguously.

Store the active session identifier and current screen checkpoint locally in
the browser. On reload, ask the backend which trials are saved and resume at a
safe boundary. A presentation interrupted before response submission is
restarted and marked with interruption metadata; completed trials are never
repeated.

## 4. Frontend Flow

Refactor the current single-file state flow only as far as needed to keep the
11-trial progression understandable. The participant flow is:

1. name and consent;
2. free-recall introduction and trials 1–4;
3. two-minute break with a visible continue-early option;
4. serial-baseline introduction and trials 5–8;
5. adaptive calculation and trials 9–10;
6. chunking trial 11;
7. aggregate totals and completion.

Retain participant-controlled rest screens between trials, the stop control,
development-only skip controls, timed auto-submission, and no correctness
feedback before completion.

The card game remains on its solved state until 15 seconds expire. Finger taps
use the space bar, prevent page scrolling, and save timestamps without a pace
cue. Suppression receives a participant self-confirmation after recall.

Final results show:

- free recall: recalled presented words out of 60;
- serial recall: correct-position letters out of the participant-specific
  total number of serial letters presented.

## 5. Scoring and Local Spelling Review

Keep exact normalized matching as the authoritative online free-recall score.
Keep positional accuracy as the primary serial score and retain the existing
secondary serial measures and overlapping error categories.

Add a separate local pre-analysis script that:

- reads exported raw free-recall responses;
- suggests Danish spelling matches only against words presented in that trial;
- records suggestion, distance or confidence, reviewer decision, and tool
  version in a separate output;
- never modifies the source export or silently changes the online score;
- supports condition-blinded manual review where practical.

## 6. Analysis

Create a v2 analysis path that filters only `final-v2.0-draft` or its frozen
successor and rejects mixed-version data. It must validate:

- exactly 11 unique completed trials with the required condition order;
- baseline lengths 6, 7, 8, and 9;
- recomputed adaptive length against stored derivation;
- matched baseline links for trials 9–11;
- non-repeating serial letters;
- three approved chunk words and a matching flattened sequence;
- required timing, compliance, tapping, timeout, and interruption metadata.

Report free-recall serial-position effects, adaptive secondary-task contrasts,
the chunking versus baseline-9 contrast, error summaries, and data-quality
flags. Keep exclusions configurable and report results both before and after
any chosen exclusions.

## 7. Test Strategy

Add focused tests in this order:

1. protocol generation and adaptive formula unit tests;
2. scoring tests for variable lengths and Danish letters;
3. API tests for the complete 11-trial flow;
4. idempotent retry and interrupted-session recovery tests;
5. analysis validation and spelling-review tests;
6. desktop and mobile browser checks for timing, tapping, break skipping,
   card-game completion, and final totals.

Adaptive tests must cover zero performance, clamp boundaries, half-up rounding,
mixed performance, and perfect performance producing length 9.

## 8. Build Order

1. Add and test the v2 protocol module and adaptive calculation.
2. Add versioned persistence helpers and v2 API endpoints.
3. Add the 11-trial frontend state flow and recovery checkpoints.
4. Add aggregate final results.
5. Add the v2 analysis and local spelling-review pipelines.
6. Run automated tests, production frontend build, and browser validation.
7. Inspect one desktop and one mobile session in Supabase.
8. Freeze the identifier as `final-v2.0` only after all checks pass.

## 9. Definition of Done

The rebuild is ready for data collection when:

- v1 and timing-test tests still pass;
- all v2 automated tests pass;
- a production frontend build succeeds;
- desktop and mobile participants can complete or safely resume the flow;
- retries cannot create duplicate trial rows;
- all 11 rows and adaptive metadata pass the v2 quality checks;
- spelling review preserves immutable source data;
- the deployed commit identifiers are recorded in protocol history.