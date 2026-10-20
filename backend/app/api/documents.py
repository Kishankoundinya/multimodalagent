import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from backend.app.models.schemas import (
    DocumentResponse,
    DocumentUploadResponse,
    SeedDocument,
    SeedIndexRequest,
)
from backend.app.database.database import (
    insert_document,
    get_all_documents,
    get_document_by_id,
)
from backend.app.services.document_service import (
    process_pdf_document,
    detect_seed_documents,
    remove_document,
)
from backend.app.utils.config import settings
from backend.app.utils.logging import logger

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.get("", response_model=List[DocumentResponse])
def list_documents():
    """List all tracked documents in SQLite."""
    return get_all_documents()

@router.get("/seed/list", response_model=List[SeedDocument])
def list_seed_documents():
    """List all detected PDFs in data/seed directory."""
    return detect_seed_documents()

@router.post("/seed/index", response_model=DocumentResponse)
def index_seed_document(req: SeedIndexRequest, background_tasks: BackgroundTasks):
    """Index an unindexed PDF from the seed folder."""
    seed_file_path = os.path.join(settings.SEED_DIR, req.filename)
    if not os.path.exists(seed_file_path):
        raise HTTPException(status_code=404, detail=f"Seed document '{req.filename}' not found.")

    doc_id = str(uuid.uuid4())
    dest_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{req.filename}")
    shutil.copyfile(seed_file_path, dest_path)
    file_size = os.path.getsize(dest_path)

    doc_data = {
        "id": doc_id,
        "filename": req.filename,
        "company": req.company,
        "fiscal_year": req.fiscal_year,
        "file_path": dest_path,
        "file_size": file_size,
        "processing_status": "Uploading",
    }
    insert_document(doc_data)

    # Process in background task
    background_tasks.add_task(process_pdf_document, doc_id)
    return get_document_by_id(doc_id)

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company: str = Form(...),
    fiscal_year: str = Form(...),
    auto_process: bool = Form(True)
):
    """Upload a new PDF financial document."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported at this stage.")

    # Size validation
    doc_id = str(uuid.uuid4())
    dest_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{file.filename}")
    
    try:
        with open(dest_path, "wb") as buffer:
            contents = await file.read()
            if len(contents) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"File exceeds max size of {settings.MAX_FILE_SIZE_MB}MB.")
            buffer.write(contents)
    except Exception as e:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    file_size = os.path.getsize(dest_path)
    doc_data = {
        "id": doc_id,
        "filename": file.filename,
        "company": company.strip(),
        "fiscal_year": fiscal_year.strip(),
        "file_path": dest_path,
        "file_size": file_size,
        "processing_status": "Uploading",
    }
    insert_document(doc_data)

    if auto_process:
        background_tasks.add_task(process_pdf_document, doc_id)
        doc_record = get_document_by_id(doc_id)
        return DocumentUploadResponse(
            document=doc_record,
            message="Document uploaded successfully. Processing pipeline scheduled."
        )

    doc_record = get_document_by_id(doc_id)
    return DocumentUploadResponse(
        document=doc_record,
        message="Document uploaded successfully. Processing pending."
    )

@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: str):
    """Get single document details and processing status."""
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc

@router.post("/{doc_id}/process", response_model=DocumentResponse)
def trigger_process_document(doc_id: str, background_tasks: BackgroundTasks):
    """Trigger or re-trigger processing for an uploaded document."""
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    background_tasks.add_task(process_pdf_document, doc_id)
    return doc

@router.delete("/{doc_id}")
def delete_doc(doc_id: str):
    """Delete document, its indexed ChromaDB vectors, and related data."""
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    remove_document(doc_id)
    return {"message": f"Document {doc_id} deleted successfully."}
