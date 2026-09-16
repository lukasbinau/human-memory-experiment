from pathlib import Path
import random
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.app.protocols.final_v1 import (
    CARD_GAME_SECONDS,
    FREE_RECALL_PAUSE_SECONDS,
    FREE_RECALL_RESPONSE_SECONDS,
    PROTOCOL_VERSION as FINAL_PROTOCOL_VERSION,
    SERIAL_RESPONSE_SECONDS,
    build_free_recall_conditions,
    build_serial_trials,
)
from backend.app.protocols.final_v2 import (
    CARD_GAME_SECONDS as V2_CARD_GAME_SECONDS,
    FREE_RECALL_PAUSE_SECONDS as V2_FREE_RECALL_PAUSE_SECONDS,
    FREE_RECALL_RESPONSE_SECONDS as V2_FREE_RECALL_RESPONSE_SECONDS,
    PROTOCOL_VERSION as V2_PROTOCOL_VERSION,
    SECTION_BREAK_SECONDS as V2_SECTION_BREAK_SECONDS,
    SERIAL_RESPONSE_SECONDS as V2_SERIAL_RESPONSE_SECONDS,
    build_adaptive_trials as build_v2_adaptive_trials,
    build_baseline_trials as build_v2_baseline_trials,
    build_free_recall_conditions as build_v2_free_recall_conditions,
    calculate_adaptive_length,
)
from backend.app.scoring.free_recall import score_response
from backend.app.scoring.serial_recall import normalize_sequence
from backend.app.scoring.serial_recall import score_response as score_serial_response
from backend.app.database.supabase_client import (
    complete_session,
    get_next_trial_number,
    get_session,
    get_trials,
    save_session,
    save_trial,
)

load_dotenv()

app = FastAPI(title="Human Memory Experiment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WORD_LIST_PATH = Path(__file__).resolve().parents[2] / "hukommelseseksperiment_300_ord.csv"
TIMING_TEST_PAIRS = [
    ("500-750", 500, 750),
    ("500-1000", 500, 1000),
    ("750-1000", 750, 1000),
    ("750-1250", 750, 1250),
    ("1000-1250", 1000, 1250),
    ("1000-1500", 1000, 1500),
    ("1250-1500", 1250, 1500),
    ("1500-1750", 1500, 1750),
    ("1500-2000", 1500, 2000),
    ("2000-2500", 2000, 2500),
]


class ScoreRequest(BaseModel):
    session_id: str
    presented_words: list[str]
    response: str
    condition: str = "baseline"
    trial_number: int = 1
    timing: dict = {}
    task_data: dict = {}


class StartPilotRequest(BaseModel):
    participant_code: str


class TimingScoreRequest(ScoreRequest):
    pass


class FinalFreeScoreRequest(ScoreRequest):
    pass


class TimingPairRequest(BaseModel):
    session_id: str
    pair_id: str


class SerialScoreRequest(BaseModel):
    session_id: str
    presented_sequence: str
    response: str
    trial_number: int
    condition: str = "capacity"
    experiment_part: str = "capacity_and_errors"
    timing: dict = {}
    task_data: dict = {}


class StartSerialRequest(BaseModel):
    session_id: str | None = None


class V2SessionRequest(BaseModel):
    session_id: str


def load_words() -> list[str]:
    lines = WORD_LIST_PATH.read_text(encoding="utf-8-sig").splitlines()
    return [line.strip() for line in lines[1:] if line.strip()]


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


def create_session(participant_code: str, protocol_version: str = "pilot-v1.0", random_seed: int | None = None) -> str:
    session_id = str(uuid4())
    save_session({
        "id": session_id,
        "participant_code": participant_code,
        "protocol_version": protocol_version,
        "random_seed": random_seed if random_seed is not None else random.randint(0, 2**31 - 1),
        "consent_given": True,
    })
    return session_id


@app.post("/api/demo/start")
def start_demo_trial():
    words = random.sample(load_words(), 15)
    session_id = create_session(f"demo-{uuid4().hex[:8]}")
    return {
        "session_id": session_id,
        "condition": "baseline",
        "words": words,
        "display_ms": 2000,
    }


@app.post("/api/pilot/start")
def start_pilot(request: StartPilotRequest):
    session_id = create_session(request.participant_code)
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


@app.post("/api/final/start")
def start_final_protocol(request: StartPilotRequest):
    random_seed = random.randint(0, 2**31 - 1)
    rng = random.Random(random_seed)
    session_id = create_session(request.participant_code, FINAL_PROTOCOL_VERSION, random_seed)
    serial_trials = build_serial_trials(rng)
    free_recall_conditions = build_free_recall_conditions(rng.sample(load_words(), 60))
    return {
        "session_id": session_id,
        "protocol_version": FINAL_PROTOCOL_VERSION,
        "serial_trials": serial_trials,
        "free_recall_conditions": free_recall_conditions,
        "settings": {
            "free_recall_pause_seconds": FREE_RECALL_PAUSE_SECONDS,
            "card_game_seconds": CARD_GAME_SECONDS,
            "free_recall_response_seconds": FREE_RECALL_RESPONSE_SECONDS,
            "serial_response_seconds": SERIAL_RESPONSE_SECONDS,
        },
    }


@app.post("/api/v2/start")
def start_v2_protocol(request: StartPilotRequest):
    random_seed = random.randint(0, 2**31 - 1)
    session_id = create_session(request.participant_code, V2_PROTOCOL_VERSION, random_seed)
    return build_v2_initial_payload(session_id, random_seed)


def build_v2_initial_payload(session_id: str, random_seed: int) -> dict:
    rng = random.Random(random_seed)
    return {
        "session_id": session_id,
        "protocol_version": V2_PROTOCOL_VERSION,
        "free_recall_conditions": build_v2_free_recall_conditions(rng.sample(load_words(), 60)),
        "serial_baseline_trials": build_v2_baseline_trials(rng),
        "settings": {
            "free_recall_pause_seconds": V2_FREE_RECALL_PAUSE_SECONDS,
            "card_game_seconds": V2_CARD_GAME_SECONDS,
            "free_recall_response_seconds": V2_FREE_RECALL_RESPONSE_SECONDS,
            "serial_response_seconds": V2_SERIAL_RESPONSE_SECONDS,
            "section_break_seconds": V2_SECTION_BREAK_SECONDS,
        },
    }


@app.post("/api/v2/free-score")
def score_v2_free_recall(request: FinalFreeScoreRequest):
    if request.trial_number not in range(1, 5):
        raise HTTPException(status_code=400, detail="V2 free-recall trial number must be 1–4.")
    session = require_v2_session(request.session_id)
    expected = build_v2_initial_payload(request.session_id, int(session["random_seed"]))["free_recall_conditions"]
    expected_trial = expected[request.trial_number - 1]
    if request.condition != expected_trial["name"] or request.presented_words != expected_trial["words"]:
        raise HTTPException(status_code=400, detail="Free-recall trial does not match the session protocol.")
    existing = find_completed_trial(request.session_id, request.trial_number)
    if existing:
        return existing["score"]
    return save_free_recall_result(request)


def save_free_recall_result(request: ScoreRequest) -> dict:
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
        "task_data": request.task_data,
        "completed": True,
    })
    return result


@app.post("/api/v2/serial-score")
def score_v2_serial_trial(request: SerialScoreRequest):
    if request.trial_number not in range(5, 12):
        raise HTTPException(status_code=400, detail="V2 serial trial number must be 5–11.")
    session = require_v2_session(request.session_id)
    if request.trial_number <= 8:
        expected_trials = build_v2_initial_payload(
            request.session_id,
            int(session["random_seed"]),
        )["serial_baseline_trials"]
    else:
        expected_trials = build_v2_adaptive_payload(request.session_id, session)["trials"]
    expected_trial = next(
        (trial for trial in expected_trials if trial["trial_number"] == request.trial_number),
        None,
    )
    if (
        expected_trial is None
        or request.condition != expected_trial["condition"]
        or request.experiment_part != expected_trial["part"]
        or request.presented_sequence != expected_trial["sequence"]
    ):
        raise HTTPException(status_code=400, detail="Serial trial does not match the session protocol.")
    existing = find_completed_trial(request.session_id, request.trial_number)
    if existing:
        if request.trial_number == 11:
            complete_session(request.session_id)
        return existing["score"]
    authoritative_task_data = dict(request.task_data)
    if request.trial_number in (9, 10):
        authoritative_task_data.update({
            "adaptive_derivation": expected_trial["adaptive_derivation"],
            "matched_baseline_trial_number": expected_trial["matched_baseline_trial_number"],
        })
    elif request.trial_number == 11:
        authoritative_task_data.update({
            "chunks": expected_trial["chunks"],
            "matched_baseline_trial_number": expected_trial["matched_baseline_trial_number"],
        })
    request.task_data = authoritative_task_data
    result = save_serial_result(request)
    if request.trial_number == 11:
        complete_session(request.session_id)
    return result


def find_completed_trial(session_id: str, trial_number: int) -> dict | None:
    return next(
        (
            row
            for row in get_trials(session_id)
            if row.get("trial_number") == trial_number and row.get("completed")
        ),
        None,
    )


def save_serial_result(request: SerialScoreRequest) -> dict:
    result = score_serial_response(request.presented_sequence, request.response)
    save_trial({
        "session_id": request.session_id,
        "experiment_type": "serial_recall",
        "experiment_part": request.experiment_part,
        "condition": request.condition,
        "trial_number": request.trial_number,
        "presented_sequence": request.presented_sequence,
        "raw_response": request.response,
        "normalized_response": "".join(normalize_sequence(request.response)),
        "score": result,
        "timing": request.timing,
        "task_data": request.task_data,
        "completed": True,
    })
    return result


def require_v2_session(session_id: str) -> dict:
    session = get_session(session_id)
    if session is None or session.get("protocol_version") != V2_PROTOCOL_VERSION:
        raise HTTPException(status_code=404, detail="V2 session not found.")
    return session


@app.post("/api/v2/adaptive")
def get_v2_adaptive_trials(request: V2SessionRequest):
    session = require_v2_session(request.session_id)
    return build_v2_adaptive_payload(request.session_id, session)


def build_v2_adaptive_payload(session_id: str, session: dict) -> dict:
    baseline_rows = {
        row["trial_number"]: row
        for row in get_trials(session_id)
        if row.get("completed") and row.get("trial_number") in range(5, 9)
    }
    if set(baseline_rows) != set(range(5, 9)):
        raise HTTPException(status_code=409, detail="Complete serial baseline trials 5–8 first.")

    positional_matches = {
        trial_number + 1: int(baseline_rows[trial_number]["score"]["positional_matches"])
        for trial_number in range(5, 9)
    }
    derivation = calculate_adaptive_length(positional_matches)
    rng = random.Random(int(session["random_seed"]) + 2)
    trials = build_v2_adaptive_trials(rng, derivation["adaptive_length"])
    matched_trial_number = derivation["adaptive_length"] - 1
    for trial in trials[:2]:
        trial["matched_baseline_trial_number"] = matched_trial_number
        trial["adaptive_derivation"] = derivation
    return {"adaptive_derivation": derivation, "trials": trials}


@app.get("/api/v2/{session_id}/state")
def get_v2_state(session_id: str):
    session = require_v2_session(session_id)
    payload = build_v2_initial_payload(session_id, int(session["random_seed"]))
    rows = get_trials(session_id)
    payload["completed_trial_numbers"] = sorted(
        row["trial_number"] for row in rows if row.get("completed")
    )
    if set(range(5, 9)).issubset(payload["completed_trial_numbers"]):
        payload["adaptive"] = build_v2_adaptive_payload(session_id, session)
    return payload


@app.get("/api/v2/{session_id}/results")
def get_v2_results(session_id: str):
    require_v2_session(session_id)
    rows = sorted(
        (row for row in get_trials(session_id) if row.get("completed")),
        key=lambda row: row["trial_number"],
    )
    if {row["trial_number"] for row in rows} != set(range(1, 12)):
        raise HTTPException(status_code=409, detail="Complete all 11 trials before viewing results.")
    free_rows = [row for row in rows if row["experiment_type"] == "free_recall"]
    serial_rows = [row for row in rows if row["experiment_type"] == "serial_recall"]
    trial_results = [
        {
            "trial_number": row["trial_number"],
            "section": row["experiment_type"],
            "correct": int(
                row["score"]["recalled_count"]
                if row["experiment_type"] == "free_recall"
                else row["score"]["positional_matches"]
            ),
            "total": int(
                row["score"]["total_words"]
                if row["experiment_type"] == "free_recall"
                else row["score"]["presented_length"]
            ),
        }
        for row in rows
    ]
    return {
        "free_recall_recalled": sum(int(row["score"]["recalled_count"]) for row in free_rows),
        "free_recall_total": sum(int(row["score"]["total_words"]) for row in free_rows),
        "serial_positional_matches": sum(int(row["score"]["positional_matches"]) for row in serial_rows),
        "serial_total": sum(int(row["score"]["presented_length"]) for row in serial_rows),
        "trials": trial_results,
    }


@app.post("/api/timing-test/start")
def start_timing_test(request: StartPilotRequest):
    session_id = create_session(request.participant_code, "timing-test-v2")
    pairs = [
        {"id": pair_id, "first_ms": first_ms, "second_ms": second_ms}
        for pair_id, first_ms, second_ms in TIMING_TEST_PAIRS
    ]
    return {"session_id": session_id, "pairs": pairs}


@app.post("/api/timing-test/pair")
def start_timing_pair(request: TimingPairRequest):
    pair = next((pair for pair in TIMING_TEST_PAIRS if pair[0] == request.pair_id), None)
    if pair is None:
        raise HTTPException(status_code=400, detail="Unknown timing pair.")
    pair_id, first_ms, second_ms = pair
    intervals = random.sample([first_ms, second_ms], 2)
    words = random.sample(load_words(), 30)
    first_trial_number = get_next_trial_number(request.session_id)
    conditions = []
    for index, display_ms in enumerate(intervals):
        conditions.append({
            "name": f"timing_{display_ms}ms",
            "label": f"List {index + 1}",
            "display_ms": display_ms,
            "post_task": "none",
            "words": words[index * 15 : (index + 1) * 15],
            "trial_number": first_trial_number + index,
        })
    return {"pair_id": pair_id, "conditions": conditions}


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
        "task_data": request.task_data,
        "completed": True,
    })
    return result


@app.post("/api/timing-test/score")
def score_timing_test_trial(request: TimingScoreRequest):
    result = score_response(request.presented_words, request.response)
    save_trial({
        "session_id": request.session_id,
        "experiment_type": "free_recall",
        "experiment_part": "timing_test",
        "condition": request.condition,
        "trial_number": request.trial_number,
        "presented_sequence": request.presented_words,
        "raw_response": request.response,
        "normalized_response": request.response.strip().lower(),
        "score": result,
        "timing": request.timing,
        "task_data": request.task_data,
        "completed": True,
    })
    return result


@app.post("/api/final/free-score")
def score_final_free_recall(request: FinalFreeScoreRequest):
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
        "task_data": request.task_data,
        "completed": True,
    })
    if request.trial_number == 9:
        complete_session(request.session_id)
    return result


def generate_digits(length: int) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def generate_intervals(length: int, grouped: bool = False) -> list[int]:
    """Blank durations (ms) after each digit except the last."""
    if not grouped:
        return [500] * (length - 1)
    intervals = []
    for position in range(1, length):
        intervals.append(1250 if position % 3 == 0 else 250)
    return intervals


@app.post("/api/serial/start")
def start_serial_pilot(request: StartSerialRequest | None = None):
    session_id = request.session_id if request and request.session_id else create_session(f"serial-{uuid4().hex[:8]}")
    trials = []
    for index, length in enumerate(range(4, 10)):
        trials.append({
            "trial_number": index + 5,
            "part": "capacity_and_errors",
            "condition": "capacity",
            "label": f"Capacity · {length} digits",
            "length": length,
            "sequence": generate_digits(length),
            "intervals": generate_intervals(length),
        })

    chunk_sequence = generate_digits(9)
    trials.extend([
        {
            "trial_number": 11,
            "part": "chunking",
            "condition": "ungrouped",
            "label": "Chunking · ungrouped",
            "length": 9,
            "sequence": chunk_sequence,
            "intervals": generate_intervals(9, grouped=False),
        },
        {
            "trial_number": 12,
            "part": "chunking",
            "condition": "grouped",
            "label": "Chunking · grouped",
            "length": 9,
            "sequence": chunk_sequence,
            "intervals": generate_intervals(9, grouped=True),
        },
    ])
    for index, condition in enumerate(["control", "articulatory_suppression", "finger_tapping"]):
        trials.append({
            "trial_number": index + 13,
            "part": "secondary_tasks",
            "condition": condition,
            "label": condition.replace("_", " ").title(),
            "length": 8,
            "sequence": generate_digits(8),
            "intervals": generate_intervals(8),
        })
    return {"session_id": session_id, "trials": trials, "display_ms": 1000, "interval_ms": 500}


@app.post("/api/serial/score")
def score_serial_trial(request: SerialScoreRequest):
    result = score_serial_response(request.presented_sequence, request.response)
    save_trial({
        "session_id": request.session_id,
        "experiment_type": "serial_recall",
        "experiment_part": request.experiment_part,
        "condition": request.condition,
        "trial_number": request.trial_number,
        "presented_sequence": request.presented_sequence,
        "raw_response": request.response,
        "normalized_response": "".join(normalize_sequence(request.response)),
        "score": result,
        "timing": request.timing or {"display_ms": 1000, "interval_ms": 500},
        "task_data": request.task_data,
        "completed": True,
    })
    if request.trial_number >= 15:
        complete_session(request.session_id)
    return result


DIST_PATH = Path(__file__).resolve().parents[2] / "dist"
if DIST_PATH.exists():
    app.mount("/", StaticFiles(directory=DIST_PATH, html=True), name="frontend")
