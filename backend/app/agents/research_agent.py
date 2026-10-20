import re
import uuid
from typing import Dict, Any, List, Optional
from langchain_core.documents import Document

from backend.app.graph.state import AnalysisState
from backend.app.rag.retriever import (
    retrieve_relevant_chunks,
    format_context_with_citations,
    resolve_company_name
)
from backend.app.llm.llm_provider import get_shared_llm
from backend.app.llm.prompts import RESEARCH_PROMPT_TEMPLATE, SYSTEM_PROMPT_BASE
from backend.app.services.citation_service import validate_citations
from backend.app.database.database import insert_research_history
from backend.app.utils.config import settings
from backend.app.utils.logging import logger

def decompose_question(question: str, company: Optional[str] = None) -> List[str]:
    """
    Break complex/multi-part questions into focused subqueries (up to MAX_RETRIEVAL_STEPS).
    """
    subqueries = [question]
    q_lower = question.lower()
    comp_prefix = f"{company} " if company else ""

    # Check for multi-concept questions (e.g., "revenue, net income and debt")
    if " and " in q_lower or "," in q_lower:
        parts = re.split(r"[,;]|\band\b", question)
        cleaned_parts = [p.strip() for p in parts if len(p.strip()) > 3]
        if len(cleaned_parts) > 1:
            subqueries = [f"{comp_prefix}{part}" for part in cleaned_parts[:settings.MAX_RETRIEVAL_STEPS]]

    return subqueries

def research_agent_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Research Agent:
    Handles conversational and complex financial questions with strict grounding and page citations.
    """
    question = state.get("question")
    if not question:
        return {"error": "Research Agent received empty question."}

    company = resolve_company_name(state.get("company"), question)
    fiscal_year = state.get("fiscal_year")
    doc_id = state.get("document_id")

    logger.info(f"[Research Agent] Answering question: '{question}' for resolved company: {company}...")

    # Step 1: Decompose question if multi-part
    subqueries = decompose_question(question, company)
    iterations_used = len(subqueries)

    # Step 2: Multi-step retrieval
    all_retrieved_docs: List[Document] = []
    seen_chunk_ids = set()

    for sub_q in subqueries:
        docs = retrieve_relevant_chunks(
            query=sub_q,
            company=company,
            fiscal_year=fiscal_year,
            document_id=doc_id,
            top_k=settings.TOP_K
        )
        for doc in docs:
            c_id = doc.metadata.get("chunk_id") or doc.page_content[:50]
            if c_id not in seen_chunk_ids:
                seen_chunk_ids.add(c_id)
                all_retrieved_docs.append(doc)

    if not all_retrieved_docs:
        logger.info("[Research Agent] No relevant context found.")
        not_found_msg = "Information not found in the provided documents."
        return {
            "final_answer": not_found_msg,
            "citations": [],
            "is_grounded": False,
            "iterations_used": iterations_used
        }

    # Step 3: Format grounded context
    context = format_context_with_citations(all_retrieved_docs)

    prompt = RESEARCH_PROMPT_TEMPLATE.format(
        context=context,
        question=question
    )

    # Step 4: SharedLLM generation
    try:
        llm = get_shared_llm()
        raw_answer = llm.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT_BASE,
            max_new_tokens=settings.MAX_NEW_TOKENS,
            temperature=settings.TEMPERATURE
        )
    except Exception as e:
        logger.error(f"[Research Agent] LLM generation failed: {e}")
        raw_answer = "Information not found in the provided documents."

    # Step 5: Citation validation & grounding check
    sanitized_answer, valid_citations, is_grounded = validate_citations(
        raw_answer,
        all_retrieved_docs
    )

    # Format Sources section if not already cleanly appended
    if is_grounded and valid_citations and "## Sources" not in sanitized_answer:
        sources_text = "\n\n## Sources\n"
        for idx, c in enumerate(valid_citations, start=1):
            sources_text += f"{idx}. {c.source_document} — p. {c.page}\n"
        sanitized_answer += sources_text

    # Step 6: Persist in SQLite research_history
    history_record = {
        "id": str(uuid.uuid4()),
        "question": question,
        "company": company,
        "answer": sanitized_answer,
        "sources": [c.model_dump() for c in valid_citations]
    }
    try:
        insert_research_history(history_record)
    except Exception as e:
        logger.warning(f"Could not persist research history: {e}")

    return {
        "final_answer": sanitized_answer,
        "citations": [c.model_dump() for c in valid_citations],
        "is_grounded": is_grounded,
        "iterations_used": iterations_used
    }
