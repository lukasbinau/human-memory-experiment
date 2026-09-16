# Analysis

The analysis code is separated by protocol version:

- `run_analysis.py`: historical 15-trial `pilot-v1.0` analysis.
- `run_final_analysis.py`: nine-trial `final-v1.0-draft` and future `final-v1.0` analysis.
- `run_final_v2_analysis.py`: 11-trial `final-v2.0-draft` validation and analysis.
- `review_spelling.py`: local, non-destructive free-recall spelling suggestions for manual review.

Run the current analysis from the repository root:

```text
python analysis/run_final_v2_analysis.py --input exports/final_v2_export.json
python analysis/review_spelling.py --input exports/final_v2_export.json
```

Never combine protocol versions in one primary analysis.
