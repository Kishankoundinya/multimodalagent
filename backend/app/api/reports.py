import os
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.app.models.schemas import (
    ReportGenerateRequest,
    ReportResponse,
    ReportDetail,
)
from backend.app.database.database import (
    get_all_reports,
    get_report_by_id,
    get_document_by_id,
)
from backend.app.graph.workflow import run_analysis_workflow
from backend.app.utils.logging import logger

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("", response_model=List[ReportResponse])
def list_reports():
    """List all previously generated analyst PDF reports."""
    reports = get_all_reports()
    results = []
    for r in reports:
        results.append(ReportResponse(
            id=r["id"],
            title=r["title"],
            company=r["company"],
            fiscal_year=r["fiscal_year"],
            file_path=r["file_path"],
            created_at=r["created_at"],
            download_url=f"/api/reports/{r['id']}/download",
        ))
    return results

@router.get("/{report_id}", response_model=ReportDetail)
def get_report(report_id: str):
    """Get report metadata and section summaries."""
    r = get_report_by_id(report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found.")
    return ReportDetail(
        id=r["id"],
        title=r["title"],
        company=r["company"],
        fiscal_year=r["fiscal_year"],
        file_path=r["file_path"],
        created_at=r["created_at"],
        download_url=f"/api/reports/{r['id']}/download",
        sections=r.get("sections", {}),
    )

@router.get("/{report_id}/download")
def download_report_pdf(report_id: str):
    """Download the generated ReportLab PDF file."""
    r = get_report_by_id(report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found.")
    pdf_path = r["file_path"]
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF report file not found on disk.")

    filename = os.path.basename(pdf_path)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename,
    )

@router.post("/generate", response_model=ReportResponse)
def generate_report(req: ReportGenerateRequest):
    """
    Trigger Report Agent workflow to produce a professional 10-section PDF report.
    """
    doc = get_document_by_id(req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    logger.info(f"Triggering report generation for document {req.document_id} ({doc['company']})...")

    try:
        final_state = run_analysis_workflow({
            "request_type": "report",
            "document_id": req.document_id,
            "company": doc["company"],
            "fiscal_year": doc["fiscal_year"],
        })
        rep_res = final_state.get("report_results")
        if not rep_res:
            raise HTTPException(status_code=500, detail="Report generation did not return valid output.")
        return ReportResponse(**rep_res)
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")
