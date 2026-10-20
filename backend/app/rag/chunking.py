import uuid
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from backend.app.utils.config import settings
from backend.app.utils.logging import logger

class LightweightRecursiveCharacterSplitter:
    """
    Ultra-lightweight recursive character text splitter.
    Avoids importing heavy ML libraries (e.g. transformers/torch) from langchain_text_splitters,
    saving ~400MB of resident RAM.
    """
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        if not text:
            return []

        chunks: List[str] = []

        def _split(txt: str, seps: List[str]):
            if not txt.strip():
                return
            if len(txt) <= self.chunk_size or not seps:
                chunks.append(txt.strip())
                return

            sep = seps[0]
            parts = txt.split(sep) if sep else list(txt)
            current_doc = ""

            for part in parts:
                candidate = (current_doc + sep + part) if current_doc else part
                if len(candidate) <= self.chunk_size:
                    current_doc = candidate
                else:
                    if current_doc:
                        chunks.append(current_doc.strip())
                        overlap_start = max(0, len(current_doc) - self.chunk_overlap)
                        overlap_prefix = current_doc[overlap_start:]
                        current_doc = (overlap_prefix + sep + part) if overlap_prefix else part
                        if len(current_doc) > self.chunk_size:
                            _split(part, seps[1:])
                            current_doc = ""
                    else:
                        _split(part, seps[1:])

            if current_doc and current_doc.strip():
                chunks.append(current_doc.strip())

        _split(text, self.separators)
        return [c for c in chunks if c.strip()]


def get_text_splitter(
    chunk_size: int = None,
    chunk_overlap: int = None
) -> LightweightRecursiveCharacterSplitter:
    size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP
    return LightweightRecursiveCharacterSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
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
