
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    abort
)

import json
import sqlite3
from pathlib import Path
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether
)

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "skillbridge.db"

# Load career skills
with open(BASE_DIR / "skills.json", encoding="utf-8") as file:
    JOB_SKILLS = json.load(file)


# -----------------------------
# Database connection
# -----------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Initialize database
# -----------------------------
def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                selected_skills TEXT NOT NULL,
                match_percentage INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# -----------------------------
# Calculate skill match
# -----------------------------
def calculate_match(role, selected_skills):
    required = JOB_SKILLS[role]

    selected = set(selected_skills)

    matched = [
        skill for skill in required
        if skill in selected
    ]

    missing = [
        skill for skill in required
        if skill not in selected
    ]

    percentage = (
        round(len(matched) / len(required) * 100)
        if required else 0
    )

    return matched, missing, percentage


# -----------------------------
# Homepage
# -----------------------------
@app.route("/")
def home():
    all_skills = sorted({
        skill
        for skills in JOB_SKILLS.values()
        for skill in skills
    })

    return render_template(
        "index.html",
        roles=JOB_SKILLS.keys(),
        all_skills=all_skills,
        job_skills=JOB_SKILLS
    )


# -----------------------------
# Analyze skills
# -----------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    role = request.form.get("role")
    selected_skills = request.form.getlist("skills")

    if role not in JOB_SKILLS:
        return redirect(url_for("home"))

    valid_skills = {
        skill
        for skills in JOB_SKILLS.values()
        for skill in skills
    }

    selected_skills = sorted(
        set(selected_skills) & valid_skills
    )

    matched, missing, percentage = calculate_match(
        role, selected_skills
    )

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analyses
            (role, selected_skills, match_percentage)
            VALUES (?, ?, ?)
            """,
            (
                role,
                json.dumps(selected_skills),
                percentage
            )
        )

        analysis_id = cursor.lastrowid

    return redirect(
        url_for("dashboard", analysis_id=analysis_id)
    )


# -----------------------------
# Analysis dashboard
# -----------------------------
@app.route("/dashboard/<int:analysis_id>")
def dashboard(analysis_id):
    with get_connection() as conn:
        analysis = conn.execute(
            "SELECT * FROM analyses WHERE id = ?",
            (analysis_id,)
        ).fetchone()

    if analysis is None:
        abort(404)

    role = analysis["role"]

    if role not in JOB_SKILLS:
        abort(404)

    selected_skills = json.loads(
        analysis["selected_skills"]
    )

    matched, missing, percentage = calculate_match(
        role, selected_skills
    )

    return render_template(
        "dashboard.html",
        role=role,
        matched=matched,
        missing=missing,
        percentage=percentage,
        analysis_id=analysis_id
    )


# -----------------------------
# Analysis history
# -----------------------------
@app.route("/history")
def history():
    with get_connection() as conn:
        analyses = conn.execute(
            """
            SELECT *
            FROM analyses
            ORDER BY id DESC
            """
        ).fetchall()

    return render_template(
        "history.html",
        analyses=analyses
    )


# -----------------------------
# Generate PDF report
# -----------------------------
def generate_pdf_report(
    analysis_id,
    role,
    matched,
    missing,
    percentage,
    created_at
):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=(595.28, 841.89),
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitleCustom",
            parent=styles["Title"],
            fontSize=23,
            leading=29,
            textColor=colors.HexColor("#173B80"),
            spaceAfter=14
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportHeadingCustom",
            parent=styles["Heading2"],
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#173B80"),
            spaceBefore=15,
            spaceAfter=9
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportBodyCustom",
            parent=styles["BodyText"],
            fontSize=10,
            leading=16,
            spaceAfter=7
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportCenterCustom",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            fontSize=10,
            leading=16
        )
    )

    story = []

    # Title
    story.append(
        Paragraph(
            "SkillBridge",
            styles["ReportTitleCustom"]
        )
    )

    story.append(
        Paragraph(
            "PERSONALIZED SKILL ANALYSIS REPORT",
            styles["ReportCenterCustom"]
        )
    )

    story.append(Spacer(1, 20))

    # Report details
    details = [
        ["Analysis ID", str(analysis_id)],
        ["Target Career", role],
        ["Analysis Date", str(created_at)],
        ["Skill Match", f"{percentage}%"]
    ]

    details_table = Table(
        details,
        colWidths=[135, 360],
        hAlign="LEFT"
    )

    details_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#EAF1FF")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, -1),
                colors.HexColor("#1F2937")
            ),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            (
                "LINEBELOW",
                (0, 0),
                (-1, -2),
                0.4,
                colors.HexColor("#E5E7EB")
            )
        ])
    )

    story.append(details_table)

    # Summary
    story.append(
        Paragraph(
            "Skill Assessment Summary",
            styles["ReportHeadingCustom"]
        )
    )

    summary = [
        ["Matched Skills", "Missing Skills", "Match Percentage"],
        [
            str(len(matched)),
            str(len(missing)),
            f"{percentage}%"
        ]
    ]

    summary_table = Table(
        summary,
        colWidths=[165, 165, 165]
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#173B80")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            (
                "BACKGROUND",
                (0, 1),
                (-1, 1),
                colors.HexColor("#F3F6FC")
            )
        ])
    )

    story.append(summary_table)

    # Matched skills
    story.append(
        Paragraph(
            "Skills You Already Have",
            styles["ReportHeadingCustom"]
        )
    )

    if matched:
        for skill in matched:
            story.append(
                Paragraph(
                    "&#8226; " + escape(skill),
                    styles["ReportBodyCustom"]
                )
            )
    else:
        story.append(
            Paragraph(
                "No matching skills were selected.",
                styles["ReportBodyCustom"]
            )
        )

    # Missing skills
    story.append(
        Paragraph(
            "Skills to Improve",
            styles["ReportHeadingCustom"]
        )
    )

    if missing:
        for skill in missing:
            story.append(
                Paragraph(
                    "&#8226; " + escape(skill),
                    styles["ReportBodyCustom"]
                )
            )
    else:
        story.append(
            Paragraph(
                "All listed skills have been matched.",
                styles["ReportBodyCustom"]
            )
        )

    # Learning roadmap
    story.append(
        Paragraph(
            "Personalized Learning Roadmap",
            styles["ReportHeadingCustom"]
        )
    )

    if missing:
        for index, skill in enumerate(missing, start=1):
            step = [
                Paragraph(
                    f"<b>Step {index}: Learn {escape(skill)}</b>",
                    styles["ReportBodyCustom"]
                ),
                Paragraph(
                    "Study the fundamentals, practice with "
                    "exercises, and complete a hands-on "
                    "mini-project to demonstrate this skill.",
                    styles["ReportBodyCustom"]
                )
            ]

            story.append(KeepTogether(step))
            story.append(Spacer(1, 8))
    else:
        story.append(
            Paragraph(
                "Build a portfolio project to demonstrate "
                "your skills and continue learning.",
                styles["ReportBodyCustom"]
            )
        )

    # Disclaimer
    story.append(Spacer(1, 18))

    story.append(
        Paragraph(
            "This report compares self-reported skills "
            "against SkillBridge's example role requirements. "
            "It is not a verified professional assessment.",
            styles["ReportBodyCustom"]
        )
    )

    # Footer on each page
    def draw_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(
            colors.HexColor("#6B7280")
        )
        canvas.drawString(
            45,
            25,
            "SkillBridge | Career Intelligence"
        )
        canvas.drawRightString(
            550,
            25,
            f"Page {doc.page}"
        )
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer
    )

    buffer.seek(0)
    return buffer


# -----------------------------
# Download PDF report
# -----------------------------
@app.route("/download-report/<int:analysis_id>")
def download_report(analysis_id):
    with get_connection() as conn:
        analysis = conn.execute(
            "SELECT * FROM analyses WHERE id = ?",
            (analysis_id,)
        ).fetchone()

    if analysis is None:
        abort(404)

    role = analysis["role"]

    if role not in JOB_SKILLS:
        abort(404)

    selected_skills = json.loads(
        analysis["selected_skills"]
    )

    matched, missing, percentage = calculate_match(
        role,
        selected_skills
    )

    pdf_buffer = generate_pdf_report(
        analysis_id=analysis_id,
        role=role,
        matched=matched,
        missing=missing,
        percentage=percentage,
        created_at=analysis["created_at"]
    )

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"SkillBridge_Report_{analysis_id}.pdf",
        mimetype="application/pdf"
    )


# -----------------------------
# Run application
# -----------------------------
init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    abort
)

import json
import sqlite3
from pathlib import Path
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether
)

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "skillbridge.db"

# Load career skills
with open(BASE_DIR / "skills.json", encoding="utf-8") as file:
    JOB_SKILLS = json.load(file)


# -----------------------------
# Database connection
# -----------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Initialize database
# -----------------------------
def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                selected_skills TEXT NOT NULL,
                match_percentage INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# -----------------------------
# Calculate skill match
# -----------------------------
def calculate_match(role, selected_skills):
    required = JOB_SKILLS[role]

    selected = set(selected_skills)

    matched = [
        skill for skill in required
        if skill in selected
    ]

    missing = [
        skill for skill in required
        if skill not in selected
    ]

    percentage = (
        round(len(matched) / len(required) * 100)
        if required else 0
    )

    return matched, missing, percentage


# -----------------------------
# Homepage
# -----------------------------
@app.route("/")
def home():
    all_skills = sorted({
        skill
        for skills in JOB_SKILLS.values()
        for skill in skills
    })

    return render_template(
        "index.html",
        roles=JOB_SKILLS.keys(),
        all_skills=all_skills,
        job_skills=JOB_SKILLS
    )


# -----------------------------
# Analyze skills
# -----------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    role = request.form.get("role")
    selected_skills = request.form.getlist("skills")

    if role not in JOB_SKILLS:
        return redirect(url_for("home"))

    valid_skills = {
        skill
        for skills in JOB_SKILLS.values()
        for skill in skills
    }

    selected_skills = sorted(
        set(selected_skills) & valid_skills
    )

    matched, missing, percentage = calculate_match(
        role, selected_skills
    )

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analyses
            (role, selected_skills, match_percentage)
            VALUES (?, ?, ?)
            """,
            (
                role,
                json.dumps(selected_skills),
                percentage
            )
        )

        analysis_id = cursor.lastrowid

    return redirect(
        url_for("dashboard", analysis_id=analysis_id)
    )


# -----------------------------
# Analysis dashboard
# -----------------------------
@app.route("/dashboard/<int:analysis_id>")
def dashboard(analysis_id):
    with get_connection() as conn:
        analysis = conn.execute(
            "SELECT * FROM analyses WHERE id = ?",
            (analysis_id,)
        ).fetchone()

    if analysis is None:
        abort(404)

    role = analysis["role"]

    if role not in JOB_SKILLS:
        abort(404)

    selected_skills = json.loads(
        analysis["selected_skills"]
    )

    matched, missing, percentage = calculate_match(
        role, selected_skills
    )

    return render_template(
        "dashboard.html",
        role=role,
        matched=matched,
        missing=missing,
        percentage=percentage,
        analysis_id=analysis_id
    )


# -----------------------------
# Analysis history
# -----------------------------
@app.route("/history")
def history():
    with get_connection() as conn:
        analyses = conn.execute(
            """
            SELECT *
            FROM analyses
            ORDER BY id DESC
            """
        ).fetchall()

    return render_template(
        "history.html",
        analyses=analyses
    )


# -----------------------------
# Generate PDF report
# -----------------------------
def generate_pdf_report(
    analysis_id,
    role,
    matched,
    missing,
    percentage,
    created_at
):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=(595.28, 841.89),
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitleCustom",
            parent=styles["Title"],
            fontSize=23,
            leading=29,
            textColor=colors.HexColor("#173B80"),
            spaceAfter=14
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportHeadingCustom",
            parent=styles["Heading2"],
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#173B80"),
            spaceBefore=15,
            spaceAfter=9
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportBodyCustom",
            parent=styles["BodyText"],
            fontSize=10,
            leading=16,
            spaceAfter=7
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportCenterCustom",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            fontSize=10,
            leading=16
        )
    )

    story = []

    # Title
    story.append(
        Paragraph(
            "SkillBridge",
            styles["ReportTitleCustom"]
        )
    )

    story.append(
        Paragraph(
            "PERSONALIZED SKILL ANALYSIS REPORT",
            styles["ReportCenterCustom"]
        )
    )

    story.append(Spacer(1, 20))

    # Report details
    details = [
        ["Analysis ID", str(analysis_id)],
        ["Target Career", role],
        ["Analysis Date", str(created_at)],
        ["Skill Match", f"{percentage}%"]
    ]

    details_table = Table(
        details,
        colWidths=[135, 360],
        hAlign="LEFT"
    )

    details_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#EAF1FF")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, -1),
                colors.HexColor("#1F2937")
            ),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            (
                "LINEBELOW",
                (0, 0),
                (-1, -2),
                0.4,
                colors.HexColor("#E5E7EB")
            )
        ])
    )

    story.append(details_table)

    # Summary
    story.append(
        Paragraph(
            "Skill Assessment Summary",
            styles["ReportHeadingCustom"]
        )
    )

    summary = [
        ["Matched Skills", "Missing Skills", "Match Percentage"],
        [
            str(len(matched)),
            str(len(missing)),
            f"{percentage}%"
        ]
    ]

    summary_table = Table(
        summary,
        colWidths=[165, 165, 165]
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#173B80")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            (
                "BACKGROUND",
                (0, 1),
                (-1, 1),
                colors.HexColor("#F3F6FC")
            )
        ])
    )

    story.append(summary_table)

    # Matched skills
    story.append(
        Paragraph(
            "Skills You Already Have",
            styles["ReportHeadingCustom"]
        )
    )

    if matched:
        for skill in matched:
            story.append(
                Paragraph(
                    "&#8226; " + escape(skill),
                    styles["ReportBodyCustom"]
                )
            )
    else:
        story.append(
            Paragraph(
                "No matching skills were selected.",
                styles["ReportBodyCustom"]
            )
        )

    # Missing skills
    story.append(
        Paragraph(
            "Skills to Improve",
            styles["ReportHeadingCustom"]
        )
    )

    if missing:
        for skill in missing:
            story.append(
                Paragraph(
                    "&#8226; " + escape(skill),
                    styles["ReportBodyCustom"]
                )
            )
    else:
        story.append(
            Paragraph(
                "All listed skills have been matched.",
                styles["ReportBodyCustom"]
            )
        )

    # Learning roadmap
    story.append(
        Paragraph(
            "Personalized Learning Roadmap",
            styles["ReportHeadingCustom"]
        )
    )

    if missing:
        for index, skill in enumerate(missing, start=1):
            step = [
                Paragraph(
                    f"<b>Step {index}: Learn {escape(skill)}</b>",
                    styles["ReportBodyCustom"]
                ),
                Paragraph(
                    "Study the fundamentals, practice with "
                    "exercises, and complete a hands-on "
                    "mini-project to demonstrate this skill.",
                    styles["ReportBodyCustom"]
                )
            ]

            story.append(KeepTogether(step))
            story.append(Spacer(1, 8))
    else:
        story.append(
            Paragraph(
                "Build a portfolio project to demonstrate "
                "your skills and continue learning.",
                styles["ReportBodyCustom"]
            )
        )

    # Disclaimer
    story.append(Spacer(1, 18))

    story.append(
        Paragraph(
            "This report compares self-reported skills "
            "against SkillBridge's example role requirements. "
            "It is not a verified professional assessment.",
            styles["ReportBodyCustom"]
        )
    )

    # Footer on each page
    def draw_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(
            colors.HexColor("#6B7280")
        )
        canvas.drawString(
            45,
            25,
            "SkillBridge | Career Intelligence"
        )
        canvas.drawRightString(
            550,
            25,
            f"Page {doc.page}"
        )
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer
    )

    buffer.seek(0)
    return buffer


# -----------------------------
# Download PDF report
# -----------------------------
@app.route("/download-report/<int:analysis_id>")
def download_report(analysis_id):
    with get_connection() as conn:
        analysis = conn.execute(
            "SELECT * FROM analyses WHERE id = ?",
            (analysis_id,)
        ).fetchone()

    if analysis is None:
        abort(404)

    role = analysis["role"]

    if role not in JOB_SKILLS:
        abort(404)

    selected_skills = json.loads(
        analysis["selected_skills"]
    )

    matched, missing, percentage = calculate_match(
        role,
        selected_skills
    )

    pdf_buffer = generate_pdf_report(
        analysis_id=analysis_id,
        role=role,
        matched=matched,
        missing=missing,
        percentage=percentage,
        created_at=analysis["created_at"]
    )

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"SkillBridge_Report_{analysis_id}.pdf",
        mimetype="application/pdf"
    )


# -----------------------------
# Run application
# -----------------------------

init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5001)

