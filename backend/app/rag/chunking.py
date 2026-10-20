import uuid
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from backend.app.utils.config import settings
from backend.app.utils.logging import logger

def get_text_splitter(
    chunk_size: int = None,
    chunk_overlap: int = None
) -> RecursiveCharacterTextSplitter:
    size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP
    return RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

def chunk_page_contents(
    pages: List[Dict[str, Any]],
    document_id: str,
    document_name: str,
    company: str,
    fiscal_year: str,
    chunk_size: int = None,
    chunk_overlap: int = None
) -> List[Document]:
    """
    Split extracted page text into chunks while strictly preserving page-level metadata.
    pages: List of dicts with 'page' (1-indexed int) and 'text' (str).
    """
    splitter = get_text_splitter(chunk_size, chunk_overlap)
    documents: List[Document] = []

    for page_info in pages:
        page_num = page_info["page"]
        text = page_info["text"].strip()
        if not text:
            continue

        raw_chunks = splitter.split_text(text)
        for idx, chunk_text in enumerate(raw_chunks):
            chunk_id = f"{document_id}_p{page_num}_c{idx}"
            metadata = {
                "document_id": document_id,
                "document_name": document_name,
                "company": company,
                "year": fiscal_year,
                "page": int(page_num),
                "chunk_id": chunk_id,
            }
            doc = Document(page_content=chunk_text, metadata=metadata)
            documents.append(doc)

    logger.info(f"Chunked document '{document_name}' into {len(documents)} chunks across {len(pages)} pages.")
    return documents
