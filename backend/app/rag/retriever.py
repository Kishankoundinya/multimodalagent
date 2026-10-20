import difflib
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from backend.app.rag.vector_store import search_similar_chunks, get_vector_store
from backend.app.utils.config import settings
from backend.app.utils.logging import logger

def get_all_indexed_companies() -> List[str]:
    """
    Fetch all unique company names currently stored in the vector store.
    """
    try:
        vs = get_vector_store()
        data = vs.get(include=["metadatas"])
        if not data or not data.get("metadatas"):
            return []
        comps = set(m.get("company") for m in data["metadatas"] if m.get("company"))
        return [c for c in comps if c.strip()]
    except Exception as e:
        logger.warning(f"Could not load indexed companies: {e}")
        return []

def resolve_company_name(
    input_company: Optional[str] = None,
    query: Optional[str] = None
) -> Optional[str]:
    """
    Resolves spelling variations, typos (e.g. 'Accenture' -> 'ACCCENTURE'),
    or automatically extracts the company entity mentioned in the user query.
    """
    known_companies = get_all_indexed_companies()
    if not known_companies:
        return input_company

    # 1. Match from input_company
    if input_company and input_company.strip():
        inp = input_company.strip().lower()
        for c in known_companies:
            cl = c.lower()
            if inp == cl or inp in cl or cl in inp:
                return c
            if difflib.SequenceMatcher(None, inp, cl).ratio() >= 0.7:
                return c

    # 2. Extract from query if company not passed or unresolved
    if query and query.strip():
        q_lower = query.lower()
        # Direct check against full company name or primary word
        for c in known_companies:
            cl = c.lower()
            first_word = cl.split()[0]
            if cl in q_lower or (len(first_word) >= 3 and first_word in q_lower):
                return c

        # Token-by-token fuzzy comparison
        words = [w.strip("',.?!()[]{}:;\"") for w in q_lower.split()]
        for w in words:
            if len(w) < 3:
                continue
            for c in known_companies:
                first_word = c.lower().split()[0]
                if difflib.SequenceMatcher(None, w, first_word).ratio() >= 0.75:
                    return c

    return input_company

def retrieve_relevant_chunks(
    query: str,
    company: Optional[str] = None,
    fiscal_year: Optional[str] = None,
    document_id: Optional[str] = None,
    top_k: Optional[int] = None
) -> List[Document]:
    """
    Universal Vector RAG Retrieval:
    Embeds the user question, searches the vector store for the most relevant
    semantic embeddings, and returns them for LLM synthesis.
    Zero hardcoded values, completely generic for any document.
    """
    k = max(top_k or settings.TOP_K, 15)
    resolved_comp = resolve_company_name(company, query) or company

    filters = {}
    if document_id:
        filters["document_id"] = document_id
    elif resolved_comp and fiscal_year:
        filters = {"$and": [{"company": resolved_comp}, {"year": fiscal_year}]}
    elif resolved_comp:
        filters = {"company": resolved_comp}
    elif fiscal_year:
        filters = {"year": fiscal_year}

    filter_dict = filters if filters else None
    logger.info(f"Vector search for query: '{query}' (company: '{resolved_comp}') with filter: {filter_dict}, k={k}")

    # 1. Primary vector similarity search
    docs = search_similar_chunks(query, top_k=k, filter_dict=filter_dict)

    # 2. If filtered search returned fewer chunks than requested, supplement with broader vector search
    if len(docs) < k:
        fallback_docs = search_similar_chunks(query, top_k=k)
        seen = {(d.metadata.get("document_name"), d.metadata.get("page"), d.page_content[:60]) for d in docs}
        for fd in fallback_docs:
            key = (fd.metadata.get("document_name"), fd.metadata.get("page"), fd.page_content[:60])
            if key not in seen:
                seen.add(key)
                docs.append(fd)
                if len(docs) >= k:
                    break

    logger.info(f"Retrieved {len(docs)} chunks via vector embedding search.")
    return docs[:k]

def format_context_with_citations(documents: List[Document]) -> str:
    """
    Format retrieved documents into a context block with explicit source tags:
    [Source: document_name, p. page]
    """
    if not documents:
        return "No relevant context found in uploaded documents."

    formatted_pieces = []
    for i, doc in enumerate(documents, start=1):
        doc_name = doc.metadata.get("document_name", "Unknown Document")
        page = doc.metadata.get("page", "Unknown")
        company = doc.metadata.get("company", "")
        content = doc.page_content.strip()

        piece = (
            f"--- Document Snippet {i} ---\n"
            f"Source: {doc_name}, Page: {page}, Company: {company}\n"
            f"Content:\n{content}\n"
        )
        formatted_pieces.append(piece)

    return "\n".join(formatted_pieces)
