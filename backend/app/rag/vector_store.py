import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.app.utils.config import settings
from backend.app.utils.logging import logger
from backend.app.rag.embeddings import get_embeddings

_chroma_client: Optional[chromadb.PersistentClient] = None
_vector_store: Optional[Chroma] = None

COLLECTION_NAME = "financial_documents"

def get_chroma_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        logger.info(f"Initialized ChromaDB persistent client at {settings.CHROMA_PERSIST_DIR}")
    return _chroma_client

def get_vector_store() -> Chroma:
    global _vector_store
    if _vector_store is None:
        client = get_chroma_client()
        embeddings = get_embeddings()
        _vector_store = Chroma(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
        )
        logger.info(f"Initialized Chroma vector store collection '{COLLECTION_NAME}'")
    return _vector_store

def add_documents_to_chroma(documents: List[Document]) -> int:
    """
    Store LangChain documents into ChromaDB with metadata.
    """
    if not documents:
        return 0
    store = get_vector_store()
    
    # IDs can be taken from chunk_id metadata for idempotent upserts
    ids = [doc.metadata.get("chunk_id") for doc in documents]
    store.add_documents(documents=documents, ids=ids)
    logger.info(f"Added {len(documents)} document chunks to ChromaDB.")
    return len(documents)

def search_similar_chunks(
    query: str,
    top_k: Optional[int] = None,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[Document]:
    """
    Query vector store for the top_k most relevant chunks matching optional filters.
    """
    k = top_k or settings.TOP_K
    store = get_vector_store()
    try:
        if filter_dict:
            results = store.similarity_search(query, k=k, filter=filter_dict)
        else:
            results = store.similarity_search(query, k=k)
        return results
    except Exception as e:
        logger.error(f"Error querying ChromaDB: {e}")
        return []

def delete_document_from_chroma(document_id: str):
    """
    Remove all chunks associated with a document_id from ChromaDB.
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(COLLECTION_NAME)
        collection.delete(where={"document_id": document_id})
        logger.info(f"Deleted chunks for document_id '{document_id}' from ChromaDB.")
    except Exception as e:
        logger.warning(f"Could not delete chunks for document_id '{document_id}': {e}")

def get_vector_store_count() -> int:
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(COLLECTION_NAME)
        return collection.count()
    except Exception:
        return 0
