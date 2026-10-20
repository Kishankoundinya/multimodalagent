import os
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pymupdf as fitz

from backend.app.utils.config import settings
from backend.app.utils.logging import logger
from backend.app.database.database import (
    insert_document,
    update_document_status,
    get_document_by_id,
    get_all_documents,
    delete_document,
)
from backend.app.rag.chunking import chunk_page_contents
from backend.app.rag.vector_store import add_documents_to_chroma, delete_document_from_chroma
from backend.app.models.schemas import SeedDocument

def extract_text_from_pdf(file_path: str) -> Tuple[List[Dict[str, Any]], int]:
    """
    Extract text page-by-page from a PDF using PyMuPDF (fitz).
    Returns list of {'page': int, 'text': str} and total_pages.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    doc = fitz.open(file_path)
    total_pages = len(doc)
    pages: List[Dict[str, Any]] = []
    total_text_length = 0

    for page_idx in range(total_pages):
        page = doc[page_idx]
        text = page.get_text("text")
        cleaned_text = re.sub(r"[ \t]+", " ", text).strip()
        pages.append({
            "page": page_idx + 1,
            "text": cleaned_text
        })
        total_text_length += len(cleaned_text)

    doc.close()

    # Check for scanned PDF / non-extractable text
    if total_text_length < 50:
        raise ValueError("This PDF does not contain extractable text. OCR support can be added later.")

    return pages, total_pages

def process_pdf_document(document_id: str) -> Dict[str, Any]:
    """
    Execute document indexing pipeline:
    Extracting -> Chunking -> Embedding -> Indexing -> Completed
    """
    doc_info = get_document_by_id(document_id)
    if not doc_info:
        raise ValueError(f"Document with ID {document_id} not found.")

    file_path = doc_info["file_path"]
    filename = doc_info["filename"]
    company = doc_info["company"]
    fiscal_year = doc_info["fiscal_year"]

    logger.info(f"Starting processing for document {document_id} ({filename})")

    try:
        # Stage 1: Extracting
        update_document_status(document_id, status="Extracting")
        pages, num_pages = extract_text_from_pdf(file_path)

        # Stage 2: Chunking
        update_document_status(document_id, status="Chunking", num_pages=num_pages)
        chunks = chunk_page_contents(
            pages=pages,
            document_id=document_id,
            document_name=filename,
            company=company,
            fiscal_year=fiscal_year,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        # Free raw pages from memory
        del pages
        import gc
        gc.collect()

        if not chunks:
            raise ValueError("No valid text chunks could be created from document.")

        chunk_count = len(chunks)

        # Stage 3: Embedding
        update_document_status(document_id, status="Embedding", num_chunks=chunk_count)

        # Stage 4: Indexing in ChromaDB
        update_document_status(document_id, status="Indexing")
        add_documents_to_chroma(chunks)
        del chunks
        gc.collect()

        # Stage 5: Completed
        update_document_status(
            document_id,
            status="Completed",
            num_pages=num_pages,
            num_chunks=chunk_count
        )
        logger.info(f"Document {document_id} processing completed successfully.")
        return get_document_by_id(document_id)

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed processing document {document_id}: {error_msg}")
        update_document_status(document_id, status="Failed", error_message=error_msg)
        raise e

def detect_seed_documents() -> List[SeedDocument]:
    """
    Scans the data/seed directory for PDFs and checks if already indexed in database.
    """
    seed_path = Path(settings.SEED_DIR)
    if not seed_path.exists():
        return []

    existing_docs = {d["filename"]: d for d in get_all_documents()}
    seed_files = list(seed_path.glob("*.pdf"))
    results: List[SeedDocument] = []

    for file in seed_files:
        filename = file.name
        file_size = file.stat().st_size
        
        # Heuristic to detect company name and year from filename
        # e.g. "Apple_Annual_Report_2024.pdf" -> company "Apple", year "2024"
        stem = file.stem
        year_match = re.search(r"\b(19\d\d|20\d\d)\b", stem)
        detected_year = year_match.group(1) if year_match else "2024"

        clean_stem = re.sub(r"[\b_]?(annual|report|10-?k|fy|q\d|\d{4})[\b_]?", " ", stem, flags=re.IGNORECASE)
        detected_company = clean_stem.strip().title() or "Company"

        is_indexed = filename in existing_docs
        doc_id = existing_docs[filename]["id"] if is_indexed else None

        results.append(SeedDocument(
            filename=filename,
            file_path=str(file),
            file_size=file_size,
            detected_company=detected_company,
            detected_year=detected_year,
            is_indexed=is_indexed,
            document_id=doc_id,
        ))

    return results

def remove_document(document_id: str):
    """Delete document from SQLite, ChromaDB, and disk."""
    doc = get_document_by_id(document_id)
    if doc:
        delete_document_from_chroma(document_id)
        delete_document(document_id)
        if os.path.exists(doc["file_path"]):
            try:
                os.remove(doc["file_path"])
            except Exception as e:
                logger.warning(f"Could not remove file on disk {doc['file_path']}: {e}")
