---
title: Human Memory Experiment
emoji: 🧠
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
short_description: DTU human memory experiment pilot
---

# Human Memory Experiment

Human-memory experiment app for the DTU course 02464 Artificial Intelligence and Human Cognition.

## Project layout

- `frontend/`: Vite participant interface
- `backend/`: Python FastAPI experiment logic and API
- `analysis/`: Python validation and pilot analysis
- `supabase/`: database schema and migration files
- `docs/final-v2.0-draft.md`: current experiment protocol
- `hukommelseseksperiment_300_ord.csv`: approved Danish word list

## Local development

Start the Python API from the repository root in one terminal:

```text
python -m uvicorn backend.app.main:app --reload --port 8000
```

If `python` is not available in your terminal, use the Python executable from your active environment instead. Then start the Vite frontend in a second terminal:

```text
npm install
npm run dev
```

Open the URL printed by Vite, normally `http://127.0.0.1:5173`. The default app runs the `final-v2.0-draft` 11-trial protocol, sends trial generation and scoring requests to the Python API, and saves sessions and completed trials in Supabase.

The current draft runs four 15-word free-recall trials, four serial baselines of 6–9 letters, two adaptive secondary-task trials, and one nine-letter chunking trial. See [docs/final-v2.0-draft.md](docs/final-v2.0-draft.md) for the contract, [docs/final-v2.0-build-plan.md](docs/final-v2.0-build-plan.md) for implementation details, and [docs/protocol-versions.md](docs/protocol-versions.md) for version history.

## Free-recall timing test

Open `?mode=timing-test` on the deployed or local frontend to run the standalone timing comparison:

```text
https://lukasbinau-human-memory-experiment.hf.space/?mode=timing-test
http://127.0.0.1:5173/?mode=timing-test
```

After entering a name, the tester chooses from ten predefined timing pairs. Each comparison presents two different 15-word lists in randomized, blinded timing order, saves both recall responses, and returns to the pair menu. The tester may try or repeat any pair and close the page when finished; there is no in-app evaluation form. These sessions use protocol `timing-test-v2` and remain separate from completed main-pilot sessions, so the main pilot analysis excludes them.

## Hugging Face deployment

The repository includes a `Dockerfile` that builds the Vite frontend and serves it from FastAPI on Hugging Face Spaces.

1. Create a new Hugging Face Space named `human-memory-experiment`.
2. Choose **Docker** as the Space SDK and choose the free hardware option.
3. Upload or push this repository to the Space.
4. In the Space, open **Settings > Variables and secrets**.
5. Add these secrets:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
```

Use the same values as the local `.env` file. Do not put them in the repository or in the Dockerfile. The Space exposes port `7860`, which is the port used by the Dockerfile.

The hosted frontend uses the same-origin `/api` path automatically. Local development continues to use `http://127.0.0.1:8000`.

## Supabase setup

1. Create a new Supabase project.
2. Open **SQL Editor** in the Supabase dashboard.
3. Open `supabase/schema.sql` from this repository, copy its contents, and run it in the SQL Editor.
4. Open **Project Settings > API**.
5. Copy the project URL into `SUPABASE_URL` in a local `.env` file.
6. Copy the `service_role` key into `SUPABASE_SERVICE_ROLE_KEY` in the same local `.env` file.

The service-role key is a backend secret. Never put it in frontend code, commit it to Git, or share it in chat. The database tables have row-level security enabled; only the backend service role will write pilot data.
