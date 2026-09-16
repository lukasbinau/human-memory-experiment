import random
import unittest

from backend.app.protocols.final_v2 import (
    DANISH_LETTER_POOL,
    FREE_RECALL_FAST_MS,
    FREE_RECALL_NORMAL_MS,
    SERIAL_BLANK_MS,
    build_adaptive_trials,
    build_baseline_trials,
    build_free_recall_conditions,
    calculate_adaptive_length,
)


class FinalV2ProtocolTests(unittest.TestCase):
    def test_free_recall_order_and_trial_numbers(self):
        conditions = build_free_recall_conditions([f"word-{index}" for index in range(60)])
        self.assertEqual(
            [condition["name"] for condition in conditions],
            ["baseline", "fast", "pause", "working_memory"],
        )
        self.assertEqual([condition["trial_number"] for condition in conditions], [1, 2, 3, 4])
        self.assertEqual(FREE_RECALL_FAST_MS * 2, FREE_RECALL_NORMAL_MS)

    def test_free_recall_rejects_duplicate_words(self):
        with self.assertRaises(ValueError):
            build_free_recall_conditions(["same"] * 60)

    def test_baselines_are_six_through_nine_unique_letters(self):
        trials = build_baseline_trials(random.Random(42))
        self.assertEqual([trial["trial_number"] for trial in trials], [5, 6, 7, 8])
        self.assertEqual([trial["length"] for trial in trials], [6, 7, 8, 9])
        for trial in trials:
            self.assertEqual(len(set(trial["sequence"])), trial["length"])
            self.assertTrue(set(trial["sequence"]).issubset(DANISH_LETTER_POOL))
            self.assertEqual(trial["intervals"], [SERIAL_BLANK_MS] * (trial["length"] - 1))

    def test_adaptive_formula_clamps_and_reaches_nine(self):
        self.assertEqual(
            calculate_adaptive_length({6: 0, 7: 0, 8: 0, 9: 0})["adaptive_length"],
            6,
        )
        self.assertEqual(
            calculate_adaptive_length({6: 6, 7: 7, 8: 8, 9: 9})["adaptive_length"],
            9,
        )
        result = calculate_adaptive_length({6: 6, 7: 6, 8: 5, 9: 5})
        self.assertEqual(result["adaptive_length"], 6)
        self.assertEqual(result["rounding"], "floor")

    def test_adaptive_formula_validates_inputs(self):
        with self.assertRaises(ValueError):
            calculate_adaptive_length({6: 6, 7: 7, 8: 8})
        with self.assertRaises(ValueError):
            calculate_adaptive_length({6: 7, 7: 7, 8: 8, 9: 9})

    def test_adaptive_trials_match_length_and_chunk_shape(self):
        trials = build_adaptive_trials(random.Random(42), 7)
        self.assertEqual([trial["trial_number"] for trial in trials], [9, 10, 11])
        self.assertEqual([trial["length"] for trial in trials], [7, 7, 9])
        for trial in trials[:2]:
            self.assertEqual(len(set(trial["sequence"])), 7)
        chunk_trial = trials[2]
        self.assertEqual(len(chunk_trial["chunks"]), 3)
        self.assertTrue(all(len(chunk) == 3 for chunk in chunk_trial["chunks"]))
        self.assertEqual("".join(chunk_trial["presentation_units"]), chunk_trial["sequence"])
        self.assertEqual(chunk_trial["matched_baseline_trial_number"], 8)


if __name__ == "__main__":
    unittest.main()