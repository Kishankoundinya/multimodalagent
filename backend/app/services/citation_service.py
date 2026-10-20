import re
from typing import List, Tuple, Dict, Any, Optional
from langchain_core.documents import Document
from backend.app.models.schemas import Citation
from backend.app.utils.logging import logger

# Regex to match [Source: filename or company, p. 42] or [Source: filename, page 42]
CITATION_PATTERN = re.compile(
    r"\[Source:\s*([^,\]]+?),\s*(?:p\.|page)\s*(\d+)\]",
    re.IGNORECASE
)

# Alternative simple citation pattern like [p. 42] or (p. 42)
PAGE_ONLY_PATTERN = re.compile(r"\[(?:p\.|page)\s*(\d+)\]", re.IGNORECASE)

def extract_numbers_from_text(text: str) -> List[str]:
    """Extract currency figures, percentages, and floating numbers."""
    return re.findall(r"\$?\d+(?:,\d{3})*(?:\.\d+)?%?", text)

def validate_citations(
    answer: str,
    retrieved_documents: List[Document]
) -> Tuple[str, List[Citation], bool]:
    """
    Validates all citations in an LLM answer against the actual retrieved documents.
    Returns:
        (sanitized_answer, list_of_valid_citations, is_grounded)
    """
    if not retrieved_documents:
        return "Information not found in the provided documents.", [], False

    # Build lookup of valid pages and documents from retrieved chunks
    valid_source_pages: Dict[int, List[Document]] = {}
    valid_doc_names = set()

    for doc in retrieved_documents:
        page = doc.metadata.get("page")
        doc_name = doc.metadata.get("document_name", "").lower()
        company = doc.metadata.get("company", "").lower()
        valid_doc_names.add(doc_name)
        if company:
            valid_doc_names.add(company)

        if page is not None:
            try:
                page_int = int(page)
                if page_int not in valid_source_pages:
                    valid_source_pages[page_int] = []
                valid_source_pages[page_int].append(doc)
            except (ValueError, TypeError):
                pass

    found_matches = list(CITATION_PATTERN.finditer(answer))
    valid_citations: List[Citation] = []
    sanitized_answer = answer

    clean_ans = answer.strip().lower()
    has_citations_or_pages = bool(found_matches or PAGE_ONLY_PATTERN.findall(answer))

    # If the answer explicitly says not found and has no source citations, respect it
    if clean_ans == "information not found in the provided documents." or (
        "information not found in the provided documents" in clean_ans and not has_citations_or_pages
    ):
        return "Information not found in the provided documents.", [], False

    if not found_matches:
        # Check if page-only citations were used e.g. [p. 12]
        page_matches = list(PAGE_ONLY_PATTERN.finditer(answer))
        if page_matches:
            # Normalize them using the first retrieved doc's name
            primary_doc_name = retrieved_documents[0].metadata.get("document_name", "Document")
            for pm in page_matches:
                page_num = int(pm.group(1))
                if page_num in valid_source_pages:
                    replacement = f"[Source: {primary_doc_name}, p. {page_num}]"
                    sanitized_answer = sanitized_answer.replace(pm.group(0), replacement)
                    valid_citations.append(Citation(
                        source_document=primary_doc_name,
                        page=page_num,
                        snippet=valid_source_pages[page_num][0].page_content[:200]
                    ))
                else:
                    # Remove invalid page citation
                    sanitized_answer = sanitized_answer.replace(pm.group(0), "")
        else:
            # If no citations were embedded by LLM, check if answer contains verified data
            # and append actual source metadata from top retrieved doc
            top_doc = retrieved_documents[0]
            top_page = top_doc.metadata.get("page", 1)
            top_name = top_doc.metadata.get("document_name", "Document")
            valid_citations.append(Citation(
                source_document=top_name,
                page=int(top_page),
                snippet=top_doc.page_content[:200]
            ))

    for match in found_matches:
        raw_source = match.group(1).strip()
        page_num = int(match.group(2))

        # Check if page exists in retrieved documents
        if page_num in valid_source_pages:
            doc_for_page = valid_source_pages[page_num][0]
            resolved_doc_name = doc_for_page.metadata.get("document_name", raw_source)
            valid_citations.append(Citation(
                source_document=resolved_doc_name,
                page=page_num,
                snippet=doc_for_page.page_content[:250].strip()
            ))
        else:
            # Hallucinated page number! Remove or invalidate
            logger.warning(f"Citation validation failed: Page {page_num} not in retrieved chunks.")
            sanitized_answer = sanitized_answer.replace(match.group(0), "[Source unverified]")

    # Check grounding: If answer claimed citations but none were valid
    if found_matches and not valid_citations:
        return "Insufficient source evidence to provide a reliable answer.", [], False

    # Deduplicate citations
    unique_citations: List[Citation] = []
    seen = set()
    for c in valid_citations:
        key = (c.source_document, c.page)
        if key not in seen:
            seen.add(key)
            unique_citations.append(c)

    return sanitized_answer, unique_citations, True
