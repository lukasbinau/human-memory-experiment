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

Pilot app for the DTU course 02464 Artificial Intelligence and Human Cognition.

## Project layout

- `frontend/`: Vite participant interface
- `backend/`: Python FastAPI experiment logic and API
- `analysis/`: Python validation and pilot analysis
- `supabase/`: database schema and migration files
- `experiment-design.md`: current pilot protocol
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

Open the URL printed by Vite, normally `http://127.0.0.1:5173`. The current pilot app offers free recall and serial recall modes, sends trial generation and scoring requests to the Python API, and saves sessions and completed trials in Supabase.

The serial-recall pilot currently runs six capacity trials with sequence lengths 4, 5, 6, 7, 8, and 9 digits.

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
