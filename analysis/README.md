# Analysis

The analysis code is separated by protocol version:

- `run_analysis.py`: historical 15-trial `pilot-v1.0` analysis.
- `run_final_analysis.py`: nine-trial `final-v1.0-draft` and future `final-v1.0` analysis.
- `run_final_v2_analysis.py`: 11-trial `final-v2.1-draft` validation and analysis.
	It validates response-time bounds, attempt/refresh metadata, suppression
	confirmation, and finger-tapping evidence before producing trial tables.
- `review_spelling.py`: local, non-destructive free-recall spelling suggestions for manual review.

Run the current analysis from the repository root:

```text
python analysis/run_final_v2_analysis.py --input exports/final_v2_export.json
python analysis/review_spelling.py --input exports/final_v2_export.json
```

Create a standardized current-protocol Supabase snapshot with:

```text
python analysis/export_final_v2_supabase.py --snapshot-date YYYY-MM-DD
```

The identifiable source and participant mapping are written below the ignored
`exports/` directory. The shareable copy preserves the Supabase table structure
with anonymized participant/session/trial identifiers in a dated
`FINAL_V2_DATA_YYYY-MM-DD/` folder at the repository root.

Never combine protocol versions in one primary analysis.
