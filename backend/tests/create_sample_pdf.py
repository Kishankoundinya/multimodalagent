import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

def create_sample_financial_pdf(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("TitleStyle", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=colors.HexColor("#0F172A"))
    h2_style = ParagraphStyle("H2Style", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=colors.HexColor("#1D4ED8"), spaceBefore=10, spaceAfter=8)
    body_style = ParagraphStyle("BodyStyle", fontName="Helvetica", fontSize=10, leading=14, textColor=colors.HexColor("#334155"), spaceAfter=6)

    story = []

    # PAGE 1: Corporate Overview & Financial Highlights
    story.append(Paragraph("Acme Technologies Inc. — Annual Report 2024", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Management Discussion and Financial Review", h2_style))
    story.append(Paragraph(
        "Acme Technologies Inc. reported consolidated results for fiscal year ended December 31, 2024. "
        "During fiscal year 2024, Acme achieved record total net sales of $150,000 million, representing a 12% increase year-over-year. "
        "Gross profit expanded to $65,000 million, while operating income reached $40,000 million.",
        body_style
    ))
    story.append(Paragraph(
        "Operating activities provided positive net cash of $48,000 million. "
        "Diluted earnings per share (EPS) was $4.50 compared to $3.90 in fiscal 2023.",
        body_style
    ))
    story.append(PageBreak())

    # PAGE 2: Consolidated Financial Statements
    story.append(Paragraph("Consolidated Statements of Operations & Balance Sheet", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "For fiscal 2024, net income was $30,000 million compared with $26,000 million in fiscal 2023. "
        "As of December 31, 2024, Acme held total assets of $200,000 million, including cash and cash equivalents of $25,000 million.",
        body_style
    ))
    story.append(Paragraph(
        "Total liabilities stood at $120,000 million, including total debt of $45,000 million comprised of term debt and commercial paper notes. "
        "Total shareholders' equity was $80,000 million.",
        body_style
    ))
    story.append(PageBreak())

    # PAGE 3: Risk Factors & Disclosures
    story.append(Paragraph("Item 1A. Risk Factors & Contingencies", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "The company operates in highly competitive global markets. "
        "Elevated interest rates on floating rate commercial paper represent liquidity and credit risk. "
        "Management identified supply chain disruption risks that could lead to decreasing profit margins in subsequent quarters.",
        body_style
    ))
    story.append(Paragraph(
        "The independent auditor issued an unqualified opinion on the consolidated financial statements with no going concern doubts.",
        body_style
    ))

    doc.build(story)
    print(f"Sample PDF created at {output_path}")

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "data/seed/Acme_Annual_Report_2024.pdf"
    create_sample_financial_pdf(out)
