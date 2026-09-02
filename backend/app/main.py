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
    condition: str = "baseline"
    trial_number: int = 1
    timing: dict = {}


def load_words() -> list[str]:
    lines = WORD_LIST_PATH.read_text(encoding="utf-8-sig").splitlines()
    return [line.strip() for line in lines[1:] if line.strip()]


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


def create_session() -> str:
    session_id = str(uuid4())
    save_session({
        "id": session_id,
        "participant_code": f"pilot-{session_id[:8]}",
        "protocol_version": "pilot-v1.0",
        "random_seed": random.randint(0, 2**31 - 1),
        "consent_given": True,
    })
    return session_id


@app.post("/api/demo/start")
def start_demo_trial():
    words = random.sample(load_words(), 15)
    session_id = create_session()
    return {
        "session_id": session_id,
        "condition": "baseline",
        "words": words,
        "display_ms": 2000,
    }


@app.post("/api/pilot/start")
def start_pilot():
    session_id = create_session()
    words = random.sample(load_words(), 60)
    conditions = [
        {"name": "baseline", "label": "Baseline", "display_ms": 2000, "post_task": "none"},
        {"name": "fast", "label": "Fast presentation", "display_ms": 1000, "post_task": "none"},
        {"name": "pause", "label": "Pause", "display_ms": 2000, "post_task": "pause"},
        {"name": "working_memory", "label": "Memory game", "display_ms": 2000, "post_task": "card_game"},
    ]
    for index, condition in enumerate(conditions):
        condition["words"] = words[index * 15 : (index + 1) * 15]
        condition["trial_number"] = index + 1
    return {"session_id": session_id, "conditions": conditions}


@app.post("/api/demo/score")
def score_demo_trial(request: ScoreRequest):
    result = score_response(request.presented_words, request.response)
    save_trial({
        "session_id": request.session_id,
        "experiment_type": "free_recall",
        "experiment_part": "free_recall",
        "condition": request.condition,
        "trial_number": request.trial_number,
        "presented_sequence": request.presented_words,
        "raw_response": request.response,
        "normalized_response": request.response.strip().lower(),
        "score": result,
        "timing": request.timing,
        "completed": True,
    })
    if request.trial_number >= 4:
        complete_session(request.session_id)
    return result
