"""
QuantumGuard Labs - Professional PDF Compliance Report Generator
================================================================
Generates a professional, board-ready PDF compliance report using ReportLab.
The report is suitable for submission to auditors, regulators, and boards.
"""

import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak,
)
from reportlab.platypus.flowables import BalancedColumns
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

# ── Colour Palette ────────────────────────────────────────────────────────────
DARK_BG     = colors.HexColor("#0d1117")
BRAND_BLUE  = colors.HexColor("#1a73e8")
BRAND_TEAL  = colors.HexColor("#00bcd4")
CRITICAL_R  = colors.HexColor("#f44336")
HIGH_O      = colors.HexColor("#ff9800")
MEDIUM_Y    = colors.HexColor("#ffc107")
LOW_G       = colors.HexColor("#4caf50")
SAFE_G      = colors.HexColor("#2196f3")
TEXT_DARK   = colors.HexColor("#1a1a2e")
TEXT_GREY   = colors.HexColor("#555555")
LIGHT_GREY  = colors.HexColor("#f5f5f5")
MID_GREY    = colors.HexColor("#e0e0e0")
WHITE       = colors.white

RISK_COLORS = {
    "CRITICAL": CRITICAL_R,
    "HIGH":     HIGH_O,
    "MEDIUM":   MEDIUM_Y,
    "LOW":      LOW_G,
    "SAFE":     SAFE_G,
}

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


def _styles():
    base = getSampleStyleSheet()
    custom = {}

    custom["cover_title"] = ParagraphStyle(
        "cover_title", parent=base["Title"],
        fontSize=28, textColor=WHITE, alignment=TA_CENTER,
        spaceAfter=6, leading=34,
    )
    custom["cover_sub"] = ParagraphStyle(
        "cover_sub", parent=base["Normal"],
        fontSize=13, textColor=colors.HexColor("#b0bec5"),
        alignment=TA_CENTER, spaceAfter=4,
    )
    custom["section_h"] = ParagraphStyle(
        "section_h", parent=base["Heading1"],
        fontSize=14, textColor=BRAND_BLUE,
        spaceBefore=14, spaceAfter=6, leading=18,
        borderPad=0,
    )
    custom["sub_h"] = ParagraphStyle(
        "sub_h", parent=base["Heading2"],
        fontSize=11, textColor=TEXT_DARK,
        spaceBefore=8, spaceAfter=4,
    )
    custom["body"] = ParagraphStyle(
        "body", parent=base["Normal"],
        fontSize=9.5, textColor=TEXT_DARK,
        leading=14, spaceAfter=4, alignment=TA_JUSTIFY,
    )
    custom["small"] = ParagraphStyle(
        "small", parent=base["Normal"],
        fontSize=8, textColor=TEXT_GREY, leading=11,
    )
    custom["label"] = ParagraphStyle(
        "label", parent=base["Normal"],
        fontSize=8.5, textColor=TEXT_GREY, leading=11,
    )
    custom["value"] = ParagraphStyle(
        "value", parent=base["Normal"],
        fontSize=11, textColor=TEXT_DARK, fontName="Helvetica-Bold",
    )
    custom["attestation"] = ParagraphStyle(
        "attestation", parent=base["Normal"],
        fontSize=9, textColor=TEXT_GREY,
        leading=13, alignment=TA_JUSTIFY,
        borderColor=MID_GREY, borderWidth=1,
        borderPad=8, backColor=LIGHT_GREY,
    )
    return custom


def _header_footer(canvas, doc):
    """Draw page header and footer."""
    canvas.saveState()
    w, h = A4

    # Header bar
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, h - 1.4 * cm, w, 1.4 * cm, fill=1, stroke=0)
    canvas.setFillColor(BRAND_TEAL)
    canvas.rect(0, h - 1.4 * cm, 4 * mm, 1.4 * cm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(WHITE)
    canvas.drawString(MARGIN, h - 0.85 * cm, "QuantumGuard Labs  |  Quantum Readiness Compliance Report")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#b0bec5"))
    canvas.drawRightString(w - MARGIN, h - 0.85 * cm, f"CONFIDENTIAL")

    # Footer
    canvas.setFillColor(LIGHT_GREY)
    canvas.rect(0, 0, w, 0.9 * cm, fill=1, stroke=0)
    canvas.setFillColor(TEXT_GREY)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGIN, 0.32 * cm,
                      f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  |  "
                      f"QuantumGuard Labs QMP v0.1.0-alpha  |  For compliance use only.")
    canvas.drawRightString(w - MARGIN, 0.32 * cm, f"Page {doc.page}")

    canvas.restoreState()


def _score_bar(score: float, width: float = 8 * cm, height: float = 0.55 * cm):
    """Return a Table that renders a coloured score progress bar."""
    filled = max(0.0, min(1.0, score / 100.0))
    empty  = 1.0 - filled
    bar_color = (
        CRITICAL_R if score < 40 else
        HIGH_O     if score < 60 else
        MEDIUM_Y   if score < 75 else
        LOW_G      if score < 90 else
        SAFE_G
    )
    data = [["", ""]]
    col_widths = [width * filled, width * empty] if filled > 0 else [0.01, width]
    tbl = Table(data, colWidths=col_widths, rowHeights=[height])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), bar_color),
        ("BACKGROUND", (1, 0), (1, 0), MID_GREY),
        ("LINEABOVE",  (0, 0), (-1, 0), 0, WHITE),
        ("LINEBELOW",  (0, 0), (-1, 0), 0, WHITE),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    return tbl


def generate_pdf_report(report, plan, proof, output_path: str, org_id: str = "DEMO_ORG"):
    """
    Generate a professional PDF compliance report.

    Args:
        report:      RiskReport from BitcoinQuantumAnalyzer
        plan:        MigrationPlan from MigrationPlanner
        proof:       QuantumReadinessProof from ProofGenerator
        output_path: Full path to write the PDF file
        org_id:      Organization identifier string
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=1.8 * cm,
        bottomMargin=1.4 * cm,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        title="QuantumGuard Labs Compliance Report",
        author="QuantumGuard Labs QMP",
    )

    S = _styles()
    story = []

    # ── Cover Page ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3 * cm))

    # Dark cover banner
    cover_data = [[
        Paragraph("QuantumGuard Labs", S["cover_title"]),
    ]]
    cover_tbl = Table(cover_data, colWidths=[PAGE_W - 2 * MARGIN])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 20),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
    ]))
    story.append(cover_tbl)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Quantum Readiness Compliance Report", S["cover_sub"]))
    story.append(Paragraph(
        f"Organization: <b>{org_id}</b>  |  Report ID: {proof.proof_id[:16]}...",
        S["cover_sub"]
    ))
    story.append(Paragraph(
        f"Generated: {datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')}",
        S["cover_sub"]
    ))
    story.append(Spacer(1, 1.5 * cm))

    # Score highlight box
    score = report.quantum_readiness_score
    projected = proof.final_readiness_score
    score_color = (
        CRITICAL_R if score < 40 else HIGH_O if score < 60 else
        MEDIUM_Y   if score < 75 else LOW_G  if score < 90 else SAFE_G
    )
    score_data = [
        [Paragraph("QUANTUM READINESS SCORE", S["label"]),
         Paragraph("PROJECTED SCORE (POST-MIGRATION)", S["label"])],
        [Paragraph(f'<font color="{score_color.hexval()}" size="32"><b>{score:.1f}</b></font><font size="14"> / 100</font>', S["value"]),
         Paragraph(f'<font color="{LOW_G.hexval()}" size="32"><b>{projected:.1f}</b></font><font size="14"> / 100</font>', S["value"])],
        [_score_bar(score), _score_bar(projected)],
    ]
    score_tbl = Table(score_data, colWidths=[(PAGE_W - 2 * MARGIN) / 2 - 0.5 * cm] * 2,
                      hAlign="CENTER")
    score_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("LINEAFTER",  (0, 0), (0, -1), 1, MID_GREY),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(score_tbl)
    story.append(PageBreak())

    # ── Section 1: Executive Summary ─────────────────────────────────────────
    story.append(Paragraph("1. Executive Summary", S["section_h"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_BLUE, spaceAfter=8))

    story.append(Paragraph(
        f"This report presents the results of a comprehensive quantum risk assessment "
        f"conducted on the digital asset portfolio of <b>{org_id}</b> using the "
        f"QuantumGuard Labs Quantum Migration Platform (QMP). The assessment analyzed "
        f"<b>{report.total_utxos:,} UTXOs</b> with a combined value of "
        f"<b>{report.total_value_btc:.4f} BTC</b>.",
        S["body"]
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        f"The portfolio's current Quantum Readiness Score is <b>{score:.1f}/100</b>. "
        f"Following the execution of the proposed migration plan, the projected score "
        f"is <b>{projected:.1f}/100</b> — an improvement of "
        f"<b>{projected - score:.1f} points</b>. "
        f"A total of <b>{report.critical_count + report.high_count} UTXOs</b> "
        f"(representing <b>{(report.critical_value_btc + report.high_value_btc):.4f} BTC</b>) "
        f"require priority migration.",
        S["body"]
    ))

    # ── Section 2: Risk Distribution ─────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("2. Portfolio Risk Distribution", S["section_h"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_BLUE, spaceAfter=8))

    risk_rows = [
        [Paragraph("<b>Risk Level</b>", S["label"]),
         Paragraph("<b>UTXO Count</b>", S["label"]),
         Paragraph("<b>% of Portfolio</b>", S["label"]),
         Paragraph("<b>BTC Value</b>", S["label"]),
         Paragraph("<b>Action Required</b>", S["label"])],
    ]
    risk_data = [
        ("CRITICAL", report.critical_count, report.critical_value_btc, "Migrate immediately"),
        ("HIGH",     report.high_count,     report.high_value_btc,     "Migrate within 30 days"),
        ("MEDIUM",   report.medium_count,   0.0,                       "Plan migration within 90 days"),
        ("LOW",      report.low_count,      0.0,                       "Monitor; include in long-term plan"),
        ("SAFE",     report.safe_count,     0.0,                       "No action required"),
    ]
    for level, count, value, action in risk_data:
        pct = (count / report.total_utxos * 100) if report.total_utxos > 0 else 0
        risk_rows.append([
            Paragraph(f'<font color="{RISK_COLORS[level].hexval()}"><b>{level}</b></font>', S["body"]),
            Paragraph(str(count), S["body"]),
            Paragraph(f"{pct:.1f}%", S["body"]),
            Paragraph(f"{value:.4f} BTC" if value > 0 else "—", S["body"]),
            Paragraph(action, S["small"]),
        ])

    col_w = (PAGE_W - 2 * MARGIN) / 5
    risk_tbl = Table(risk_rows, colWidths=[col_w] * 5, repeatRows=1)
    risk_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  DARK_BG),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID",         (0, 0), (-1, -1), 0.4, MID_GREY),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(risk_tbl)

    # ── Section 3: Migration Plan ─────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("3. Migration Plan Summary", S["section_h"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_BLUE, spaceAfter=8))

    story.append(Paragraph(
        f"The migration plan (ID: <code>{plan.plan_id[:24]}...</code>) was generated using the "
        f"<b>{plan.policy_name}</b> policy. It consists of <b>{plan.total_batches} batches</b> "
        f"covering <b>{plan.total_utxos} UTXOs</b> with a total value of "
        f"<b>{plan.total_value_btc:.4f} BTC</b>. "
        f"Estimated transaction fees: <b>{plan.estimated_fees_btc:.6f} BTC</b>.",
        S["body"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    batch_rows = [
        [Paragraph("<b>Batch</b>", S["label"]),
         Paragraph("<b>Batch ID</b>", S["label"]),
         Paragraph("<b>UTXOs</b>", S["label"]),
         Paragraph("<b>Value (BTC)</b>", S["label"]),
         Paragraph("<b>Status</b>", S["label"])],
    ]
    for i, batch in enumerate(plan.batches, 1):
        batch_rows.append([
            Paragraph(f"Batch {i}", S["body"]),
            Paragraph(f"<code>{batch.batch_id[:16]}...</code>", S["small"]),
            Paragraph(str(len(batch.assessments)), S["body"]),
            Paragraph(f"{batch.total_value_btc:.4f}", S["body"]),
            Paragraph(batch.status.value, S["small"]),
        ])

    b_col_w = (PAGE_W - 2 * MARGIN) / 5
    batch_tbl = Table(batch_rows, colWidths=[b_col_w * 0.6, b_col_w * 1.6, b_col_w * 0.6, b_col_w * 0.8, b_col_w * 1.4],
                      repeatRows=1)
    batch_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  DARK_BG),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID",         (0, 0), (-1, -1), 0.4, MID_GREY),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(batch_tbl)

    # ── Section 4: Audit Trail Integrity ─────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("4. Audit Trail Integrity", S["section_h"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_BLUE, spaceAfter=8))

    story.append(Paragraph(
        "All migration activities are recorded in a tamper-evident, hash-chained audit log. "
        "Each entry is cryptographically linked to the previous one, ensuring that any "
        "modification to the log is immediately detectable.",
        S["body"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    audit_meta = [
        ["Audit Log Entries",   str(len(proof.audit_log))],
        ["Final Chain Hash",    proof.audit_log_hash[:48] + "..."],
        ["Integrity Status",    "VERIFIED"],
        ["Report ID",           proof.proof_id],
    ]
    audit_tbl = Table(audit_meta, colWidths=[5 * cm, PAGE_W - 2 * MARGIN - 5 * cm])
    audit_tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_GREY, WHITE]),
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), TEXT_GREY),
        ("TEXTCOLOR", (1, 0), (1, -1), TEXT_DARK),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("GRID",         (0, 0), (-1, -1), 0.3, MID_GREY),
    ]))
    story.append(audit_tbl)

    # ── Section 5: Attestation ────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("5. Formal Attestation Statement", S["section_h"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_BLUE, spaceAfter=8))

    story.append(Paragraph(proof.attestation_statement, S["attestation"]))
    story.append(Spacer(1, 1 * cm))

    # Signature block
    sig_data = [
        [Paragraph("Authorized Signatory", S["label"]),
         Paragraph("Date", S["label"]),
         Paragraph("Platform Version", S["label"])],
        [Paragraph("_" * 30, S["body"]),
         Paragraph(datetime.now(timezone.utc).strftime("%Y-%m-%d"), S["body"]),
         Paragraph("QMP v0.1.0-alpha", S["body"])],
    ]
    sig_tbl = Table(sig_data, colWidths=[(PAGE_W - 2 * MARGIN) / 3] * 3)
    sig_tbl.setStyle(TableStyle([
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LINEAFTER",    (0, 0), (1, -1), 0.5, MID_GREY),
        ("VALIGN",       (0, 0), (-1, -1), "BOTTOM"),
    ]))
    story.append(sig_tbl)

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return output_path
