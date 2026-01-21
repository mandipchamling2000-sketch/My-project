import re
import pdfplumber

def extract_first_page_lines(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text() or ""
    return [line.strip() for line in text.split("\n") if line.strip()]

def extract_subject(lines):
    for line in lines[:10]:
        m = re.match(r"([A-Z]{3}\s?\d{3})\s*[–-]?\s*(.+)", line)
        if m:
            return f"{m.group(1).replace(' ','')} {m.group(2).strip()}"
    return "Unknown Subject"

def parse_assignments(lines):
    results = []
    current_assignment = None
    current_weight = "—"
    current_due = "—"

    for line in lines:
        l = line.lower()

        # ---- Detect main assignment ----
        if any(k in l for k in [
            "group assessment",
            "individual assessment",
            "practical assessment",
            "case study analysis"
        ]):
            current_assignment = line
            current_weight = "—"
            current_due = "—"
            continue

        # ---- Detect weight/value ----
        w = re.search(r"(weight|value|weightage)\s*[:\-]?\s*(\d+)%?", line, re.I)
        if w:
            current_weight = w.group(2)
            continue

        # ---- Detect due date ----
        d = re.search(r"(due date|deadline|deadlines|Deadlines)\s*[:\-]?\s*(.*)", line, re.I)
        if d:
            date_only = re.search(r"\d{1,2}\s+\w+\s+\d{4}", d.group(2))
            current_due = date_only.group(0) if date_only else d.group(2).strip()
            continue

        # ---- Detect subtasks/components ----
        sub = re.match(r"(.+?)\s*[-:|]\s*(\d+)%?(?:\s*\|\s*(?:due|deadline)?[:\-]?\s*(\d{1,2}\s+\w+\s+\d{4}))?", line, re.I)
        if sub and current_assignment:
            name = sub.group(1).strip()
            weight = sub.group(2).strip() if sub.group(2) else current_weight
            due = sub.group(3).strip() if sub.group(3) else current_due
            results.append({
                "assignment": f"{current_assignment} ({name})",
                "weight": weight,
                "due_date": due
            })
            continue

    # ---- If no subtasks, add main assignment ----
    if current_assignment and not any(r["assignment"].startswith(current_assignment) for r in results):
        results.append({
            "assignment": current_assignment,
            "weight": current_weight,
            "due_date": current_due
        })

    return results

def parse_pdf(pdf_path):
    lines = extract_first_page_lines(pdf_path)
    subject = extract_subject(lines)
    assignments = parse_assignments(lines)
    for r in assignments:
        r["subject"] = subject
    return assignments

