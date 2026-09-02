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

Open the URL printed by Vite, normally `http://127.0.0.1:5173`. The current demo runs one baseline free-recall trial and sends trial generation and scoring requests to the Python API.
