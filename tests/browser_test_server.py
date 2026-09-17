"""Run the application with process-local storage for browser tests."""

from datetime import datetime, timezone
from pathlib import Path
import sys

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import main


sessions: dict[str, dict] = {}
trials: list[dict] = []


def save_session(session: dict) -> dict:
    stored = {
        **session,
        "status": "started",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    sessions[stored["id"]] = stored
    return stored


def save_trial(trial: dict) -> dict:
    existing = next(
        (
            row
            for row in trials
            if row["session_id"] == trial["session_id"]
            and row["trial_number"] == trial["trial_number"]
        ),
        None,
    )
    if existing:
        existing.update(trial)
        return existing
    stored = {**trial, "id": f"trial-{len(trials) + 1}"}
    trials.append(stored)
    return stored


def complete_trial(trial: dict) -> dict:
    existing = next(
        row
        for row in trials
        if row["session_id"] == trial["session_id"]
        and row["trial_number"] == trial["trial_number"]
    )
    if not existing.get("completed"):
        existing.update(trial)
    return existing


def get_session(session_id: str) -> dict | None:
    return sessions.get(session_id)


def get_trials(session_id: str) -> list[dict]:
    return sorted(
        [row for row in trials if row["session_id"] == session_id],
        key=lambda row: row["trial_number"],
    )


def get_next_trial_number(session_id: str) -> int:
    numbers = [row["trial_number"] for row in get_trials(session_id)]
    return max(numbers, default=0) + 1


def complete_session(session_id: str) -> dict:
    sessions[session_id].update({
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })
    return sessions[session_id]


main.save_session = save_session
main.save_trial = save_trial
main.complete_trial = complete_trial
main.get_session = get_session
main.get_trials = get_trials
main.get_next_trial_number = get_next_trial_number
main.complete_session = complete_session


if __name__ == "__main__":
    uvicorn.run(main.app, host="127.0.0.1", port=8011)