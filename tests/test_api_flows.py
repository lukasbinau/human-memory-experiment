import unittest
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from analysis.run_final_analysis import build_serial_table, validate_data
from backend.app.main import app


class InMemoryPersistence:
    def __init__(self):
        self.sessions = {}
        self.trials = []

    def save_session(self, session: dict) -> dict:
        stored = {**session, "status": "started", "started_at": "2026-09-11T10:00:00Z"}
        self.sessions[stored["id"]] = stored
        return stored

    def save_trial(self, trial: dict) -> dict:
        key = (trial["session_id"], trial["trial_number"])
        existing = next(
            (row for row in self.trials if (row["session_id"], row["trial_number"]) == key),
            None,
        )
        if existing:
            existing.update(trial)
            return existing
        stored = {**trial, "id": f"trial-{len(self.trials) + 1}"}
        self.trials.append(stored)
        return stored

    def get_session(self, session_id: str) -> dict | None:
        return self.sessions.get(session_id)

    def get_trials(self, session_id: str) -> list[dict]:
        return sorted(
            [row for row in self.trials if row["session_id"] == session_id],
            key=lambda row: row["trial_number"],
        )

    def next_trial_number(self, session_id: str) -> int:
        numbers = [row["trial_number"] for row in self.trials if row["session_id"] == session_id]
        return max(numbers, default=0) + 1

    def complete_session(self, session_id: str) -> dict:
        self.sessions[session_id]["status"] = "completed"
        self.sessions[session_id]["completed_at"] = "2026-09-11T10:15:00Z"
        return self.sessions[session_id]


class ApiFlowTests(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryPersistence()
        self.patchers = [
            patch("backend.app.main.save_session", self.store.save_session),
            patch("backend.app.main.save_trial", self.store.save_trial),
            patch("backend.app.main.get_next_trial_number", self.store.next_trial_number),
            patch("backend.app.main.get_session", self.store.get_session),
            patch("backend.app.main.get_trials", self.store.get_trials),
            patch("backend.app.main.complete_session", self.store.complete_session),
        ]
        for patcher in self.patchers:
            patcher.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        for patcher in reversed(self.patchers):
            patcher.stop()

    def test_complete_final_protocol_and_analysis_contract(self):
        response = self.client.post("/api/final/start", json={"participant_code": "Integration Tester"})
        self.assertEqual(response.status_code, 200)
        protocol = response.json()
        session_id = protocol["session_id"]
        self.assertEqual(protocol["protocol_version"], "final-v1.0-draft")
        self.assertEqual(len(protocol["serial_trials"]), 5)
        self.assertEqual(len(protocol["free_recall_conditions"]), 4)
        self.assertEqual(protocol["serial_trials"][3]["sequence"], protocol["serial_trials"][4]["sequence"])

        for trial in protocol["serial_trials"]:
            response = self.client.post("/api/serial/score", json={
                "session_id": session_id,
                "presented_sequence": trial["sequence"],
                "response": " ".join(trial["sequence"].lower()),
                "trial_number": trial["trial_number"],
                "condition": trial["condition"],
                "experiment_part": trial["part"],
                "timing": {
                    "presentation_units": trial["presentation_units"],
                    "unit_display_ms": trial["unit_display_ms"],
                    "intervals": trial["intervals"],
                    "total_exposure_ms": trial["total_exposure_ms"],
                },
                "task_data": {"tap_count": 12 if trial["condition"] == "finger_tapping" else 0},
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["positional_accuracy"], 1)

        self.assertEqual(self.store.sessions[session_id]["status"], "started")
        for condition in protocol["free_recall_conditions"]:
            response = self.client.post("/api/final/free-score", json={
                "session_id": session_id,
                "presented_words": condition["words"],
                "response": ", ".join(condition["words"]),
                "condition": condition["name"],
                "trial_number": condition["trial_number"],
                "timing": {"display_ms": condition["display_ms"], "post_task": condition["post_task"]},
                "task_data": {"submissions": []},
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["accuracy"], 1)

        self.assertEqual(self.store.sessions[session_id]["status"], "completed")
        self.assertEqual(len(self.store.trials), 9)
        sessions = pd.DataFrame([{**self.store.sessions[session_id], "participant_id": "P01"}])
        trials = pd.DataFrame(self.store.trials)
        quality = validate_data(sessions, trials)
        self.assertTrue(quality["passed"].all(), quality.loc[~quality["passed"]].to_dict("records"))
        serial_table = build_serial_table(sessions, trials)
        self.assertTrue(serial_table["ordered_subsequence_accuracy"].eq(1).all())
        self.assertTrue(serial_table["item_accuracy"].eq(1).all())
        self.assertTrue(serial_table["positional_accuracy"].eq(1).all())

    def test_timing_pairs_can_repeat_without_completing_main_session(self):
        response = self.client.post("/api/timing-test/start", json={"participant_code": "Timing Tester"})
        self.assertEqual(response.status_code, 200)
        timing_session = response.json()
        session_id = timing_session["session_id"]
        self.assertEqual(len(timing_session["pairs"]), 10)
        pair_id = "500-1000"

        generated_trials = []
        for expected_numbers in ([1, 2], [3, 4]):
            response = self.client.post("/api/timing-test/pair", json={"session_id": session_id, "pair_id": pair_id})
            self.assertEqual(response.status_code, 200)
            conditions = response.json()["conditions"]
            self.assertEqual(sorted(condition["display_ms"] for condition in conditions), [500, 1000])
            self.assertEqual([condition["trial_number"] for condition in conditions], expected_numbers)
            self.assertEqual(len({word for condition in conditions for word in condition["words"]}), 30)
            generated_trials.extend(conditions)
            for condition in conditions:
                score = self.client.post("/api/timing-test/score", json={
                    "session_id": session_id,
                    "presented_words": condition["words"],
                    "response": "",
                    "condition": condition["name"],
                    "trial_number": condition["trial_number"],
                    "timing": {"display_ms": condition["display_ms"]},
                    "task_data": {"pair_id": pair_id},
                })
                self.assertEqual(score.status_code, 200)

        self.assertEqual(len(generated_trials), 4)
        self.assertEqual(len(self.store.trials), 4)
        self.assertEqual(self.store.sessions[session_id]["protocol_version"], "timing-test-v2")
        self.assertEqual(self.store.sessions[session_id]["status"], "started")

    def test_complete_v2_protocol_with_adaptive_trials_and_results(self):
        response = self.client.post("/api/v2/start", json={"participant_code": "V2 Tester"})
        self.assertEqual(response.status_code, 200)
        protocol = response.json()
        session_id = protocol["session_id"]
        self.assertEqual(protocol["protocol_version"], "final-v2.0-draft")
        self.assertEqual(
            [condition["trial_number"] for condition in protocol["free_recall_conditions"]],
            [1, 2, 3, 4],
        )
        self.assertEqual(
            [trial["length"] for trial in protocol["serial_baseline_trials"]],
            [6, 7, 8, 9],
        )

        for condition in protocol["free_recall_conditions"]:
            score = self.client.post("/api/v2/free-score", json={
                "session_id": session_id,
                "presented_words": condition["words"],
                "response": ", ".join(condition["words"]),
                "condition": condition["name"],
                "trial_number": condition["trial_number"],
                "timing": {
                    "display_ms": condition["display_ms"],
                    "post_task": condition["post_task"],
                    "post_task_seconds": 15 if condition["post_task"] != "none" else 0,
                    "response_limit_seconds": 90,
                },
                "task_data": {"response_ms": 1234},
            })
            self.assertEqual(score.status_code, 200)

        for trial in protocol["serial_baseline_trials"]:
            score = self.client.post("/api/v2/serial-score", json={
                "session_id": session_id,
                "presented_sequence": trial["sequence"],
                "response": trial["sequence"],
                "trial_number": trial["trial_number"],
                "condition": trial["condition"],
                "experiment_part": trial["part"],
            })
            self.assertEqual(score.status_code, 200)

        adaptive_response = self.client.post("/api/v2/adaptive", json={"session_id": session_id})
        self.assertEqual(adaptive_response.status_code, 200)
        adaptive = adaptive_response.json()
        self.assertEqual(adaptive["adaptive_derivation"]["adaptive_length"], 9)
        self.assertEqual([trial["trial_number"] for trial in adaptive["trials"]], [9, 10, 11])

        for trial in adaptive["trials"]:
            score = self.client.post("/api/v2/serial-score", json={
                "session_id": session_id,
                "presented_sequence": trial["sequence"],
                "response": trial["sequence"],
                "trial_number": trial["trial_number"],
                "condition": trial["condition"],
                "experiment_part": trial["part"],
                "task_data": {
                    "matched_baseline_trial_number": trial.get("matched_baseline_trial_number"),
                    "adaptive_derivation": trial.get("adaptive_derivation"),
                },
            })
            self.assertEqual(score.status_code, 200)

        self.assertEqual(self.store.sessions[session_id]["status"], "completed")
        self.assertEqual(len(self.store.get_trials(session_id)), 11)
        first_trial = self.store.get_trials(session_id)[0]
        self.assertEqual(first_trial["timing"]["response_limit_seconds"], 90)
        self.assertEqual(first_trial["task_data"]["response_ms"], 1234)
        results = self.client.get(f"/api/v2/{session_id}/results")
        self.assertEqual(results.status_code, 200)
        result_data = results.json()
        self.assertEqual({key: result_data[key] for key in (
            "free_recall_recalled",
            "free_recall_total",
            "serial_positional_matches",
            "serial_total",
        )}, {
            "free_recall_recalled": 60,
            "free_recall_total": 60,
            "serial_positional_matches": 57,
            "serial_total": 57,
        })
        self.assertEqual(len(result_data["trials"]), 11)
        self.assertEqual(result_data["trials"][0], {
            "trial_number": 1,
            "section": "free_recall",
            "correct": 15,
            "total": 15,
        })
        self.assertEqual(result_data["trials"][-1], {
            "trial_number": 11,
            "section": "serial_recall",
            "correct": 9,
            "total": 9,
        })

        final_trial = adaptive["trials"][-1]
        retry = self.client.post("/api/v2/serial-score", json={
            "session_id": session_id,
            "presented_sequence": final_trial["sequence"],
            "response": "",
            "trial_number": 11,
            "condition": final_trial["condition"],
            "experiment_part": final_trial["part"],
        })
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.json()["positional_accuracy"], 1)
        self.assertEqual(len(self.store.get_trials(session_id)), 11)
        self.assertEqual(self.store.sessions[session_id]["status"], "completed")

        state = self.client.get(f"/api/v2/{session_id}/state")
        self.assertEqual(state.status_code, 200)
        self.assertEqual(state.json()["completed_trial_numbers"], list(range(1, 12)))

    def test_unknown_timing_pair_returns_client_error(self):
        response = self.client.post("/api/timing-test/pair", json={"session_id": "missing", "pair_id": "not-a-pair"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Unknown timing pair.")


if __name__ == "__main__":
    unittest.main()