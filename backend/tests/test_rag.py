import pytest
from langchain_core.documents import Document
from backend.app.rag.chunking import chunk_page_contents
from backend.app.services.citation_service import validate_citations

def test_chunking_and_metadata_preservation():
    pages = [
        {"page": 1, "text": "Apple Inc. reported record revenue of $383 billion in fiscal year 2024. Services grew significantly."},
        {"page": 2, "text": "Net income for the year was $96 billion compared to $99 billion in 2023. Total debt was $106 billion."}
    ]

    chunks = chunk_page_contents(
        pages=pages,
        document_id="test_doc_001",
        document_name="apple_10k_2024.pdf",
        company="Apple",
        fiscal_year="2024",
        chunk_size=100,
        chunk_overlap=20,
    )

    assert len(chunks) >= 2
    # Verify metadata preservation on every chunk
    for chunk in chunks:
        assert chunk.metadata["document_id"] == "test_doc_001"
        assert chunk.metadata["document_name"] == "apple_10k_2024.pdf"
        assert chunk.metadata["company"] == "Apple"
        assert chunk.metadata["year"] == "2024"
        assert chunk.metadata["page"] in [1, 2]
        assert "chunk_id" in chunk.metadata

def test_citation_validation_valid():
    retrieved_docs = [
        Document(
            page_content="Revenue for FY2024 was $383,285 million.",
            metadata={"document_name": "apple_2024.pdf", "page": 24, "company": "Apple"}
        ),
        Document(
            page_content="Net income was $93,736 million.",
            metadata={"document_name": "apple_2024.pdf", "page": 27, "company": "Apple"}
        )
    ]

    answer = "Apple reported revenue of $383,285 million [Source: apple_2024.pdf, p. 24] and net income of $93,736 million [Source: apple_2024.pdf, p. 27]."
    sanitized, citations, is_grounded = validate_citations(answer, retrieved_docs)

    assert is_grounded is True
    assert len(citations) == 2
    assert citations[0].page == 24
    assert citations[1].page == 27
    assert "[Source: apple_2024.pdf, p. 24]" in sanitized

def test_citation_validation_hallucinated_page():
    retrieved_docs = [
        Document(
            page_content="Revenue for FY2024 was $383,285 million.",
            metadata={"document_name": "apple_2024.pdf", "page": 24, "company": "Apple"}
        )
    ]

    # Page 999 does not exist in retrieved docs!
    answer = "Apple reported revenue on page 999 [Source: apple_2024.pdf, p. 999]."
    sanitized, citations, is_grounded = validate_citations(answer, retrieved_docs)

    # Hallucinated page must be flagged/removed and not marked valid
    assert "[Source unverified]" in sanitized or not citations

def test_langchain_lcel_prompt_and_parser():
    from backend.app.llm.prompts import research_prompt_template
    from langchain_core.output_parsers import StrOutputParser

    assert research_prompt_template is not None
    prompt_value = research_prompt_template.invoke({
        "context": "Revenue was $100B [Source: doc.pdf, p. 1]",
        "question": "What was revenue?"
    })
    text = prompt_value.to_string()
    assert "What was revenue?" in text
    assert "$100B" in text
    parser = StrOutputParser()
    parsed = parser.invoke("Test LLM Answer")
    assert parsed == "Test LLM Answer"

def test_company_resolution_and_statement_retrieval(monkeypatch):
    import backend.app.rag.retriever as retriever
    monkeypatch.setattr(retriever, "get_all_indexed_companies", lambda: ["ACCCENTURE", "Amazon", "Acme Technologies"])
    from backend.app.rag.retriever import resolve_company_name

    # Test typo resolution (e.g. 2 C's vs 3 C's registered in Chroma: ACCCENTURE)
    res_input = resolve_company_name(input_company="Accenture")
    assert res_input == "ACCCENTURE"

    # Test resolution directly from query text
    res_query = resolve_company_name(query="What was Accenture's total revenue in fiscal year 2025?")
    assert res_query == "ACCCENTURE"

    # Test Amazon
    res_amazon = resolve_company_name(query="What was Amazon's total net sales in 2024?")
    assert res_amazon == "Amazon"

    # Test Acme
    res_acme = resolve_company_name(query="What was Acme's revenue?")
    assert res_acme == "Acme Technologies"
