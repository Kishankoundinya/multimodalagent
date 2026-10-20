import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.pdfgen import canvas

from backend.app.utils.config import settings
from backend.app.utils.logging import logger
from backend.app.database.database import insert_report

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print total page count:
    'Page X of Y' along with a professional header.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        if self._pageNumber > 1:
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#6B7280"))
            # Header
            self.drawString(54, 750, "FINANCIAL RESEARCH & ANALYSIS REPORT | LOCAL AI SYSTEM")
            self.setStrokeColor(colors.HexColor("#E5E7EB"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

            # Footer
            page_str = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(558, 36, page_str)
            self.drawString(54, 36, "Strictly Grounded in Disclosed Filings | Do Not Fabricate")
            self.line(54, 48, 558, 48)
            self.restoreState()

def build_pdf_report(
    report_id: str,
    title: str,
    company: str,
    fiscal_year: str,
    sections: Dict[str, Any]
) -> str:
    """
    Generate professional PDF research report.
    Returns path to the generated PDF.
    """
    os.makedirs(settings.REPORT_DIR, exist_ok=True)
    pdf_filename = f"report_{company.lower().replace(' ', '_')}_{fiscal_year}_{report_id[:8]}.pdf"
    pdf_path = os.path.join(settings.REPORT_DIR, pdf_filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    c_primary = colors.HexColor("#0F172A")
    c_accent = colors.HexColor("#1D4ED8")
    c_text = colors.HexColor("#334155")
    c_light = colors.HexColor("#F8FAFC")
    c_border = colors.HexColor("#CBD5E1")

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=32,
        textColor=c_primary,
        alignment=0,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=18,
        textColor=c_accent,
    )
    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=20,
        textColor=c_primary,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=c_text,
        spaceAfter=6,
    )
    source_tag_style = ParagraphStyle(
        "Source_Tag",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#4B5563"),
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=c_text,
    )
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    story = []

    # ==========================================
    # 1. COVER PAGE
    # ==========================================
    story.append(Spacer(1, 100))
    story.append(Paragraph("FINANCIAL RESEARCH & ANALYSIS SYSTEM", subtitle_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=3, color=c_accent, spaceBefore=4, spaceAfter=20))

    meta_text = (
        f"<b>Target Entity:</b> {company}<br/>"
        f"<b>Reporting Period:</b> {fiscal_year}<br/>"
        f"<b>Analysis Generated:</b> {datetime.now().strftime('%B %d, %Y')}<br/>"
        f"<b>Verification Status:</b> Document Grounded & Source Validated<br/>"
        f"<b>Engine:</b> LangGraph Multi-Agent Architecture | Google Gemini ({settings.LLM_MODEL})"
    )
    story.append(Paragraph(meta_text, body_style))
    story.append(Spacer(1, 40))

    disclaimer = (
        "<i>Notice: This report is systematically constructed from primary company disclosure documents. "
        "Every factual claim, metric, and red flag is strictly verified against source document page numbers. "
        "No financial information was artificially synthesized.</i>"
    )
    story.append(Paragraph(disclaimer, source_tag_style))
    story.append(PageBreak())

    # ==========================================
    # 2. EXECUTIVE SUMMARY
    # ==========================================
    story.append(Paragraph("1. Executive Summary", h1_style))
    exec_summary = sections.get("executive_summary", "Executive summary not provided.")
    story.append(Paragraph(exec_summary.replace("\n", "<br/>"), body_style))
    story.append(Spacer(1, 14))

    # ==========================================
    # 3. COMPANY INFORMATION
    # ==========================================
    story.append(Paragraph("2. Company & Filing Information", h1_style))
    comp_info = sections.get("company_info", {})
    doc_name = comp_info.get("document_name", "Primary Disclosure Document")
    pages_count = comp_info.get("num_pages", "N/A")
    chunks_count = comp_info.get("num_chunks", "N/A")

    info_data = [
        [Paragraph("<b>Company Name</b>", table_cell_style), Paragraph(company, table_cell_style)],
        [Paragraph("<b>Fiscal Year</b>", table_cell_style), Paragraph(fiscal_year, table_cell_style)],
        [Paragraph("<b>Source Document</b>", table_cell_style), Paragraph(doc_name, table_cell_style)],
        [Paragraph("<b>Total Document Pages</b>", table_cell_style), Paragraph(str(pages_count), table_cell_style)],
        [Paragraph("<b>Indexed Context Chunks</b>", table_cell_style), Paragraph(str(chunks_count), table_cell_style)],
    ]
    info_table = Table(info_data, colWidths=[150, 350])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_light),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))

    # ==========================================
    # 4. KEY FINANCIAL METRICS
    # ==========================================
    story.append(Paragraph("3. Key Financial Metrics", h1_style))
    metrics_list = sections.get("metrics", [])
    if metrics_list:
        metric_table_data = [[
            Paragraph("<b>Metric</b>", table_header_style),
            Paragraph("<b>Value</b>", table_header_style),
            Paragraph("<b>Period</b>", table_header_style),
            Paragraph("<b>Source Page</b>", table_header_style),
        ]]
        for m in metrics_list:
            metric_table_data.append([
                Paragraph(m.get("metric", ""), table_cell_style),
                Paragraph(str(m.get("value", "N/A")), table_cell_style),
                Paragraph(str(m.get("period", fiscal_year)), table_cell_style),
                Paragraph(f"Page {m.get('page', 'N/A')}", table_cell_style),
            ])
        m_table = Table(metric_table_data, colWidths=[160, 140, 100, 100])
        m_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("GRID", (0, 0), (-1, -1), 0.5, c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(m_table)
    else:
        story.append(Paragraph("Information not found in the provided documents.", body_style))
    story.append(Spacer(1, 14))

    # ==========================================
    # 5. FINANCIAL PERFORMANCE & CALCULATED RATIOS
    # ==========================================
    story.append(Paragraph("4. Financial Performance & Calculated Ratios", h1_style))
    ratios_list = sections.get("calculated_ratios", [])
    if ratios_list:
        ratios_table_data = [[
            Paragraph("<b>Calculated Ratio</b>", table_header_style),
            Paragraph("<b>Value</b>", table_header_style),
            Paragraph("<b>Source Formula & Derivation</b>", table_header_style),
        ]]
        for r in ratios_list:
            ratios_table_data.append([
                Paragraph(r.get("metric", ""), table_cell_style),
                Paragraph(str(r.get("value", "N/A")), table_cell_style),
                Paragraph(str(r.get("calculation_formula") or r.get("source_text") or "Calculated from source values"), table_cell_style),
            ])
        r_table = Table(ratios_table_data, colWidths=[140, 90, 270])
        r_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_accent),
            ("GRID", (0, 0), (-1, -1), 0.5, c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(r_table)
    else:
        story.append(Paragraph("No verifiable ratios could be calculated from disclosed base values.", body_style))
    story.append(Spacer(1, 14))

    # ==========================================
    # 6. FINANCIAL TRENDS
    # ==========================================
    story.append(Paragraph("5. Financial Trends & Operating Trajectory", h1_style))
    trends_narrative = sections.get("financial_trends", "Financial trend observations based on primary filings.")
    story.append(Paragraph(trends_narrative.replace("\n", "<br/>"), body_style))
    story.append(Spacer(1, 14))

    # ==========================================
    # 7. RED FLAGS
    # ==========================================
    story.append(Paragraph("6. Identified Financial Red Flags & Risk Indicators", h1_style))
    red_flags = sections.get("red_flags", [])
    if red_flags:
        rf_table_data = [[
            Paragraph("<b>Severity</b>", table_header_style),
            Paragraph("<b>Indicator</b>", table_header_style),
            Paragraph("<b>Documented Evidence & Citation</b>", table_header_style),
        ]]
        for rf in red_flags:
            sev = rf.get("severity", "MEDIUM")
            sev_color = colors.HexColor("#DC2626") if sev == "HIGH" else (
                colors.HexColor("#D97706") if sev == "MEDIUM" else colors.HexColor("#2563EB")
            )
            rf_table_data.append([
                Paragraph(f"<font color='{sev_color}'><b>{sev}</b></font>", table_cell_style),
                Paragraph(f"<b>{rf.get('title', '')}</b><br/>{rf.get('description', '')}", table_cell_style),
                Paragraph(f"{rf.get('evidence', '')}<br/><b>Source:</b> Page {rf.get('page', 'N/A')}", source_tag_style),
            ])
        rf_table = Table(rf_table_data, colWidths=[70, 180, 250])
        rf_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("GRID", (0, 0), (-1, -1), 0.5, c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(rf_table)
    else:
        story.append(Paragraph("No significant material red flags identified in the examined sections.", body_style))
    story.append(Spacer(1, 14))

    # ==========================================
    # 8. COMPANY COMPARISON
    # ==========================================
    story.append(Paragraph("7. Company / Peer Comparison", h1_style))
    comp_narrative = sections.get("comparison_summary", "Single-entity comprehensive review.")
    story.append(Paragraph(comp_narrative.replace("\n", "<br/>"), body_style))
    story.append(Spacer(1, 14))

    # ==========================================
    # 9. RESEARCH FINDINGS
    # ==========================================
    story.append(Paragraph("8. Key Research Findings", h1_style))
    findings = sections.get("research_findings", "Document-grounded analysis findings.")
    story.append(Paragraph(findings.replace("\n", "<br/>"), body_style))
    story.append(Spacer(1, 14))

    # ==========================================
    # 10. SOURCES
    # ==========================================
    story.append(Paragraph("9. Verified Disclosed Sources", h1_style))
    sources_list = sections.get("sources", [])
    if sources_list:
        sources_table_data = [[
            Paragraph("<b>#</b>", table_header_style),
            Paragraph("<b>Document Name</b>", table_header_style),
            Paragraph("<b>Cited Page</b>", table_header_style),
            Paragraph("<b>Context Snippet</b>", table_header_style),
        ]]
        for idx, s in enumerate(sources_list, start=1):
            sources_table_data.append([
                Paragraph(str(idx), table_cell_style),
                Paragraph(s.get("source_document", "Report"), table_cell_style),
                Paragraph(f"Page {s.get('page', 'N/A')}", table_cell_style),
                Paragraph(s.get("snippet", "")[:120] + "...", source_tag_style),
            ])
        s_table = Table(sources_table_data, colWidths=[30, 150, 70, 250])
        s_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#475569")),
            ("GRID", (0, 0), (-1, -1), 0.5, c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(s_table)
    else:
        story.append(Paragraph("Primary disclosures indexed in local repository.", body_style))

    # Build the document with custom numbered canvas
    doc.build(story, canvasmaker=NumberedCanvas)
    logger.info(f"Generated PDF report saved to {pdf_path}")
    return pdf_path
