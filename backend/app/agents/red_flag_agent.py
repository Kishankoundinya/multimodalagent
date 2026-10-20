import re
import uuid
from typing import Dict, Any, List
from langchain_core.documents import Document

from backend.app.graph.state import AnalysisState
from backend.app.rag.retriever import retrieve_relevant_chunks, format_context_with_citations, resolve_company_name
from backend.app.llm.llm_provider import get_shared_llm
from backend.app.llm.prompts import RED_FLAG_PROMPT_TEMPLATE, SYSTEM_PROMPT_BASE
from backend.app.database.database import insert_red_flags
from backend.app.utils.logging import logger

def detect_direct_pattern_flags(docs: List[Document], company: str, fiscal_year: str) -> List[Dict[str, Any]]:
    """
    Search chunks for explicit warning signs such as auditor qualifications,
    going concern language, or material weaknesses in internal control.
    """
    flags = []
    
    triggers = [
        (
            r"going\s+concern",
            "Going Concern Uncertainty",
            "The document references going concern conditions or substantial doubt regarding continued operations.",
            "HIGH"
        ),
        (
            r"material\s+weakness(?:es)?\s+in\s+internal\s+control",
            "Internal Control Material Weakness",
            "Management or independent auditors identified material weakness in internal control over financial reporting.",
            "HIGH"
        ),
        (
            r"qualified\s+opinion|adverse\s+opinion",
            "Auditor Opinion Qualification",
            "Independent auditor's report contains a qualified or adverse opinion.",
            "HIGH"
        ),
        (
            r"(?:net\s+cash\s+used\s+in\s+operating\s+activities|negative\s+operating\s+cash\s+flow)",
            "Negative Operating Cash Flow",
            "Operating cash flow is negative, indicating cash burn from core business operations.",
            "MEDIUM"
        ),
        (
            r"(?:defaults?|covenant\s+violation|restructuring\s+charges?)",
            "Debt Covenants or Restructuring Actions",
            "Document references debt covenant violations, restructuring charges, or debt renegotiations.",
            "MEDIUM"
        )
    ]

    for doc in docs:
        text = doc.page_content
        page = doc.metadata.get("page", 1)
        doc_name = doc.metadata.get("document_name", "Report")

        for pattern, title, desc, severity in triggers:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Capture snippet around match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 100)
                evidence = text[start:end].replace("\n", " ").strip()
                
                flags.append({
                    "id": str(uuid.uuid4()),
                    "document_id": doc.metadata.get("document_id", "unknown"),
                    "company": company,
                    "fiscal_year": fiscal_year,
                    "title": title,
                    "description": desc,
                    "evidence": evidence,
                    "severity": severity,
                    "source_document": doc_name,
                    "page": page,
                })
    return flags

def red_flag_agent_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Red Flag Agent:
    Identifies document-supported financial warning indicators with severity and exact evidence.
    """
    doc_id = state.get("document_id")
    company = resolve_company_name(state.get("company")) or state.get("company", "Company")
    fiscal_year = state.get("fiscal_year", "FY")

    logger.info(f"[Red Flag Agent] Analyzing red flags for {company} ({fiscal_year})...")

    # Target queries for risk and red flag disclosures
    queries = [
        f"{company} risks debt maturities liquidity commitments contingencies",
        f"{company} auditor report going concern material weakness",
        f"{company} declining revenues net loss decrease in margins"
    ]

    docs: List[Document] = []
    for q in queries:
        retrieved = retrieve_relevant_chunks(q, company=company, document_id=doc_id, top_k=3)
        for d in retrieved:
            if not any(d.metadata.get("chunk_id") == existing.metadata.get("chunk_id") for existing in docs):
                docs.append(d)

    if not docs:
        logger.info("[Red Flag Agent] No relevant chunks found for red flags.")
        return {"red_flags": []}

    context = format_context_with_citations(docs)
    doc_name = docs[0].metadata.get("document_name", "Annual Report")
    
    # 1. Deterministic pattern checks
    detected_flags = detect_direct_pattern_flags(docs, company, fiscal_year)

    # 2. SharedLLM synthesis
    prompt = RED_FLAG_PROMPT_TEMPLATE.format(
        context=context,
        company=company,
        fiscal_year=fiscal_year
    )

    try:
        llm = get_shared_llm()
        output = llm.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT_BASE, max_new_tokens=160)

        # Parse blocks
        current_flag = {}
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("FLAG:"):
                if current_flag.get("title") and current_flag.get("evidence"):
                    current_flag["id"] = str(uuid.uuid4())
                    current_flag["document_id"] = doc_id or "unknown"
                    current_flag["company"] = company
                    current_flag["fiscal_year"] = fiscal_year
                    current_flag["source_document"] = doc_name
                    detected_flags.append(current_flag)
                current_flag = {"title": line.replace("FLAG:", "").strip()}
            elif line.startswith("SEVERITY:"):
                sev = line.replace("SEVERITY:", "").strip().upper()
                current_flag["severity"] = sev if sev in ["LOW", "MEDIUM", "HIGH"] else "MEDIUM"
            elif line.startswith("PAGE:"):
                try:
                    current_flag["page"] = int(re.search(r"\d+", line).group(0))
                except Exception:
                    current_flag["page"] = docs[0].metadata.get("page", 1)
            elif line.startswith("EVIDENCE:"):
                current_flag["evidence"] = line.replace("EVIDENCE:", "").strip()
            elif line.startswith("DESCRIPTION:"):
                current_flag["description"] = line.replace("DESCRIPTION:", "").strip()

        # Append last flag if complete
        if current_flag.get("title") and current_flag.get("evidence"):
            current_flag["id"] = str(uuid.uuid4())
            current_flag["document_id"] = doc_id or "unknown"
            current_flag["company"] = company
            current_flag["fiscal_year"] = fiscal_year
            current_flag["source_document"] = doc_name
            if "severity" not in current_flag:
                current_flag["severity"] = "MEDIUM"
            if "description" not in current_flag:
                current_flag["description"] = current_flag["title"]
            if "page" not in current_flag:
                current_flag["page"] = docs[0].metadata.get("page", 1)
            detected_flags.append(current_flag)

    except Exception as e:
        logger.warning(f"[Red Flag Agent] LLM parsing warning: {e}")

    # Deduplicate flags by title
    unique_flags = []
    seen_titles = set()
    for f in detected_flags:
        title_key = f["title"].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_flags.append(f)

    # Persist in SQLite
    if unique_flags:
        insert_red_flags(unique_flags)

    logger.info(f"[Red Flag Agent] Identified {len(unique_flags)} red flags.")
    return {"red_flags": unique_flags}
