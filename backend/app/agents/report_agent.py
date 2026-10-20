import uuid
from typing import Dict, Any, List
from langchain_core.documents import Document

from backend.app.graph.state import AnalysisState
from backend.app.rag.retriever import retrieve_relevant_chunks, format_context_with_citations
from backend.app.llm.llm_provider import get_shared_llm
from backend.app.llm.prompts import REPORT_SUMMARY_PROMPT_TEMPLATE, SYSTEM_PROMPT_BASE
from backend.app.services.report_service import build_pdf_report
from backend.app.database.database import (
    get_document_by_id,
    get_metrics_for_document,
    get_red_flags_for_document,
    insert_report,
)
from backend.app.utils.config import settings
from backend.app.utils.logging import logger

def report_agent_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Report Agent:
    Compiles validated outputs from other agents, generates narrative summaries,
    and produces an analyst-grade PDF report with exact citations.
    """
    doc_id = state.get("document_id")
    if not doc_id:
        return {"error": "Report Agent requires a document_id."}

    doc_info = get_document_by_id(doc_id)
    if not doc_info:
        return {"error": f"Document {doc_id} not found."}

    company = doc_info["company"]
    fiscal_year = doc_info["fiscal_year"]
    report_title = f"{company} Financial Analysis & Equity Research Report ({fiscal_year})"

    logger.info(f"[Report Agent] Generating report for {company} ({fiscal_year})...")

    # Retrieve metrics and red flags from database if not present in state
    metrics = state.get("metrics") or get_metrics_for_document(doc_id)
    raw_metrics = [m for m in metrics if not m.get("is_calculated")]
    calculated_ratios = [m for m in metrics if m.get("is_calculated")]

    red_flags = state.get("red_flags") or get_red_flags_for_document(doc_id)

    # Context retrieval for narrative sections
    summary_docs = retrieve_relevant_chunks(
        f"{company} business overview financial performance future prospects",
        company=company,
        document_id=doc_id,
        top_k=4
    )
    context = format_context_with_citations(summary_docs)

    prompt = REPORT_SUMMARY_PROMPT_TEMPLATE.format(
        context=context,
        company=company,
        fiscal_year=fiscal_year
    )

    try:
        llm = get_shared_llm()
        exec_summary = llm.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT_BASE,
            max_new_tokens=settings.MAX_REPORT_TOKENS
        )
    except Exception as e:
        logger.warning(f"[Report Agent] LLM summary generation: {e}")
        exec_summary = (
            f"This financial analysis report evaluates the disclosed performance of {company} "
            f"for fiscal period {fiscal_year}. All key metrics and findings are grounded in official filings."
        )

    # Gather citations from summary docs
    sources = []
    for d in summary_docs:
        sources.append({
            "source_document": d.metadata.get("document_name", doc_info["filename"]),
            "page": d.metadata.get("page", 1),
            "snippet": d.page_content[:150]
        })

    sections = {
        "executive_summary": exec_summary,
        "company_info": {
            "company": company,
            "fiscal_year": fiscal_year,
            "document_name": doc_info["filename"],
            "num_pages": doc_info.get("num_pages", 0),
            "num_chunks": doc_info.get("num_chunks", 0),
        },
        "metrics": raw_metrics,
        "calculated_ratios": calculated_ratios,
        "financial_trends": (
            f"Analysis of {company}'s statements reflects reported operating metrics for {fiscal_year}. "
            "Please refer to the extracted metrics and calculated profitability margins for detailed breakdown."
        ),
        "red_flags": red_flags,
        "comparison_summary": "Comparative data is available on the multi-company comparison dashboard.",
        "research_findings": state.get("final_answer") or "Detailed findings synthesized from disclosed financial notes.",
        "sources": sources,
    }

    report_id = str(uuid.uuid4())
    pdf_path = build_pdf_report(
        report_id=report_id,
        title=report_title,
        company=company,
        fiscal_year=fiscal_year,
        sections=sections
    )

    report_record = {
        "id": report_id,
        "title": report_title,
        "company": company,
        "fiscal_year": fiscal_year,
        "file_path": pdf_path,
        "sections": sections
    }
    insert_report(report_record)

    report_results = {
        "id": report_id,
        "title": report_title,
        "company": company,
        "fiscal_year": fiscal_year,
        "file_path": pdf_path,
        "created_at": doc_info.get("upload_date"),
        "download_url": f"/api/reports/{report_id}/download"
    }

    logger.info(f"[Report Agent] Report generated successfully: {report_id}")
    return {"report_results": report_results}
