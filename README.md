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

```text
npm install
npm run dev
```

The Python API can be started separately with:

```text
python -m uvicorn backend.app.main:app --reload
```
