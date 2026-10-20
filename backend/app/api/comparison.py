from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import ComparisonRequest, ComparisonResponse
from backend.app.graph.workflow import run_analysis_workflow
from backend.app.utils.logging import logger

router = APIRouter(prefix="/api/compare", tags=["Comparison"])

@router.post("", response_model=ComparisonResponse)
def compare_companies(req: ComparisonRequest):
    """
    Compare two indexed companies on key financial metrics with exact page citations.
    """
    if not req.company_a or not req.company_b:
        raise HTTPException(status_code=400, detail="Both company_a and company_b are required.")

    initial_state = {
        "request_type": "comparison",
        "company": req.company_a.strip(),
        "company_b": req.company_b.strip(),
        "fiscal_year": req.fiscal_year_a.strip() if req.fiscal_year_a else None,
        "fiscal_year_b": req.fiscal_year_b.strip() if req.fiscal_year_b else None,
    }

    try:
        final_state = run_analysis_workflow(initial_state)
        comp_res = final_state.get("comparison_results")
        if not comp_res:
            raise HTTPException(status_code=500, detail="Comparison Agent failed to produce results.")
        return comp_res
    except Exception as e:
        logger.error(f"Error in comparison endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {e}")
