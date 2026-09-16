"""Create non-destructive spelling suggestions for free-recall responses."""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.scoring.free_recall import normalize_word


TOOL_VERSION = "spelling-review-v1"


def response_words(raw_response: str) -> list[str]:
    return [word for word in (normalize_word(part) for part in re.split(r"[\s,;]+", raw_response or "")) if word]


def build_suggestions(export: dict) -> pd.DataFrame:
    rows = []
    for trial in export["trials"]:
        if trial.get("experiment_type") != "free_recall":
            continue
        presented = [normalize_word(word) for word in trial["presented_sequence"]]
        for entered in response_words(trial.get("raw_response") or ""):
            if entered in presented:
                continue
            matches = difflib.get_close_matches(entered, presented, n=1, cutoff=0.6)
            suggestion = matches[0] if matches else ""
            confidence = difflib.SequenceMatcher(None, entered, suggestion).ratio() if suggestion else 0.0
            rows.append({
                "session_id": trial["session_id"],
                "trial_number": trial["trial_number"],
                "condition": trial["condition"],
                "entered_word": entered,
                "suggested_presented_word": suggestion,
                "similarity": round(confidence, 3),
                "review_decision": "",
                "reviewer_note": "",
                "tool_version": TOOL_VERSION,
            })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Suggest spelling corrections for manual review.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("spelling_review.csv"))
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as source:
        export = json.load(source)
    if "trials" not in export:
        raise ValueError("Input JSON must contain a trials array.")
    suggestions = build_suggestions(export)
    suggestions.to_csv(args.output, index=False)
    print(f"Wrote {len(suggestions)} spelling-review rows to {args.output}.")


if __name__ == "__main__":
    main()