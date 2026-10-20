from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Document Schemas
class DocumentResponse(BaseModel):
    id: str
    filename: str
    company: str
    fiscal_year: str
    upload_date: str
    num_pages: int = 0
    num_chunks: int = 0
    processing_status: str
    chroma_collection: Optional[str] = "financial_docs"
    error_message: Optional[str] = None
    file_path: str
    file_size: int = 0

class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str

class SeedDocument(BaseModel):
    filename: str
    file_path: str
    file_size: int
    detected_company: str
    detected_year: str
    is_indexed: bool
    document_id: Optional[str] = None

class SeedIndexRequest(BaseModel):
    filename: str
    company: str
    fiscal_year: str

# Financial Metric Schemas
class FinancialMetricItem(BaseModel):
    id: Optional[str] = None
    document_id: Optional[str] = None
    metric: str
    value: Optional[str] = None
    unit: Optional[str] = None
    period: Optional[str] = None
    company: str
    fiscal_year: Optional[str] = None
    source_document: Optional[str] = None
    page: Optional[int] = None
    source_text: Optional[str] = None
    is_calculated: bool = False
    calculation_formula: Optional[str] = None

class FinancialMetricsResponse(BaseModel):
    document_id: str
    company: str
    fiscal_year: str
    metrics: List[FinancialMetricItem]
    calculated_ratios: List[FinancialMetricItem]

# Red Flag Schemas
class RedFlagItem(BaseModel):
    id: Optional[str] = None
    document_id: Optional[str] = None
    company: str
    fiscal_year: str
    title: str
    description: str
    evidence: str
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    source_document: Optional[str] = None
    page: Optional[int] = None

class RedFlagsResponse(BaseModel):
    items: List[RedFlagItem]
    total: int

# Citation Schemas
class Citation(BaseModel):
    source_document: str
    page: int
    snippet: Optional[str] = None

# Research Schemas
class ResearchRequest(BaseModel):
    question: str
    company: Optional[str] = None
    fiscal_year: Optional[str] = None
    document_id: Optional[str] = None

class ResearchResponse(BaseModel):
    question: str
    company: Optional[str] = None
    answer: str
    sources: List[Citation]
    is_grounded: bool = True
    iterations_used: int = 1

class ResearchHistoryItem(BaseModel):
    id: str
    question: str
    company: Optional[str] = None
    created_at: str
    answer: str
    sources: List[Citation]

# Comparison Schemas
class ComparisonRequest(BaseModel):
    company_a: str
    company_b: str
    fiscal_year_a: Optional[str] = None
    fiscal_year_b: Optional[str] = None

class MetricComparisonRow(BaseModel):
    metric: str
    company_a_val: Optional[str] = None
    company_a_page: Optional[int] = None
    company_b_val: Optional[str] = None
    company_b_page: Optional[int] = None
    difference_note: Optional[str] = None

class ComparisonResponse(BaseModel):
    company_a: str
    company_b: str
    year_a: Optional[str] = None
    year_b: Optional[str] = None
    metrics_comparison: List[MetricComparisonRow]
    summary: str
    sources: List[Citation]

# Report Schemas
class ReportGenerateRequest(BaseModel):
    document_id: str
    title: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    title: str
    company: str
    fiscal_year: str
    file_path: str
    created_at: str
    download_url: str

class ReportDetail(ReportResponse):
    sections: Dict[str, Any]

# Settings Schemas
class SettingsResponse(BaseModel):
    app_name: str
    llm_model: str
    gemini_api_key_configured: bool = False
    device: str
    temperature: float
    max_new_tokens: int
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    max_retrieval_steps: int
    max_file_size_mb: int

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: Optional[float] = None
    max_new_tokens: Optional[int] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    top_k: Optional[int] = None
    max_retrieval_steps: Optional[int] = None

# Health Schema
class HealthResponse(BaseModel):
    status: str
    app_name: str
    llm_model: str
    device: str
    embedding_model: str
    database_status: str
    chromadb_status: str
    indexed_documents_count: int
