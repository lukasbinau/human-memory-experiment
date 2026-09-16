import random
import unittest

import pandas as pd

from analysis.review_spelling import build_suggestions
from analysis.run_final_v2_analysis import validate_data
from backend.app.protocols.final_v2 import (
    build_adaptive_trials,
    build_baseline_trials,
    build_free_recall_conditions,
)
from backend.app.scoring.free_recall import score_response as score_free_recall
from backend.app.scoring.serial_recall import score_response as score_serial_recall


class FinalV2AnalysisTests(unittest.TestCase):
    def setUp(self):
        session_id = "session-v2"
        self.sessions = pd.DataFrame([{
            "id": session_id,
            "protocol_version": "final-v2.0-draft",
            "status": "completed",
            "started_at": "2026-09-16T10:00:00Z",
        }])
        rng = random.Random(42)
        words = [f"word{index}" for index in range(60)]
        free_conditions = build_free_recall_conditions(words)
        baseline_trials = build_baseline_trials(rng)
        adaptive_trials = build_adaptive_trials(random.Random(44), 9)
        trials = []
        for condition in free_conditions:
            raw_response = ", ".join(condition["words"])
            trials.append({
                "session_id": session_id,
                "trial_number": condition["trial_number"],
                "experiment_type": "free_recall",
                "condition": condition["name"],
                "presented_sequence": condition["words"],
                "raw_response": raw_response,
                "score": score_free_recall(condition["words"], raw_response),
                "task_data": {},
            })
        for trial in baseline_trials + adaptive_trials:
            task_data = {
                "chunks": trial.get("chunks", []),
                "matched_baseline_trial_number": trial.get("matched_baseline_trial_number", 8),
            }
            trials.append({
                "session_id": session_id,
                "trial_number": trial["trial_number"],
                "experiment_type": "serial_recall",
                "condition": trial["condition"],
                "presented_sequence": trial["sequence"],
                "raw_response": trial["sequence"],
                "score": score_serial_recall(trial["sequence"], trial["sequence"]),
                "task_data": task_data,
            })
        self.trials = pd.DataFrame(trials)

    def test_valid_complete_export_passes_quality_checks(self):
        quality = validate_data(self.sessions, self.trials)
        self.assertTrue(quality["passed"].all(), quality.loc[~quality["passed"]].to_dict("records"))

    def test_spelling_review_only_suggests_presented_words(self):
        export = {"trials": [{
            "session_id": "session-v2",
            "trial_number": 1,
            "experiment_type": "free_recall",
            "condition": "baseline",
            "presented_sequence": ["båd", "hammer"],
            "raw_response": "baad hammer fremmed",
        }]}
        suggestions = build_suggestions(export)
        self.assertEqual(set(suggestions["entered_word"]), {"baad", "fremmed"})
        self.assertTrue(set(suggestions["suggested_presented_word"]).issubset({"", "båd", "hammer"}))
        self.assertTrue(suggestions["review_decision"].eq("").all())


if __name__ == "__main__":
    unittest.main()