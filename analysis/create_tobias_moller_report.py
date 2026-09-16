"""Create a participant-facing PDF summary for Tobias Møller's completed session."""

import sys
from pathlib import Path

from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.database.supabase_client import get_supabase_client


OUTPUT_PATH = ROOT / "analysis" / "output" / "tobias_moller_session_results.pdf"


def styled_table(rows: list[list[str]], widths: list[float]) -> Table:
    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f6f78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f4f7f6")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b9c9c6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def main() -> None:
    load_dotenv(ROOT / ".env")
    client = get_supabase_client()
    sessions = client.table("sessions").select("id,participant_code,status,started_at,completed_at").ilike("participant_code", "%Tobias%").execute().data or []
    sessions = [session for session in sessions if session["status"] == "completed"]
    if len(sessions) != 1:
        raise ValueError(f"Expected exactly one completed Tobias session; found {len(sessions)}.")
    session = sessions[0]
    trials = client.table("trials").select("trial_number,condition,experiment_part,raw_response,score,task_data").eq("session_id", session["id"]).order("trial_number").execute().data or []
    if len(trials) != 15:
        raise ValueError(f"Expected 15 completed trials; found {len(trials)}.")

    styles = getSampleStyleSheet()
    title = styles["Title"]
    title.textColor = colors.HexColor("#1f6f78")
    heading = styles["Heading2"]
    heading.textColor = colors.HexColor("#1f6f78")
    body = styles["BodyText"]
    body.leading = 13
    document = SimpleDocTemplate(str(OUTPUT_PATH), pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm, topMargin=14 * mm, bottomMargin=14 * mm)
    story = [
        Paragraph("Human Memory Experiment: Session Results", title),
        Paragraph(f"Participant: <b>{session['participant_code']}</b> &nbsp;&nbsp; Status: <b>Completed</b>", body),
        Spacer(1, 4 * mm),
        Paragraph("Free Recall", heading),
    ]

    free_rows = [["Condition", "Recall", "Primacy", "Middle", "Recency", "Intrusions"]]
    for trial in trials[:4]:
        score = trial["score"]
        groups = score["position_groups"]
        free_rows.append([
            trial["condition"].replace("_", " ").title(),
            f"{score['recalled_count']}/15 ({score['accuracy']:.0%})",
            f"{groups['primacy']['recalled']}/5",
            f"{groups['middle']['recalled']}/5",
            f"{groups['recency']['recalled']}/5",
            ", ".join(score["intrusions"]) or "None",
        ])
    story.extend([styled_table(free_rows, [31 * mm, 28 * mm, 19 * mm, 18 * mm, 20 * mm, 47 * mm]), Spacer(1, 4 * mm), Paragraph("Serial Recall: Capacity", heading)])

    capacity_rows = [["Length", "Positional accuracy", "Whole sequence", "Errors: omission / substitution / transposition"]]
    for trial in trials[4:10]:
        score = trial["score"]
        capacity_rows.append([
            f"{score['presented_length']} digits",
            f"{score['positional_matches']}/{score['presented_length']} ({score['positional_accuracy']:.0%})",
            "Yes" if score["whole_sequence_correct"] else "No",
            f"{score['omissions']} / {score['substitutions']} / {score['transpositions']}",
        ])
    story.extend([styled_table(capacity_rows, [30 * mm, 45 * mm, 33 * mm, 67 * mm]), Spacer(1, 4 * mm), Paragraph("Serial Recall: Experimental Conditions", heading)])

    condition_rows = [["Comparison", "Result", "Change from control/pair"]]
    chunking = {trial["condition"]: trial["score"]["positional_accuracy"] for trial in trials[10:12]}
    secondary = {trial["condition"]: trial["score"]["positional_accuracy"] for trial in trials[12:15]}
    for trial in trials[10:15]:
        score = trial["score"]
        label = trial["condition"].replace("_", " ").title()
        if trial["condition"] == "ungrouped":
            change = "Reference"
        elif trial["condition"] == "grouped":
            change = f"{(chunking['grouped'] - chunking['ungrouped']) * 100:+.1f} percentage points"
        elif trial["condition"] == "control":
            change = "Reference"
        else:
            change = f"{(secondary[trial['condition']] - secondary['control']) * 100:+.1f} percentage points"
        condition_rows.append([label, f"{score['positional_matches']}/{score['presented_length']} ({score['positional_accuracy']:.0%})", change])
    story.extend([styled_table(condition_rows, [54 * mm, 45 * mm, 76 * mm]), Spacer(1, 4 * mm)])
    control = next(trial for trial in trials if trial["condition"] == "control")
    story.extend([
        Paragraph("Interpretation", heading),
        Paragraph(
            "The grouped chunking trial was 11.1 percentage points higher than the ungrouped trial. The three secondary-task results should be interpreted cautiously: the control response was 0/8, so the apparent advantages for articulatory suppression and finger tapping do not support an improvement from those tasks. This is one participant's pilot result, not a group-level conclusion.",
            body,
        ),
        Spacer(1, 3 * mm),
        Paragraph("Prepared from the saved trial scores. Error categories can overlap and are not summed.", styles["Italic"]),
    ])
    document.build(story)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()