import csv
import random
import unittest
from pathlib import Path

from backend.app.protocols.final_v1 import (
    CONSONANT_POOL,
    DRAFT_CHUNKS,
    FREE_RECALL_FAST_MS,
    FREE_RECALL_NORMAL_MS,
    build_free_recall_conditions,
    build_serial_trials,
)


class FinalProtocolTests(unittest.TestCase):
    def setUp(self):
        self.trials = build_serial_trials(random.Random(42))

    def test_serial_order_and_lengths(self):
        self.assertEqual(
            [trial["condition"] for trial in self.trials],
            ["articulatory_suppression", "finger_tapping", "control", "ungrouped", "grouped"],
        )
        self.assertTrue(all(trial["length"] == 15 for trial in self.trials))

    def test_non_chunked_trials_use_each_approved_consonant_once(self):
        for trial in self.trials[:3]:
            self.assertEqual(set(trial["sequence"]), set(CONSONANT_POOL))
            self.assertEqual(len(set(trial["sequence"])), 15)

    def test_chunking_pair_uses_same_letters_and_exposure(self):
        ungrouped, grouped = self.trials[3:]
        self.assertEqual(ungrouped["sequence"], grouped["sequence"])
        self.assertEqual(ungrouped["total_exposure_ms"], grouped["total_exposure_ms"])
        self.assertEqual("".join(grouped["presentation_units"]), grouped["sequence"])

    def test_approved_chunks_are_unique_three_letter_words(self):
        chunks = [chunk for chunk, _ in DRAFT_CHUNKS]
        self.assertEqual(len(chunks), 13)
        self.assertEqual(len(chunks), len(set(chunks)))
        self.assertTrue(all(len(chunk) == 3 and chunk.isalpha() for chunk in chunks))

    def test_draft_chunks_exist_in_approved_danish_word_pool(self):
        word_list_path = Path(__file__).resolve().parents[1] / "hukommelseseksperiment_300_ord.csv"
        with word_list_path.open(encoding="utf-8-sig", newline="") as source:
            approved_words = {row["ord"].strip().upper() for row in csv.DictReader(source)}
        self.assertTrue({chunk for chunk, _ in DRAFT_CHUNKS}.issubset(approved_words))

    def test_free_recall_order_and_trial_numbers(self):
        conditions = build_free_recall_conditions([f"word-{index}" for index in range(60)])
        self.assertEqual([condition["name"] for condition in conditions], ["working_memory", "pause", "fast", "baseline"])
        self.assertEqual([condition["trial_number"] for condition in conditions], [6, 7, 8, 9])

    def test_fast_rate_is_half_the_normal_rate(self):
        self.assertEqual(FREE_RECALL_FAST_MS * 2, FREE_RECALL_NORMAL_MS)


if __name__ == "__main__":
    unittest.main()