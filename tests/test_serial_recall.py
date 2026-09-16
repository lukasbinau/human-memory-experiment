import unittest

from backend.app.scoring.serial_recall import normalize_sequence, score_response


class SerialRecallScoringTests(unittest.TestCase):
    def test_normalizes_letter_case_and_separators(self):
        self.assertEqual(normalize_sequence("b d-f,å"), ["B", "D", "F", "Å"])

    def test_scores_perfect_letter_response(self):
        result = score_response("BDFGHJKLMNPRSTV", "b d f g h j k l m n p r s t v")
        self.assertEqual(result["positional_matches"], 15)
        self.assertEqual(result["positional_accuracy"], 1)
        self.assertEqual(result["item_accuracy"], 1)
        self.assertEqual(result["ordered_subsequence_accuracy"], 1)
        self.assertTrue(result["whole_sequence_correct"])

    def test_credits_ordered_recall_after_an_omission(self):
        result = score_response("BDFGH", "BDGH")
        self.assertEqual(result["positional_matches"], 2)
        self.assertEqual(result["item_matches"], 4)
        self.assertEqual(result["ordered_subsequence_matches"], 4)
        self.assertEqual(result["ordered_subsequence_accuracy"], 0.8)
        self.assertEqual(result["omissions"], 1)

    def test_separates_item_recall_from_ordered_recall(self):
        result = score_response("BDFGH", "BFDGH")
        self.assertEqual(result["item_matches"], 5)
        self.assertEqual(result["ordered_subsequence_matches"], 4)

    def test_preserves_legacy_digit_scoring(self):
        result = score_response("4729163", "4721963")
        self.assertEqual(result["presented_length"], 7)
        self.assertEqual(result["positional_matches"], 5)
        self.assertEqual(result["substitutions"], 2)
        self.assertEqual(result["transpositions"], 2)

    def test_reports_letter_omissions_and_repetitions(self):
        result = score_response("BDFG", "BBDD")
        self.assertEqual(result["positional_matches"], 1)
        self.assertEqual(result["repetitions"], 2)
        self.assertEqual(result["substitutions"], 3)


if __name__ == "__main__":
    unittest.main()