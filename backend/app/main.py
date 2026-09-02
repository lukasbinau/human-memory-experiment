from pathlib import Path
import random
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.scoring.free_recall import score_response
from backend.app.database.supabase_client import save_session, save_trial, complete_session

load_dotenv()

app = FastAPI(title="Human Memory Experiment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WORD_LIST_PATH = Path(__file__).resolve().parents[2] / "hukommelseseksperiment_300_ord.csv"


class ScoreRequest(BaseModel):
    session_id: str
    presented_words: list[str]
    response: str


def load_words() -> list[str]:
    lines = WORD_LIST_PATH.read_text(encoding="utf-8-sig").splitlines()
    return [line.strip() for line in lines[1:] if line.strip()]


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/demo/start")
def start_demo_trial():
    words = random.sample(load_words(), 15)
    session_id = str(uuid4())
    save_session({
        "id": session_id,
        "participant_code": f"pilot-{session_id[:8]}",
        "protocol_version": "pilot-v1.0",
        "random_seed": random.randint(0, 2**31 - 1),
        "consent_given": True,
    })
    return {
        "session_id": session_id,
        "condition": "baseline",
        "words": words,
        "display_ms": 2000,
    }


@app.post("/api/demo/score")
def score_demo_trial(request: ScoreRequest):
    result = score_response(request.presented_words, request.response)
    save_trial({
        "session_id": request.session_id,
        "experiment_type": "free_recall",
        "experiment_part": "demo",
        "condition": "baseline",
        "trial_number": 1,
        "presented_sequence": request.presented_words,
        "raw_response": request.response,
        "normalized_response": request.response.strip().lower(),
        "score": result,
        "timing": {"display_ms": 2000},
        "completed": True,
    })
    complete_session(request.session_id)
    return result
