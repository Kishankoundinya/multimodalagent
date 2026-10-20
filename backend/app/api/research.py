from typing import List
from fastapi import APIRouter, HTTPException

from backend.app.models.schemas import (
    ResearchRequest,
    ResearchResponse,
    ResearchHistoryItem,
)
from backend.app.graph.workflow import run_analysis_workflow
from backend.app.database.database import get_research_history
from backend.app.utils.logging import logger

router = APIRouter(prefix="/api/research", tags=["Research"])

@router.post("", response_model=ResearchResponse)
def execute_research_query(req: ResearchRequest):
    """
    Execute conversational grounded research query using the Research Agent.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    initial_state = {
        "request_type": "research",
        "question": req.question.strip(),
        "company": req.company.strip() if req.company else None,
        "fiscal_year": req.fiscal_year.strip() if req.fiscal_year else None,
        "document_id": req.document_id,
    }

    try:
        final_state = run_analysis_workflow(initial_state)
        return ResearchResponse(
            question=req.question,
            company=req.company,
            answer=final_state.get("final_answer", "Information not found in the provided documents."),
            sources=final_state.get("citations", []),
            is_grounded=final_state.get("is_grounded", True),
            iterations_used=final_state.get("iterations_used", 1),
        )
    except Exception as e:
        logger.error(f"Research query execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Research processing error: {e}")

@router.get("/history", response_model=List[ResearchHistoryItem])
def get_past_research():
    """Retrieve full analysis and research query history."""
    return get_research_history()
