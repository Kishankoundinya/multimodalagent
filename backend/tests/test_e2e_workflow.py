import os
import uuid
import pytest
from backend.app.database.database import (
    init_db,
    insert_document,
    get_document_by_id,
    get_metrics_for_document,
    get_red_flags_for_document,
    get_all_reports,
)
from backend.app.services.document_service import process_pdf_document
from backend.app.rag.vector_store import search_similar_chunks
from backend.app.agents.extraction_agent import extraction_agent_node
from backend.app.agents.red_flag_agent import red_flag_agent_node
from backend.app.agents.report_agent import report_agent_node

def test_full_e2e_pipeline():
    init_db()

    # 1. Setup test document
    sample_pdf = "data/seed/Acme_Annual_Report_2024.pdf"
    assert os.path.exists(sample_pdf), "Sample PDF should exist for testing"

    doc_id = str(uuid.uuid4())
    doc_data = {
        "id": doc_id,
        "filename": "Acme_Annual_Report_2024.pdf",
        "company": "Acme Technologies",
        "fiscal_year": "2024",
        "file_path": os.path.abspath(sample_pdf),
        "file_size": os.path.getsize(sample_pdf),
        "processing_status": "Uploading",
    }
    insert_document(doc_data)

    # 2. Process document (Extract -> Chunk -> Embed -> Index in ChromaDB)
    processed = process_pdf_document(doc_id)
    assert processed["processing_status"] == "Completed"
    assert processed["num_pages"] == 3
    assert processed["num_chunks"] > 0

    # 3. Verify ChromaDB retrieval
    chunks = search_similar_chunks("total net sales revenue 2024", top_k=3, filter_dict={"company": "Acme Technologies"})
    assert len(chunks) > 0
    top_chunk = chunks[0]
    assert "page" in top_chunk.metadata
    assert top_chunk.metadata["company"] == "Acme Technologies"
    assert "150,000" in top_chunk.page_content or "sales" in top_chunk.page_content.lower()

    # 4. Run Extraction Agent
    state = {
        "request_type": "metrics",
        "document_id": doc_id,
        "company": "Acme Technologies",
        "fiscal_year": "2024",
    }
    ext_result = extraction_agent_node(state)
    stored_metrics = get_metrics_for_document(doc_id)
    assert len(stored_metrics) > 0

    metric_names = [m["metric"] for m in stored_metrics]
    assert "Revenue" in metric_names
    assert "Net Income" in metric_names

    # Verify calculated ratios
    calc_ratios = [m for m in stored_metrics if m["is_calculated"]]
    assert len(calc_ratios) > 0
    ratio_names = [r["metric"] for r in calc_ratios]
    assert "Net Profit Margin" in ratio_names
    assert "Debt-to-Equity Ratio" in ratio_names

    # Check that Net Profit Margin = 30000 / 150000 * 100 = 20.00%
    npm = next(r for r in calc_ratios if r["metric"] == "Net Profit Margin")
    assert "20.00%" in npm["value"]

    # 5. Run Red Flag Agent
    rf_state = {
        "request_type": "red_flags",
        "document_id": doc_id,
        "company": "Acme Technologies",
        "fiscal_year": "2024",
    }
    rf_result = red_flag_agent_node(rf_state)
    stored_flags = get_red_flags_for_document(doc_id)
    # The sample PDF contains interest rate and liquidity risk factors
    assert isinstance(stored_flags, list)

    # 6. Run Report Agent (ReportLab PDF generation)
    rep_state = {
        "request_type": "report",
        "document_id": doc_id,
        "company": "Acme Technologies",
        "fiscal_year": "2024",
        "metrics": stored_metrics,
        "red_flags": stored_flags,
    }
    rep_result = report_agent_node(rep_state)
    assert "report_results" in rep_result
    pdf_path = rep_result["report_results"]["file_path"]
    assert os.path.exists(pdf_path), f"Report PDF was not generated at {pdf_path}"
    assert os.path.getsize(pdf_path) > 1000, "Report PDF is empty or corrupt"

    all_reports = get_all_reports()
    assert any(r["id"] == rep_result["report_results"]["id"] for r in all_reports)
