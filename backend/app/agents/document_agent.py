from typing import Dict, Any
from backend.app.graph.state import AnalysisState
from backend.app.services.document_service import process_pdf_document
from backend.app.utils.logging import logger

def document_agent_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Document Agent:
    Validates, extracts text using PyMuPDF, chunks, embeds, and stores in ChromaDB.
    """
    doc_id = state.get("document_id")
    if not doc_id:
        return {"error": "Document Agent received no document_id."}

    logger.info(f"[Document Agent] Processing document {doc_id}...")
    try:
        updated_doc = process_pdf_document(doc_id)
        return {
            "document_id": doc_id,
            "company": updated_doc.get("company"),
            "fiscal_year": updated_doc.get("fiscal_year"),
        }
    except Exception as e:
        logger.error(f"[Document Agent] Failed: {e}")
        return {"error": str(e)}
