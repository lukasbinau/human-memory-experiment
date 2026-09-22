"""Export and anonymize the current experiment data from Supabase."""

import argparse
import copy
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.run_final_v2_analysis import PROTOCOL_VERSION, validate_data
from backend.app.database.supabase_client import get_supabase_client


ANONYMIZATION_NAMESPACE = uuid.UUID("24064a6b-1f8d-4bbd-923d-eefe68bcae21")
TEST_NAME_MARKERS = ("test", "tester", "validation", "fixed flow", "pending input")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export current-protocol Supabase data.")
    parser.add_argument("--protocol-version", default=PROTOCOL_VERSION)
    parser.add_argument("--snapshot-date", default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument("--private-root", type=Path, default=ROOT / "exports")
    parser.add_argument("--public-root", type=Path, default=ROOT / "analysis" / "data")
    return parser.parse_args()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch_protocol_data(protocol_version: str) -> tuple[list[dict], list[dict]]:
    client = get_supabase_client()
    sessions = (
        client.table("sessions")
        .select("*")
        .eq("protocol_version", protocol_version)
        .order("started_at")
        .execute()
        .data
        or []
    )
    session_ids = {session["id"] for session in sessions}
    trials = [
        trial
        for trial in (client.table("trials").select("*").execute().data or [])
        if trial.get("session_id") in session_ids
    ]
    trials.sort(key=lambda trial: (trial["session_id"], trial["trial_number"]))
    return sessions, trials


def is_test_session(participant_code: str) -> bool:
    lowered = participant_code.lower()
    return any(marker in lowered for marker in TEST_NAME_MARKERS)


def build_quality_assessment(
    sessions: list[dict], trials: list[dict], protocol_version: str = PROTOCOL_VERSION
) -> dict:
    completed_sessions = [session for session in sessions if session.get("status") == "completed"]
    completed_ids = {session["id"] for session in completed_sessions}
    completed_trials = [trial for trial in trials if trial["session_id"] in completed_ids]
    validation = (
        validate_data(pd.DataFrame(completed_sessions), pd.DataFrame(completed_trials))
        if completed_sessions
        else pd.DataFrame()
    )
    assessments = []
    for participant_index, session in enumerate(sessions, start=1):
        participant_id = f"P{participant_index:03d}"
        rows = sorted(
            (trial for trial in trials if trial["session_id"] == session["id"]),
            key=lambda trial: trial["trial_number"],
        )
        by_number = {trial["trial_number"]: trial for trial in rows}
        completed = session.get("status") == "completed"
        test_session = is_test_session(session.get("participant_code") or "")
        complete_trial_set = (
            [trial["trial_number"] for trial in rows] == list(range(1, 12))
            and all(trial.get("completed") for trial in rows)
        )
        free_rows = [by_number[number] for number in range(1, 5) if number in by_number]
        all_free_recall_empty = len(free_rows) == 4 and all(
            not (trial.get("raw_response") or "").strip()
            and not ((trial.get("task_data") or {}).get("submissions") or [])
            for trial in free_rows
        )
        session_checks = (
            validation.loc[validation["session_id"].eq(session["id"])]
            if completed and not validation.empty
            else pd.DataFrame()
        )
        failed_checks = (
            session_checks.loc[~session_checks["passed"], ["check", "detail"]].to_dict("records")
            if not session_checks.empty
            else []
        )
        base_eligible = completed and complete_trial_set and not test_session
        suppression_confirmed = (by_number.get(9, {}).get("task_data") or {}).get("suppression_confirmed")
        tapping_data = by_number.get(10, {}).get("task_data") or {}
        tap_times = tapping_data.get("tap_times_ms")
        tapping_evidence = (
            isinstance(tap_times, list)
            and len(tap_times) > 0
            and tapping_data.get("tap_count") == len(tap_times)
        )
        trial_checks_pass = lambda number: not any(
            check["check"] in {f"trial_{number}", f"score_{number}", f"response_time_{number}", f"attempt_metadata_{number}"}
            for check in failed_checks
        )
        free_recall_usable = base_eligible and not all_free_recall_empty and all(
            trial_checks_pass(number) for number in range(1, 5)
        )
        serial_baseline_usable = base_eligible and all(trial_checks_pass(number) for number in range(5, 9)) and not any(
            check["check"].startswith("unique_letters_") for check in failed_checks
        )
        adaptive_derivation_usable = not any(
            check["check"] == "adaptive_lengths" for check in failed_checks
        )
        suppression_usable = (
            base_eligible
            and trial_checks_pass(9)
            and adaptive_derivation_usable
            and not any(check["check"] in {"matched_baseline_9", "suppression_compliance_recorded"} for check in failed_checks)
            and suppression_confirmed is True
        )
        tapping_usable = (
            base_eligible
            and trial_checks_pass(10)
            and adaptive_derivation_usable
            and not any(check["check"] in {"matched_baseline_10", "tapping_evidence"} for check in failed_checks)
            and tapping_evidence
        )
        chunking_usable = base_eligible and trial_checks_pass(11) and not any(
            check["check"] in {"chunk_words", "chunk_flattening"} for check in failed_checks
        )
        reasons = []
        if test_session:
            reasons.append("known_test_session")
        if not completed:
            reasons.append("session_not_completed")
        if completed and not complete_trial_set:
            reasons.append("incomplete_or_duplicate_trial_set")
        if all_free_recall_empty:
            reasons.append("all_free_recall_responses_empty_known_ui_risk")
        if suppression_confirmed is False:
            reasons.append("suppression_not_performed")
        if 10 in by_number and not tapping_evidence:
            reasons.append("finger_tapping_evidence_missing")
        assessments.append({
            "participant_id": participant_id,
            "session_id": str(uuid.uuid5(ANONYMIZATION_NAMESPACE, session["id"])),
            "session_status": session.get("status"),
            "trial_count": len(rows),
            "completed_trial_count": sum(bool(trial.get("completed")) for trial in rows),
            "is_test_session": test_session,
            "all_free_recall_responses_empty": all_free_recall_empty,
            "failed_validation_checks": failed_checks,
            "exclusion_reasons": reasons,
            "usable": {
                "complete_session": base_eligible,
                "free_recall": free_recall_usable,
                "serial_baseline": serial_baseline_usable,
                "articulatory_suppression": suppression_usable,
                "finger_tapping": tapping_usable,
                "chunking": chunking_usable,
                "all_sections": all((
                    free_recall_usable,
                    serial_baseline_usable,
                    suppression_usable,
                    tapping_usable,
                    chunking_usable,
                )),
            },
        })
    return {"protocol_version": protocol_version, "sessions": assessments}


def anonymize(sessions: list[dict], trials: list[dict]) -> tuple[dict, list[dict]]:
    session_map = {
        session["id"]: str(uuid.uuid5(ANONYMIZATION_NAMESPACE, session["id"]))
        for session in sessions
    }
    trial_map = {
        trial["id"]: str(uuid.uuid5(ANONYMIZATION_NAMESPACE, trial["id"]))
        for trial in trials
    }
    anonymized_sessions = copy.deepcopy(sessions)
    private_mapping = []
    for participant_index, session in enumerate(anonymized_sessions, start=1):
        original_id = session["id"]
        participant_id = f"P{participant_index:03d}"
        private_mapping.append({
            "participant_id": participant_id,
            "session_id": original_id,
            "anonymized_session_id": session_map[original_id],
            "participant_code": session["participant_code"],
        })
        session["id"] = session_map[original_id]
        session["participant_code"] = participant_id
    anonymized_trials = copy.deepcopy(trials)
    for trial in anonymized_trials:
        trial["id"] = trial_map[trial["id"]]
        trial["session_id"] = session_map[trial["session_id"]]
    return {"sessions": anonymized_sessions, "trials": anonymized_trials}, private_mapping


def main() -> None:
    args = parse_args()
    load_dotenv(dotenv_path=ROOT / ".env")
    sessions, trials = fetch_protocol_data(args.protocol_version)
    exported_at = datetime.now(timezone.utc).isoformat()
    private_directory = args.private_root / f"{args.protocol_version}_{args.snapshot_date}"
    public_directory = args.public_root / f"{args.protocol_version}_{args.snapshot_date}"
    raw_export = {"sessions": sessions, "trials": trials}
    anonymized_export, private_mapping = anonymize(sessions, trials)
    quality = build_quality_assessment(sessions, trials, args.protocol_version)
    quality["exported_at"] = exported_at
    quality["counts"] = {
        "sessions": len(sessions),
        "trials": len(trials),
        "completed_sessions": sum(session.get("status") == "completed" for session in sessions),
    }
    write_json(private_directory / "supabase_export.json", raw_export)
    write_json(private_directory / "private_participant_mapping.json", private_mapping)
    write_json(public_directory / "supabase_export_anonymized.json", anonymized_export)
    write_json(public_directory / "quality_assessment.json", quality)
    write_json(public_directory / "export_manifest.json", {
        "exported_at": exported_at,
        "protocol_version": args.protocol_version,
        "source": "Supabase sessions and trials tables",
        "sessions": len(sessions),
        "trials": len(trials),
        "completed_sessions": quality["counts"]["completed_sessions"],
        "anonymization": "participant_code replaced by participant_id; session and trial UUIDs replaced deterministically",
    })
    print(f"Private export: {private_directory}")
    print(f"Shareable export: {public_directory}")
    print(f"Exported {len(sessions)} sessions and {len(trials)} trials.")


if __name__ == "__main__":
    main()