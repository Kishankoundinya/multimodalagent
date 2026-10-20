from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.models.schemas import (
    FinancialMetricsResponse,
    FinancialMetricItem,
    RedFlagsResponse,
    RedFlagItem,
)
from backend.app.database.database import (
    get_document_by_id,
    get_metrics_for_document,
    get_red_flags_for_document,
    get_all_red_flags,
)
from backend.app.graph.workflow import run_analysis_workflow
from backend.app.utils.logging import logger

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])

@router.get("/red-flags", response_model=RedFlagsResponse)
def list_all_red_flags():
    """Retrieve all identified red flags across all companies."""
    items = get_all_red_flags()
    return RedFlagsResponse(items=[RedFlagItem(**item) for item in items], total=len(items))

@router.get("/{document_id}", response_model=FinancialMetricsResponse)
def get_document_metrics(document_id: str, auto_extract: bool = Query(True)):
    """
    Retrieve extracted financial metrics and calculated ratios for a document.
    Automatically triggers Extraction Agent if metrics are not yet indexed.
    """
    doc = get_document_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    existing_metrics = get_metrics_for_document(document_id)
    if not existing_metrics and auto_extract:
        # Trigger Extraction Agent via LangGraph
        logger.info(f"No stored metrics for doc {document_id}, executing Extraction Agent...")
        try:
            state = run_analysis_workflow({
                "request_type": "metrics",
                "document_id": document_id,
                "company": doc["company"],
                "fiscal_year": doc["fiscal_year"],
            })
            existing_metrics = get_metrics_for_document(document_id)
        except Exception as e:
            logger.error(f"Extraction agent execution failed: {e}")

    raw_metrics = [FinancialMetricItem(**m) for m in existing_metrics if not m.get("is_calculated")]
    ratios = [FinancialMetricItem(**m) for m in existing_metrics if m.get("is_calculated")]

    return FinancialMetricsResponse(
        document_id=document_id,
        company=doc["company"],
        fiscal_year=doc["fiscal_year"],
        metrics=raw_metrics,
        calculated_ratios=ratios,
    )

@router.post("/{document_id}/extract", response_model=FinancialMetricsResponse)
def force_extract_metrics(document_id: str):
    """Force re-extraction of metrics and ratios."""
    doc = get_document_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    run_analysis_workflow({
        "request_type": "metrics",
        "document_id": document_id,
        "company": doc["company"],
        "fiscal_year": doc["fiscal_year"],
    })
    metrics = get_metrics_for_document(document_id)
    raw_metrics = [FinancialMetricItem(**m) for m in metrics if not m.get("is_calculated")]
    ratios = [FinancialMetricItem(**m) for m in metrics if m.get("is_calculated")]

    return FinancialMetricsResponse(
        document_id=document_id,
        company=doc["company"],
        fiscal_year=doc["fiscal_year"],
        metrics=raw_metrics,
        calculated_ratios=ratios,
    )

@router.get("/{document_id}/red-flags", response_model=RedFlagsResponse)
def get_document_red_flags(document_id: str, auto_detect: bool = Query(True)):
    """Retrieve red flags for a specific document."""
    doc = get_document_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    flags = get_red_flags_for_document(document_id)
    if not flags and auto_detect:
        logger.info(f"No stored red flags for doc {document_id}, executing Red Flag Agent...")
        try:
            run_analysis_workflow({
                "request_type": "red_flags",
                "document_id": document_id,
                "company": doc["company"],
                "fiscal_year": doc["fiscal_year"],
            })
            flags = get_red_flags_for_document(document_id)
        except Exception as e:
            logger.error(f"Red flag agent execution failed: {e}")

    return RedFlagsResponse(items=[RedFlagItem(**f) for f in flags], total=len(flags))
