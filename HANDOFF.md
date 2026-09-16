# Handoff Document — Human Memory Experiment App

> **Historical document:** This handoff describes `pilot-v1.0` as it existed on 4 September 2026. The current implementation is `final-v1.0-draft`; see [docs/final-v1.0-draft.md](docs/final-v1.0-draft.md) and [docs/protocol-versions.md](docs/protocol-versions.md).

**Date written:** 4 September 2026
**Course:** 02464 Artificial Intelligence and Human Cognition (DTU)
**Group:** s255728, s255213, s256191, s254943

This document is for the agent/person taking over three jobs:

1. **Clean up the code** (readability, structure, small fixes)
2. **Explain the code to the group members** (most have limited coding experience)
3. **Do the statistics and data analysis** on the collected pilot data

Read this fully before touching anything. It explains what exists, why it was built this way, what's already been fixed, and what's still open.

---

## 1. What this project is

A web app that runs the group's **Human Memory Mini Project** pilot experiment: a free-recall task (remembering words) followed by a serial-recall task (remembering digit sequences), covering all the conditions specified in [experiment-design.md](experiment-design.md) — **read that file first**, it is the authoritative experiment protocol (stimuli, timings, conditions, scoring rules). This handoff document only covers the *app*, not the experiment design itself.

**Live deployment:** https://huggingface.co/spaces/lukasbinau/human-memory-experiment
**Local dev:** frontend at `http://127.0.0.1:5173`, backend at `http://127.0.0.1:8000`

## 2. Current status

The app is functionally complete and has been tested (automated + manual) on both desktop and mobile. It:

- Collects the participant's real name (not anonymous — see §6.3)
- Runs 4 free-recall conditions (baseline, fast, pause, working-memory/card-game) — 15 words each
- Runs 11 serial-recall trials (6 capacity, 2 chunking, 3 secondary-task) — see §6.2 for the exact trial-number mapping
- Scores everything server-side in Python and saves raw + scored data to Supabase
- Has a working Stop button, progress indicators, and (in dev mode only) a Skip button for fast manual testing

Known issues that were found and fixed this session (for context, don't re-fix these):
- Chunking trials previously had identical timing for grouped/ungrouped (now uses a real 250/250/1250ms vs 500ms rhythm — see `generate_intervals()` in `backend/app/main.py`)
- Mobile keyboard was pushing recall screens off-screen (fixed via `100dvh` + mobile-only top-alignment)
- Serial-recall trials were showing participants their accuracy score after every trial, which the experiment design explicitly forbids (mid-experiment feedback could bias later trials) — now shows only a plain "saved" message, same as free recall
- A form-width bug caused recall word-chips to render partially off-screen (left edge at x=-17px)
- A duplicate/leaking timer bug in the 2-minute break screen (fixed by using the shared `timer` variable instead of a local one)
- Desktop layout regression from the mobile fix (screens went top-aligned instead of centered on desktop) — fixed by scoping the top-alignment to `max-width: 600px` only

Known **not-yet-fixed, low-priority cosmetic items** (optional):
- The memory-card game grid looks small/disproportionate on large desktop screens (sized mobile-first, never given a larger desktop variant)
- On the serial-recall digit-entry screen, the narrow centered input sits above a full-width `space-between` footer, causing slight visual misalignment

## 3. Tech stack and architecture

```
Participant's browser
      │  HTTP (fetch)
      ▼
Vite frontend (vanilla JS, no framework)  →  served as static files by FastAPI in production
      │  /api/... (JSON)
      ▼
Python FastAPI backend  (backend/app/main.py)
      │  generates stimuli, scores responses, talks to Supabase
      ▼
Supabase (PostgreSQL)  →  tables: sessions, trials
```

- **No frontend framework** — the entire UI is one file, `frontend/src/main.js`, that does `document.querySelector('#app').innerHTML = '<section>...</section>'` for every screen and wires up event listeners after each render. This was a deliberate simplicity choice for a beginner-friendly group project, not an oversight.
- **No frontend build tooling beyond Vite** — no React/Vue, no state management library, no TypeScript.
- **Styling** is one file, `frontend/src/styles.css`, plain CSS (no Sass/Tailwind).
- **Backend** is one FastAPI app (`backend/app/main.py`) plus two small pure-function scoring modules (`backend/app/scoring/free_recall.py`, `backend/app/scoring/serial_recall.py`) and one database module (`backend/app/database/supabase_client.py`).
- **Deployment**: Hugging Face Space, Docker SDK. The `Dockerfile` builds the Vite frontend in a `node` stage, then copies the built `dist/` into a `python:3.12-slim` stage that runs `uvicorn`. FastAPI serves the built frontend directly via `StaticFiles` (see the bottom of `main.py`) — this is why the frontend's `apiUrl` in production resolves to an empty string (same-origin `/api/...` calls), see `frontend/src/main.js` line ~4.

## 4. Repository structure

```
├── experiment-design.md          ← the experiment protocol (READ THIS FIRST)
├── HANDOFF.md                    ← this file
├── hukommelseseksperiment_300_ord.csv   ← approved 300-word Danish stimulus pool
├── index.html                    ← Vite entry point
├── Dockerfile                    ← Hugging Face deployment build
├── frontend/src/
│   ├── main.js                   ← ALL app/UI logic (single file, ~500 lines)
│   └── styles.css                ← ALL styling (single file)
├── backend/app/
│   ├── main.py                   ← FastAPI app, all API routes, trial/stimulus generation
│   ├── scoring/
│   │   ├── free_recall.py        ← word-recall scoring (pure function, easy to unit test)
│   │   └── serial_recall.py      ← digit-recall scoring (pure function, easy to unit test)
│   └── database/
│       └── supabase_client.py    ← the only file that talks to Supabase
├── supabase/schema.sql           ← database schema (source of truth for table structure)
├── analysis/                     ← EMPTY except a placeholder README — this is your workspace
└── .env                          ← local secrets (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) — never commit this
```

## 5. Running it locally

```powershell
# Terminal 1 — backend (from the Python environment that has the packages installed)
python -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. In dev mode (`npm run dev`), every screen shows a small "Skip" button (top-right) that jumps straight to the next screen — useful for fast manual testing. It does not appear in the production build.

## 6. For the data-analysis job

### 6.1 Database access

Supabase project. Credentials are in the local `.env` file (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`). **This key has been exposed in chat/screenshots multiple times during development — rotate it in the Supabase dashboard (Project Settings → API) before doing serious analysis work, and definitely before this key is used anywhere near real participant data collection.** Use the `supabase` Python package (already a backend dependency) or just query via the Supabase dashboard's SQL editor / Table Editor.

Two tables, defined in `supabase/schema.sql`:

**`sessions`**: `id`, `participant_code` (see §6.3 — this holds the participant's real name), `protocol_version`, `random_seed`, `consent_given`, `status` (`started` / `completed`), `started_at`, `completed_at`.

**`trials`**: `id`, `session_id`, `experiment_type` (`free_recall` / `serial_recall`), `experiment_part`, `condition`, `trial_number`, `presented_sequence` (jsonb), `raw_response`, `normalized_response`, `score` (jsonb — see §6.4/6.5 for exact shape), `timing` (jsonb), `task_data` (jsonb), `completed`, `created_at`. Unique constraint on `(session_id, trial_number)`.

### 6.2 Trial-number → condition map (important, not obvious from the data alone)

| trial_number | experiment_type | experiment_part | condition |
|---|---|---|---|
| 1 | free_recall | free_recall | baseline |
| 2 | free_recall | free_recall | fast |
| 3 | free_recall | free_recall | pause |
| 4 | free_recall | free_recall | working_memory |
| 5–10 | serial_recall | capacity_and_errors | capacity (length = 4,5,6,7,8,9 respectively, in randomized order — check `presented_sequence` length per row, don't assume order) |
| 11 | serial_recall | chunking | ungrouped |
| 12 | serial_recall | chunking | grouped |
| 13 | serial_recall | secondary_tasks | control |
| 14 | serial_recall | secondary_tasks | articulatory_suppression |
| 15 | serial_recall | secondary_tasks | finger_tapping |

Trials 11 and 12 use the **same digit sequence** (by design, to isolate the chunking timing effect from stimulus difficulty — confirm this holds in your data as a sanity check).

### 6.3 Important: `participant_code` holds real names now

Early in development this column was meant to hold an anonymous ID. The group later decided (deliberately) that participants should enter their real name so results can be attributed. **The column name is a leftover from the earlier design — it is not a bug, don't "fix" it, but do treat this field as personal data** when writing up the report (the group should discuss anonymization/pseudonymization before sharing the report or dataset outside the group).

### 6.4 Free-recall `score` field shape (from `backend/app/scoring/free_recall.py`)

```json
{
  "recalled_count": 8,
  "total_words": 15,
  "accuracy": 0.533,
  "recalled_words": ["bog", "kop", "..."],
  "intrusions": ["hund"],
  "position_groups": {
    "primacy": {"recalled": 3, "total": 5, "accuracy": 0.6},
    "middle":  {"recalled": 2, "total": 5, "accuracy": 0.4},
    "recency": {"recalled": 3, "total": 5, "accuracy": 0.6}
  }
}
```
Positions 1–5 in `presented_sequence` = primacy, 6–10 = middle, 11–15 = recency (matches the experiment design's position-group definition).

**Scoring is exact-match only** (after lowercasing + trimming + basic punctuation stripping — see `normalize_word()`). No spelling correction, no fuzzy matching, no singular/plural equivalence. This was a deliberate methodological choice (see §6.6 in `experiment-design.md`) — raw responses are preserved in `raw_response` so you can manually review near-misses if needed, but the `score` field's numbers reflect strict exact matching only.

### 6.5 Serial-recall `score` field shape (from `backend/app/scoring/serial_recall.py`)

```json
{
  "presented_length": 9,
  "response_length": 8,
  "positional_matches": 5,
  "positional_accuracy": 0.556,
  "whole_sequence_correct": false,
  "omissions": 1,
  "intrusions": 0,
  "substitutions": 3,
  "repetitions": 0,
  "transpositions": 2
}
```
Note: `repetitions` and `transpositions` are **not mutually exclusive** with `substitutions`/`omissions` — a single wrong digit can be counted under more than one category. Read the function itself (`backend/app/scoring/serial_recall.py`, ~30 lines, easy to follow) before doing arithmetic that assumes these are disjoint counts.

### 6.6 Suggested analysis plan

Follow `experiment-design.md` §2–5 exactly — it specifies exactly which comparisons the report needs:
- Primacy vs. middle, recency vs. middle (free recall, per condition)
- Fast vs. baseline (effect of presentation rate on primacy)
- Pause vs. working-memory vs. baseline (effect on recency)
- Accuracy vs. sequence length, 4–9 digits (serial-recall capacity curve)
- Grouped vs. ungrouped accuracy (chunking effect)
- Control vs. articulatory-suppression vs. finger-tapping accuracy (secondary-task effect)

Pull data with a Python script in `analysis/` (empty so far) using the `supabase` client or a direct Postgres connection, join `trials` to `sessions`, and produce the figures the report needs. Nothing here has been built yet — this is genuinely your starting point, not a partially-done task.

## 7. For the code-cleanup job

Concrete, specific things worth doing (not an exhaustive audit — use judgement, don't over-engineer):

- `backend/requirements.txt` has **no version pins** (`fastapi`, not `fastapi==0.141.1`). Pin versions for reproducibility before anyone else sets up the project.
- No automated tests exist anywhere. The two scoring functions (`free_recall.py`, `serial_recall.py`) are pure functions with no side effects — ideal candidates for simple `pytest` unit tests, and would directly protect the data-analysis job's assumptions in §6.4/6.5.
- `frontend/src/main.js` builds every screen as one big inline HTML template-literal string per function. This works but isn't very approachable for teaching purposes — consider whether extracting repeated patterns (e.g., the "kicker + h1 + intro + button" shape used by ~8 screens) into one small helper function would make it easier to explain to the group, without over-abstracting.
- No linter/formatter is configured (no ESLint, no Prettier, no `ruff`/`black` for Python). Worth adding if the group will keep editing this code.
- CORS in `backend/app/main.py` is hardcoded to `127.0.0.1:5173`/`localhost:5173` — correct for local dev, irrelevant in production (same-origin), but worth a one-line comment explaining why it's not a production concern.

## 8. For explaining the code to group members

Suggested order, cheapest-to-understand first:

1. **`experiment-design.md`** — the "why", not the code. Make sure everyone understands the protocol before looking at code.
2. **`supabase/schema.sql`** — two tables, ~15 columns each. This is the simplest file in the repo and grounds everything else ("the app's whole job is to fill in these two tables correctly").
3. **`backend/app/scoring/free_recall.py`** and **`serial_recall.py`** — small, pure, no dependencies, directly testable by hand with a pen-and-paper example. Best place to build confidence reading Python.
4. **`backend/app/main.py`** — walk through one endpoint at a time (`/api/pilot/start` → `/api/demo/score` is the free-recall pair; `/api/serial/start` → `/api/serial/score` is the serial pair). Point out `generate_intervals()` specifically since it directly implements the chunking timing from the experiment design.
5. **`frontend/src/main.js`** — explain the core pattern first: *every screen is a function that replaces `#app`'s HTML and attaches click handlers*. Once that clicks, the rest of the file is just "which function calls which function next." The `resumeAction`/Stop-button mechanism is the one genuinely subtle part — explain it as "each screen remembers how to restart itself if the participant hits Stop."

## 9. Deployment notes (only if you need to redeploy)

Hugging Face rejects direct pushes of this repo's `main` branch because it contains binary course materials (PDFs, a ZIP, a PNG) in its Git history, and it also rejects a normal push because those binaries exceed its size/type policy. The working deployment method used throughout this project:

```powershell
# Move the 4 binary files out of the working tree temporarily
$backup = Join-Path $env:TEMP 'human-memory-deploy-backup'
New-Item -ItemType Directory $backup
Move-Item '02464 Artificial intelligence and human cognition, Fall 2026 - 922026 - 137 PM.zip','CourseOverview.png','CourseOverviewLecture26.pdf','Slides02464_Week1_26.pdf' $backup

# Create a fresh orphan branch with no binary history, commit, force-push it as the Space's main
git checkout --orphan hf-deploy-tmp
git rm -r --cached .
git add .
git commit -m "Deploy <description>"
git push huggingface hf-deploy-tmp:main --force

# Restore local main and the course files
git checkout main
Move-Item -Force (Join-Path $backup '*') '.'
Remove-Item $backup -Recurse -Force
git branch -D hf-deploy-tmp
```

The Hugging Face remote is already configured (`git remote -v` will show `huggingface`). Space secrets (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`) are set under the Space's Settings → Variables and secrets — not in this repo.

## 10. If you get stuck

Re-read `experiment-design.md` first — nearly every "why does the app do X" question is answered there. This handoff document only explains the *implementation*, not the experimental logic behind it.
