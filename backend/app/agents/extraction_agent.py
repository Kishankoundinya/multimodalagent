import re
import uuid
from typing import Dict, Any, List, Optional
from langchain_core.documents import Document

from backend.app.graph.state import AnalysisState
from backend.app.rag.retriever import retrieve_relevant_chunks, format_context_with_citations, resolve_company_name
from backend.app.llm.llm_provider import get_shared_llm
from backend.app.llm.prompts import EXTRACTION_PROMPT_TEMPLATE, SYSTEM_PROMPT_BASE
from backend.app.database.database import insert_metrics, get_metrics_for_document
from backend.app.utils.logging import logger

CORE_METRIC_NAMES = [
    "Revenue",
    "Net Income",
    "Operating Income",
    "EBITDA",
    "Total Assets",
    "Total Liabilities",
    "Total Debt",
    "Cash",
    "Equity",
    "EPS",
    "Operating Margin",
    "Net Profit Margin",
    "ROE",
    "ROA",
    "Current Ratio",
    "Debt-to-Equity Ratio"
]

def clean_numerical_value(val_str: str) -> Optional[float]:
    """Parse numeric float from a string like '$383,285 million' or '3.5%'."""
    if not val_str:
        return None
    # Remove currency signs and commas
    cleaned = re.sub(r"[^\d.-]", "", val_str)
    try:
        return float(cleaned)
    except ValueError:
        return None

def extract_metric_with_regex(metric_name: str, docs: List[Document]) -> Optional[Dict[str, Any]]:
    """
    Regex fallback to extract stated financial lines directly from text chunks.
    Ensures 100% strict grounding without LLM hallucination.
    """
    patterns = {
        "Revenue": [
            r"(?:total\s+)?(?:net\s+)?(?:sales|revenue)[^\d\n]*?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)",
            r"(?:revenue|sales)\s+(?:was|of)\s+\$?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)"
        ],
        "Net Income": [
            r"net\s+income[^\d\n]*?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)",
            r"net\s+(?:earnings|loss)[^\d\n]*?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)"
        ],
        "Operating Income": [
            r"operating\s+income[^\d\n]*?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)"
        ],
        "Total Assets": [
            r"total\s+assets[^\d\n]*?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)"
        ],
        "Total Liabilities": [
            r"total\s+liabilities[^\d\n]*?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)"
        ],
        "Total Debt": [
            r"total\s+debt[^\d\n]*?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)",
            r"commercial\s+paper\s+and\s+term\s+debt[^\d\n]*?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)"
        ],
        "Cash": [
            r"cash\s+and\s+cash\s+equivalents[^\d\n]*?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)"
        ],
        "Equity": [
            r"(?:total\s+)?shareholders['’]?\s+equity[^\d\n]*?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)"
        ],
        "EPS": [
            r"diluted\s+earnings\s+per\s+share[^\d\n]*?\$?\s*([0-9]+(?:\.[0-9]+)?)",
            r"diluted\s+(?:eps|earnings\s+per\s+share)[^\d\n]*?\$?\s*([0-9]+(?:\.[0-9]+)?)"
        ]
    }

    if metric_name not in patterns:
        return None

    for doc in docs:
        text = doc.page_content
        for pattern in patterns[metric_name]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = match.group(1)
                page = doc.metadata.get("page", 1)
                doc_name = doc.metadata.get("document_name", "Report")
                # Grab surrounding sentence
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                source_sentence = text[start:end].replace("\n", " ").strip()
                return {
                    "metric": metric_name,
                    "value": f"${val}",
                    "unit": "USD",
                    "period": doc.metadata.get("year", "FY"),
                    "page": page,
                    "source_document": doc_name,
                    "source_text": source_sentence,
                }
    return None

def calculate_ratios(extracted_map: Dict[str, Dict[str, Any]], company: str, fiscal_year: str, doc_name: str) -> List[Dict[str, Any]]:
    """
    Strictly calculate financial ratios only when required source metrics are available.
    Labels clearly: 'Calculated from source values'.
    """
    calculated = []

    # 1. Net Profit Margin = (Net Income / Revenue) * 100
    if "Net Income" in extracted_map and "Revenue" in extracted_map:
        ni = clean_numerical_value(extracted_map["Net Income"]["value"])
        rev = clean_numerical_value(extracted_map["Revenue"]["value"])
        if ni is not None and rev is not None and rev > 0:
            ratio_val = (ni / rev) * 100
            ni_val_str = extracted_map["Net Income"]["value"]
            rev_val_str = extracted_map["Revenue"]["value"]
            source_pages = f"p. {extracted_map['Net Income']['page']} and p. {extracted_map['Revenue']['page']}"
            calculated.append({
                "metric": "Net Profit Margin",
                "value": f"{ratio_val:.2f}%",
                "unit": "%",
                "period": fiscal_year,
                "fiscal_year": fiscal_year,
                "company": company,
                "source_document": doc_name,
                "page": extracted_map["Net Income"]["page"],
                "source_text": f"Calculated from source values: Net Income ({ni_val_str}) / Revenue ({rev_val_str}) * 100",
                "is_calculated": True,
                "calculation_formula": f"Net Income ({ni_val_str}) / Revenue ({rev_val_str}) * 100 [{source_pages}]"
            })

    # 2. Debt-to-Equity = Total Debt / Shareholders' Equity
    if "Total Debt" in extracted_map and "Equity" in extracted_map:
        debt = clean_numerical_value(extracted_map["Total Debt"]["value"])
        equity = clean_numerical_value(extracted_map["Equity"]["value"])
        if debt is not None and equity is not None and equity != 0:
            ratio_val = debt / equity
            debt_str = extracted_map["Total Debt"]["value"]
            eq_str = extracted_map["Equity"]["value"]
            source_pages = f"p. {extracted_map['Total Debt']['page']} and p. {extracted_map['Equity']['page']}"
            calculated.append({
                "metric": "Debt-to-Equity Ratio",
                "value": f"{ratio_val:.2f}",
                "unit": "ratio",
                "period": fiscal_year,
                "fiscal_year": fiscal_year,
                "company": company,
                "source_document": doc_name,
                "page": extracted_map["Total Debt"]["page"],
                "source_text": f"Calculated from source values: Total Debt ({debt_str}) / Equity ({eq_str})",
                "is_calculated": True,
                "calculation_formula": f"Total Debt ({debt_str}) / Equity ({eq_str}) [{source_pages}]"
            })

    # 3. ROA = (Net Income / Total Assets) * 100
    if "Net Income" in extracted_map and "Total Assets" in extracted_map:
        ni = clean_numerical_value(extracted_map["Net Income"]["value"])
        assets = clean_numerical_value(extracted_map["Total Assets"]["value"])
        if ni is not None and assets is not None and assets > 0:
            ratio_val = (ni / assets) * 100
            ni_str = extracted_map["Net Income"]["value"]
            assets_str = extracted_map["Total Assets"]["value"]
            source_pages = f"p. {extracted_map['Net Income']['page']} and p. {extracted_map['Total Assets']['page']}"
            calculated.append({
                "metric": "ROA",
                "value": f"{ratio_val:.2f}%",
                "unit": "%",
                "period": fiscal_year,
                "fiscal_year": fiscal_year,
                "company": company,
                "source_document": doc_name,
                "page": extracted_map["Net Income"]["page"],
                "source_text": f"Calculated from source values: Net Income ({ni_str}) / Total Assets ({assets_str}) * 100",
                "is_calculated": True,
                "calculation_formula": f"Net Income ({ni_str}) / Total Assets ({assets_str}) * 100 [{source_pages}]"
            })

    # 4. ROE = (Net Income / Shareholders' Equity) * 100
    if "Net Income" in extracted_map and "Equity" in extracted_map:
        ni = clean_numerical_value(extracted_map["Net Income"]["value"])
        equity = clean_numerical_value(extracted_map["Equity"]["value"])
        if ni is not None and equity is not None and equity != 0:
            ratio_val = (ni / equity) * 100
            ni_str = extracted_map["Net Income"]["value"]
            eq_str = extracted_map["Equity"]["value"]
            source_pages = f"p. {extracted_map['Net Income']['page']} and p. {extracted_map['Equity']['page']}"
            calculated.append({
                "metric": "ROE",
                "value": f"{ratio_val:.2f}%",
                "unit": "%",
                "period": fiscal_year,
                "fiscal_year": fiscal_year,
                "company": company,
                "source_document": doc_name,
                "page": extracted_map["Net Income"]["page"],
                "source_text": f"Calculated from source values: Net Income ({ni_str}) / Equity ({eq_str}) * 100",
                "is_calculated": True,
                "calculation_formula": f"Net Income ({ni_str}) / Equity ({eq_str}) * 100 [{source_pages}]"
            })

    return calculated

def extraction_agent_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Extraction Agent:
    Extracts financial metrics from retrieved documents and computes verified ratios.
    """
    doc_id = state.get("document_id")
    company = resolve_company_name(state.get("company")) or state.get("company", "Company")
    fiscal_year = state.get("fiscal_year", "FY")

    logger.info(f"[Extraction Agent] Extracting metrics for {company} ({fiscal_year})...")

    # Retrieve relevant financial sections: Statement of Operations, Balance Sheet, Cash Flows
    queries = [
        f"{company} consolidated statements of operations revenue net income operating income",
        f"{company} consolidated balance sheets total assets liabilities total debt equity cash",
        f"{company} earnings per share diluted operating margin EBITDA"
    ]

    all_docs: List[Document] = []
    for q in queries:
        docs = retrieve_relevant_chunks(q, company=company, document_id=doc_id, top_k=4)
        for d in docs:
            if not any(d.metadata.get("chunk_id") == existing.metadata.get("chunk_id") for existing in all_docs):
                all_docs.append(d)

    if not all_docs:
        logger.warning("[Extraction Agent] No chunks retrieved for extraction.")
        return {"metrics": [], "calculated_ratios": []}

    context = format_context_with_citations(all_docs)
    doc_name = all_docs[0].metadata.get("document_name", "Annual Report")

    extracted_metrics_map: Dict[str, Dict[str, Any]] = {}

    # Step 1: Use regex table parsing across retrieved chunks to find exact stated numbers
    for metric_name in CORE_METRIC_NAMES:
        extracted = extract_metric_with_regex(metric_name, all_docs)
        if extracted:
            extracted_metrics_map[metric_name] = extracted

    # Step 2: Use SharedLLM only if core metrics were not fully captured by direct statement parsing
    core_present = ("Revenue" in extracted_metrics_map and "Net Income" in extracted_metrics_map)
    if not core_present or len(extracted_metrics_map) < 4:
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(
            context=context,
            company=company,
            fiscal_year=fiscal_year
        )

        try:
            llm = get_shared_llm()
            llm_output = llm.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT_BASE, max_new_tokens=160)
            
            # Parse lines like: METRIC: Revenue | VALUE: $383,285 million | PERIOD: FY2024 | PAGE: 24 | TEXT: ...
            for line in llm_output.split("\n"):
                line = line.strip()
                if not line.startswith("METRIC:"):
                    continue
                parts = [p.strip() for p in line.split("|")]
                item = {}
                for part in parts:
                    if ":" in part:
                        k, v = part.split(":", 1)
                        item[k.strip().lower()] = v.strip()
                
                m_name = item.get("metric")
                m_val = item.get("value")
                if m_name and m_val and m_val.lower() != "null" and m_name not in extracted_metrics_map:
                    try:
                        page_val = int(item.get("page", 1))
                    except ValueError:
                        page_val = all_docs[0].metadata.get("page", 1)
                    
                    extracted_metrics_map[m_name] = {
                        "metric": m_name,
                        "value": m_val,
                        "unit": "USD",
                        "period": item.get("period", fiscal_year),
                        "page": page_val,
                        "source_document": doc_name,
                        "source_text": item.get("text", "")
                    }
        except Exception as e:
            logger.warning(f"[Extraction Agent] LLM parsing encountered warning ({e}), relying on verified regex extractions.")

    # Convert map to list and format
    final_metrics: List[Dict[str, Any]] = []
    for metric_name, data in extracted_metrics_map.items():
        record = {
            "id": str(uuid.uuid4()),
            "document_id": doc_id or "unknown",
            "company": company,
            "fiscal_year": fiscal_year,
            "metric": metric_name,
            "value": data.get("value"),
            "unit": data.get("unit", "USD"),
            "period": data.get("period", fiscal_year),
            "source_document": data.get("source_document", doc_name),
            "page": data.get("page"),
            "source_text": data.get("source_text"),
            "is_calculated": False,
            "calculation_formula": None
        }
        final_metrics.append(record)

    # Step 3: Compute calculated ratios strictly from available source values
    calculated_ratios = calculate_ratios(extracted_metrics_map, company, fiscal_year, doc_name)
    for ratio in calculated_ratios:
        ratio["id"] = str(uuid.uuid4())
        ratio["document_id"] = doc_id or "unknown"
        final_metrics.append(ratio)

    # Persist in SQLite
    if final_metrics:
        insert_metrics(final_metrics)

    logger.info(f"[Extraction Agent] Extracted {len(final_metrics)} metrics (including {len(calculated_ratios)} calculated ratios).")
    return {
        "metrics": [m for m in final_metrics if not m.get("is_calculated")],
        "calculated_ratios": [m for m in final_metrics if m.get("is_calculated")]
    }
