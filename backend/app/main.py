from pathlib import Path
import random

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.scoring.free_recall import score_response

app = FastAPI(title="Human Memory Experiment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WORD_LIST_PATH = Path(__file__).resolve().parents[2] / "hukommelseseksperiment_300_ord.csv"


class ScoreRequest(BaseModel):
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
    return {"condition": "baseline", "words": words, "display_ms": 2000}


@app.post("/api/demo/score")
def score_demo_trial(request: ScoreRequest):
    return score_response(request.presented_words, request.response)
