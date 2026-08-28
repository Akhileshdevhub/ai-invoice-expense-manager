# -*- coding: utf-8 -*-
"""Builds the Interview Preparation Guide PDF from content.py + qa_bank.py.

Run: python docs/interview_prep/build_guide.py
Output: docs/interview_prep/Interview_Prep_Guide.pdf
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from content import (
    PITCH_30S, PITCH_2MIN, ARCHITECTURE_TEXT, DATA_FLOW_TEXT,
    CONCEPTS, CODE_WALKTHROUGH, CV_BULLETS,
)
from qa_bank import QA_BANK

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    ListFlowable, ListItem, KeepTogether, HRFlowable,
)

OUT_PATH = Path(__file__).resolve().parent / "Interview_Prep_Guide.pdf"

# DejaVu Sans (unlike reportlab's built-in Helvetica) has a glyph for the
# Rupee sign (₹), which several answers in this guide use — Helvetica
# silently renders it as a black box.
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
pdfmetrics.registerFont(TTFont("DejaVuSans", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique", str(FONT_DIR / "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-BoldOblique", str(FONT_DIR / "DejaVuSans-BoldOblique.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSansMono", str(FONT_DIR / "DejaVuSansMono.ttf")))
pdfmetrics.registerFontFamily(
    "DejaVuSans", normal="DejaVuSans", bold="DejaVuSans-Bold",
    italic="DejaVuSans-Oblique", boldItalic="DejaVuSans-BoldOblique",
)

INK = colors.HexColor("#1a1a1a")
MUTED = colors.HexColor("#5a5a5a")
ACCENT = colors.HexColor("#2f5d8c")
RULE = colors.HexColor("#cfcfcf")
BOX_BG = colors.HexColor("#f3f5f7")

styles = getSampleStyleSheet()

def style(name, parent, **kw):
    s = ParagraphStyle(name, parent=styles[parent], **kw)
    styles.add(s)
    return s

style("DocTitle", "Title", fontSize=25, leading=30, textColor=INK, spaceAfter=6, fontName="DejaVuSans-Bold")
style("DocSubtitle", "Normal", fontSize=12.5, leading=17, textColor=MUTED, spaceAfter=4, fontName="DejaVuSans")
style("H1", "Heading1", fontSize=17, leading=21, textColor=INK, spaceBefore=22, spaceAfter=10,
      borderColor=RULE, borderWidth=0, fontName="DejaVuSans-Bold")
style("H2", "Heading2", fontSize=13, leading=17, textColor=ACCENT, spaceBefore=14, spaceAfter=6, fontName="DejaVuSans-Bold")
style("H3", "Heading3", fontSize=11, leading=14, textColor=INK, spaceBefore=10, spaceAfter=4, fontName="DejaVuSans-Bold")
style("Body", "Normal", fontSize=10, leading=14.5, textColor=INK, spaceAfter=8, alignment=TA_LEFT, fontName="DejaVuSans")
style("BodySmall", "Normal", fontSize=9, leading=13, textColor=MUTED, spaceAfter=6, fontName="DejaVuSans")
style("Mono", "Code", fontSize=8.3, leading=11.5, textColor=INK, backColor=BOX_BG,
      borderPadding=8, spaceAfter=10, fontName="DejaVuSansMono")
style("QALabel", "Normal", fontSize=9, leading=12, textColor=ACCENT, spaceBefore=6, spaceAfter=2,
      fontName="DejaVuSans-Bold")
style("QAQuestion", "Normal", fontSize=11, leading=14, textColor=INK, spaceBefore=10, spaceAfter=4,
      fontName="DejaVuSans-Bold")
style("TOCEntry", "Normal", fontSize=10.5, leading=18, textColor=INK, fontName="DejaVuSans")
style("Cover", "Normal", fontSize=10.5, leading=16, textColor=MUTED, fontName="DejaVuSans")


def rule():
    return HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=2, spaceAfter=10)


def section(title):
    return [Paragraph(title, styles["H1"]), rule()]


def qa_block(item, number):
    flow = [
        Paragraph(f"Q{number}. {item['q']}", styles["QAQuestion"]),
        Paragraph("Short answer", styles["QALabel"]),
        Paragraph(item["short"], styles["Body"]),
        Paragraph("Detailed answer", styles["QALabel"]),
        Paragraph(item["detailed"], styles["Body"]),
        Paragraph("How to say it out loud", styles["QALabel"]),
        Paragraph(item["verbal"], styles["Body"]),
        Paragraph("Likely follow-up", styles["QALabel"]),
        Paragraph(f"<i>{item['follow_up_q']}</i> — {item['follow_up_a']}", styles["Body"]),
    ]
    return KeepTogether(flow) if False else flow  # KeepTogether can overflow a page for long Q&As; let them flow naturally


def code_file_block(entry):
    rows = [
        ["File", entry["file"]],
        ["Purpose", entry["purpose"]],
        ["Key functions", entry["functions"]],
        ["Inputs", entry["inputs"]],
        ["Outputs", entry["outputs"]],
        ["Logic", entry["logic"]],
        ["Design decision", entry["design_decision"]],
        ["Failure cases", entry["failure_cases"]],
        ["Likely question", entry["interview_question"]],
    ]
    table_data = []
    for label, value in rows:
        table_data.append([
            Paragraph(f"<b>{label}</b>", styles["BodySmall"]),
            Paragraph(value, styles["Body"]),
        ])
    t = Table(table_data, colWidths=[1.15 * inch, 5.15 * inch])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build():
    doc = SimpleDocTemplate(
        str(OUT_PATH), pagesize=letter,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.85 * inch, rightMargin=0.85 * inch,
        title="AI Invoice & Expense Manager — Interview Preparation Guide",
        author="Akhilesh",
    )

    story = []

    # ---- Cover ----
    story.append(Spacer(1, 1.6 * inch))
    story.append(Paragraph("AI Invoice &amp; Expense Manager", styles["DocTitle"]))
    story.append(Paragraph("Technical &amp; Interview Preparation Guide", styles["DocSubtitle"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(rule())
    story.append(Paragraph(
        "This guide is meant to teach the project well enough to defend it in an "
        "interview — not just describe what it does, but explain every design "
        "decision, every honest limitation, and every tradeoff. It intentionally "
        "matches the codebase: nothing here describes a technology or technique "
        "that isn't actually implemented in this repository.",
        styles["Cover"],
    ))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "Scope note: rather than a mechanically generated 220-question bank "
        "(20 questions x 11 categories), this guide has a curated ~65 questions "
        "across 10 categories, each at full depth. A shorter guide that gets "
        "actually studied beats a longer one that doesn't — the same principle "
        "the project itself applies to scope (see README, \"Engineering quality "
        "over number of features\").",
        styles["Cover"],
    ))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("Author: Akhilesh &nbsp;&nbsp;|&nbsp;&nbsp; Project: ai-invoice-expense-manager", styles["Cover"]))
    story.append(PageBreak())

    # ---- 1. Elevator pitches ----
    story += section("1. Elevator Pitches")
    story.append(Paragraph("30-second explanation (memorize this)", styles["H2"]))
    story.append(Paragraph(PITCH_30S, styles["Body"]))
    story.append(Paragraph("2-minute explanation", styles["H2"]))
    for para in PITCH_2MIN.split("\n\n"):
        story.append(Paragraph(para, styles["Body"]))
    story.append(PageBreak())

    # ---- 2. Architecture & data flow ----
    story += section("2. Full Architecture")
    story.append(Paragraph(ARCHITECTURE_TEXT, styles["Body"]))
    story.append(Paragraph("End-to-End Data Flow", styles["H2"]))
    story.append(Paragraph(DATA_FLOW_TEXT, styles["Mono"]))
    story.append(PageBreak())

    # ---- 3. Concepts ----
    story += section("3. Concepts by Area")
    concept_order = ["OCR", "NLP", "ML", "Analytics", "Database", "LLM", "Security", "Testing", "Deployment"]
    for name in concept_order:
        story.append(Paragraph(name, styles["H2"]))
        story.append(Paragraph(CONCEPTS[name], styles["Body"]))
    story.append(PageBreak())

    # ---- 4. Code walkthrough ----
    story += section("4. Code Walkthrough — Major Files")
    story.append(Paragraph(
        "For each file: purpose, key functions, inputs/outputs, the important "
        "logic, the design decision behind it, real failure cases, and a "
        "question likely to come up about it.",
        styles["BodySmall"],
    ))
    for entry in CODE_WALKTHROUGH:
        story.append(Paragraph(entry["file"], styles["H3"]))
        story.append(code_file_block(entry))
        story.append(Spacer(1, 10))
    story.append(PageBreak())

    # ---- 5. Interview Q&A ----
    story += section("5. Interview Questions & Answers")
    story.append(Paragraph(
        "Organized by category. Each question has a short answer, a detailed "
        "answer, guidance on how to say it out loud, and a likely follow-up.",
        styles["BodySmall"],
    ))
    for category, items in QA_BANK.items():
        story.append(PageBreak())
        story.append(Paragraph(category, styles["H2"]))
        for i, item in enumerate(items, 1):
            story += qa_block(item, i)

    story.append(PageBreak())

    # ---- 6. CV bullet points ----
    story += section("6. CV / Resume Bullet Points")
    story.append(Paragraph(
        "Three versions for different audiences. All are truthful to what was "
        "actually built and measured — no invented users, accuracy figures, or "
        "business impact.",
        styles["BodySmall"],
    ))
    for label, bullets in CV_BULLETS.items():
        story.append(Paragraph(f"{label} version", styles["H2"]))
        items = [ListItem(Paragraph(b, styles["Body"]), leftIndent=6) for b in bullets]
        story.append(ListFlowable(items, bulletType="bullet", start="•"))
    story.append(PageBreak())

    # ---- 7. Revision checklist ----
    story += section("7. Concepts to Revise Before an Interview")
    revise_items = [
        "Why the confirmation gate exists and exactly which function enforces it (repository.confirm_transaction).",
        "The amount extraction priority order (labeled total > fallback largest number) and why the fallback is flagged.",
        "The date-parsing bug (dateutil dayfirst on ISO dates) — a concrete story of a real bug found and fixed.",
        "Why rule-based categorization is the default, not the ML classifier — and what would change that.",
        "What TF-IDF, precision/recall/F1, and a confusion matrix each mean, using this project's actual numbers.",
        "The exact mechanism preventing LLM hallucination (template answer computed before any LLM call; prompt says 'do not alter numbers'; exception fallback).",
        "Why the query intent parser is rule-based, not LLM-based, and its real vocabulary limits.",
        "The database schema, the one composite index, and why no ORM.",
        "What is NOT tested (live OpenAI key, full-pipeline automation, UI integration) — stated honestly, not glossed over.",
        "The three CV bullet versions — know which one fits which conversation.",
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(t, styles["Body"]), leftIndent=6) for t in revise_items],
        bulletType="bullet", start="•",
    ))

    doc.build(story)
    print(f"Built {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    build()
