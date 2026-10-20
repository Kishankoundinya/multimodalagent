from typing import Dict, Any, List, Optional
from langchain_core.documents import Document

from backend.app.graph.state import AnalysisState
from backend.app.rag.retriever import retrieve_relevant_chunks, format_context_with_citations, resolve_company_name
from backend.app.llm.llm_provider import get_shared_llm
from backend.app.llm.prompts import COMPARISON_PROMPT_TEMPLATE, SYSTEM_PROMPT_BASE
from backend.app.database.database import get_metrics_by_company_year
from backend.app.agents.extraction_agent import clean_numerical_value, CORE_METRIC_NAMES
from backend.app.utils.logging import logger

def compare_values(val_a_str: Optional[str], val_b_str: Optional[str], comp_a: str, comp_b: str) -> Optional[str]:
    """Generate objective, non-subjective difference notes between two reported metrics."""
    if not val_a_str or not val_b_str:
        return None

    num_a = clean_numerical_value(val_a_str)
    num_b = clean_numerical_value(val_b_str)

    if num_a is not None and num_b is not None:
        diff = num_a - num_b
        if diff > 0:
            return f"{comp_a} reported higher by {abs(diff):,.2f} than {comp_b}."
        elif diff < 0:
            return f"{comp_b} reported higher by {abs(diff):,.2f} than {comp_a}."
        else:
            return f"{comp_a} and {comp_b} reported equal values."
    return None

def comparison_agent_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Comparison Agent:
    Performs objective, side-by-side comparison of two companies with exact citations.
    """
    company_a = resolve_company_name(state.get("company")) or state.get("company")
    company_b = resolve_company_name(state.get("company_b")) or state.get("company_b")
    year_a = state.get("fiscal_year")
    year_b = state.get("fiscal_year_b") or year_a

    if not company_a or not company_b:
        return {"error": "Comparison Agent requires both company and company_b."}

    logger.info(f"[Comparison Agent] Comparing {company_a} vs {company_b}...")

    # Load stored metrics from SQLite
    metrics_a_list = get_metrics_by_company_year(company_a, year_a)
    metrics_b_list = get_metrics_by_company_year(company_b, year_b)

    metrics_a_map = {m["metric"]: m for m in metrics_a_list}
    metrics_b_map = {m["metric"]: m for m in metrics_b_list}

    # Retrieve context chunks for both companies
    chunks_a = retrieve_relevant_chunks(f"{company_a} revenue net income debt assets", company=company_a, top_k=3)
    chunks_b = retrieve_relevant_chunks(f"{company_b} revenue net income debt assets", company=company_b, top_k=3)

    context_a = format_context_with_citations(chunks_a)
    context_b = format_context_with_citations(chunks_b)

    # Build comparison rows
    comparison_rows = []
    citations = []

    metrics_to_check = [
        "Revenue", "Net Income", "Operating Income", "Total Assets",
        "Total Liabilities", "Total Debt", "Cash", "Equity", "EPS",
        "Net Profit Margin", "Debt-to-Equity Ratio", "ROE", "ROA"
    ]

    for metric in metrics_to_check:
        m_a = metrics_a_map.get(metric)
        m_b = metrics_b_map.get(metric)

        val_a = m_a["value"] if m_a else None
        page_a = m_a["page"] if m_a else None
        val_b = m_b["value"] if m_b else None
        page_b = m_b["page"] if m_b else None

        diff_note = compare_values(val_a, val_b, company_a, company_b)

        if val_a or val_b:
            comparison_rows.append({
                "metric": metric,
                "company_a_val": val_a or "Not reported in provided documents",
                "company_a_page": page_a,
                "company_b_val": val_b or "Not reported in provided documents",
                "company_b_page": page_b,
                "difference_note": diff_note
            })

            if m_a and page_a:
                citations.append({
                    "source_document": m_a.get("source_document", f"{company_a} Report"),
                    "page": page_a,
                    "snippet": m_a.get("source_text")
                })
            if m_b and page_b:
                citations.append({
                    "source_document": m_b.get("source_document", f"{company_b} Report"),
                    "page": page_b,
                    "snippet": m_b.get("source_text")
                })

    # Generate summary with SharedLLM
    prompt = COMPARISON_PROMPT_TEMPLATE.format(
        company_a=company_a,
        company_b=company_b,
        context_a=context_a,
        context_b=context_b
    )

    try:
        llm = get_shared_llm()
        summary = llm.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT_BASE, max_new_tokens=300)
    except Exception as e:
        logger.warning(f"[Comparison Agent] LLM generation fallback: {e}")
        summary = f"Objective financial comparison conducted between {company_a} and {company_b}. Detailed metrics differences are presented in the comparison table below."

    # Deduplicate citations
    unique_citations = []
    seen = set()
    for c in citations:
        key = (c["source_document"], c["page"])
        if key not in seen:
            seen.add(key)
            unique_citations.append(c)

    results = {
        "company_a": company_a,
        "company_b": company_b,
        "year_a": year_a,
        "year_b": year_b,
        "metrics_comparison": comparison_rows,
        "summary": summary,
        "sources": unique_citations
    }

    return {"comparison_results": results}
