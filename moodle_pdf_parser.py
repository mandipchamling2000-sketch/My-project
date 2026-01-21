import re
import pdfplumber
import pandas as pd
from pathlib import Path

# ----------------------------
# READ FIRST PAGE
# ----------------------------
def extract_lines(pdf):
    with pdfplumber.open(pdf) as p:
        text = p.pages[0].extract_text() if p.pages else ""
    return [l.strip() for l in text.split("\n") if l.strip()]


# ----------------------------
# SUBJECT
# ----------------------------
def extract_subject(lines):
    for line in lines[:10]:
        m = re.match(r"([A-Z]{3}\s?\d{3})\s*[–-]?\s*(.+)", line)
        if m:
            return f"{m.group(1).replace(' ', '')} {m.group(2).strip()}"
    return "Unknown Subject"


# ----------------------------
# DATE
# ----------------------------
def extract_date(text):
    m = re.search(r"(\d{1,2}\s+\w+\s+\d{4})", text)
    return m.group(1) if m else "—"


# ----------------------------
# ASSESSMENT TYPE
# ----------------------------
def detect_assessment_type(lines):
    for l in lines:
        if "group assessment" in l.lower():
            return "Group Assessment"
        if "practical" in l.lower():
            return "Practical Assessment"
        if "individual" in l.lower():
            return "Individual Assessment"
    return "Assessment"


# ----------------------------
# PARSER
# ----------------------------
def parse_assignments(lines):
    results = []
    assessment_type = detect_assessment_type(lines)

    subtask_found = False

    for line in lines:
        # ---- Skip metadata ----
        if re.match(r"(weight|weightage|value)\s*[:\-]", line, re.I):
            continue

        # ---- Subtasks ----
        m = re.match(
            r"(.+?)\s*[-:]\s*(\d+)%\s*(.*)",
            line
        )
        if m:
            name = m.group(1).strip()

            # ignore fake tasks
            if name.lower() in ["weight", "value", "weightage"]:
                continue

            due = extract_date(m.group(3))
            results.append({
                "assignment": f"{assessment_type} ({name})",
                "due_date": due
            })
            subtask_found = True

    # ---- No subtasks → single assignment ----
    if not subtask_found:
        due = "—"
        for l in lines:
            if re.search(r"due date|deadline", l, re.I):
                due = extract_date(l)

        results.append({
            "assignment": assessment_type,
            "due_date": due
        })

    return results


# ----------------------------
# PROCESS PDF
# ----------------------------
def process_pdf(pdf):
    lines = extract_lines(pdf)
    subject = extract_subject(lines)
    rows = parse_assignments(lines)

    for r in rows:
        r["subject"] = subject

    return rows


# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    pdfs = list(Path(".").glob("*.pdf"))
    all_rows = []

    for pdf in pdfs:
        all_rows.extend(process_pdf(pdf))

    df = pd.DataFrame(all_rows)
    df = df[["subject", "assignment", "due_date"]]

    print("\nExtracted Assignment Data:\n")
    print(df)

    df.to_csv("assignments_summary.csv", index=False)
    print("\nSaved to assignments_summary.csv")

