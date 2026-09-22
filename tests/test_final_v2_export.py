import unittest

from analysis.export_final_v2_supabase import anonymize


class FinalV2ExportTests(unittest.TestCase):
    def test_anonymize_preserves_table_shape_and_foreign_keys(self):
        sessions = [{
            "id": "session-source-id",
            "participant_code": "Participant Name",
            "protocol_version": "final-v2.1-draft",
            "status": "completed",
        }]
        trials = [{
            "id": "trial-source-id",
            "session_id": "session-source-id",
            "trial_number": 1,
            "task_data": {"submissions": [{"word": "spejl"}]},
        }]

        exported, mapping = anonymize(sessions, trials)

        self.assertEqual(set(exported), {"sessions", "trials"})
        self.assertEqual(set(exported["sessions"][0]), set(sessions[0]))
        self.assertEqual(set(exported["trials"][0]), set(trials[0]))
        self.assertEqual(exported["sessions"][0]["participant_code"], "P001")
        self.assertNotEqual(exported["sessions"][0]["id"], sessions[0]["id"])
        self.assertEqual(exported["trials"][0]["session_id"], exported["sessions"][0]["id"])
        self.assertNotEqual(exported["trials"][0]["id"], trials[0]["id"])
        self.assertEqual(exported["trials"][0]["task_data"], trials[0]["task_data"])
        self.assertEqual(mapping[0]["participant_code"], "Participant Name")
        self.assertEqual(sessions[0]["participant_code"], "Participant Name")
        self.assertEqual(trials[0]["session_id"], "session-source-id")


if __name__ == "__main__":
    unittest.main()