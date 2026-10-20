from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.documents import Document

class AnalysisState(TypedDict, total=False):
    # Workflow routing
    request_type: str  # "document", "research", "metrics", "red_flags", "comparison", "report"
    
    # Context & Parameters
    document_id: Optional[str]
    company: Optional[str]
    company_b: Optional[str]
    fiscal_year: Optional[str]
    fiscal_year_b: Optional[str]
    question: Optional[str]
    
    # Retrieval
    retrieved_documents: List[Document]
    retrieved_documents_b: List[Document]
    
    # Research findings
    raw_answer: Optional[str]
    final_answer: Optional[str]
    citations: List[Dict[str, Any]]
    is_grounded: bool
    iterations_used: int
    
    # Structured outputs from specific agents
    metrics: List[Dict[str, Any]]
    calculated_ratios: List[Dict[str, Any]]
    red_flags: List[Dict[str, Any]]
    comparison_results: Dict[str, Any]
    report_results: Dict[str, Any]
    
    # Status / Errors
    error: Optional[str]
