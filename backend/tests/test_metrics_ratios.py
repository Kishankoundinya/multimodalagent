import pytest
from backend.app.agents.extraction_agent import (
    clean_numerical_value,
    calculate_ratios,
)

def test_clean_numerical_value():
    assert clean_numerical_value("$383,285 million") == 383285.0
    assert clean_numerical_value("93,736") == 93736.0
    assert clean_numerical_value("24.45%") == 24.45
    assert clean_numerical_value(None) is None
    assert clean_numerical_value("Not available") is None

def test_calculate_ratios():
    extracted_map = {
        "Revenue": {"value": "$383,285 million", "page": 24},
        "Net Income": {"value": "$93,736 million", "page": 27},
        "Total Debt": {"value": "$106,629 million", "page": 32},
        "Equity": {"value": "$66,750 million", "page": 35},
        "Total Assets": {"value": "$364,980 million", "page": 30},
    }

    ratios = calculate_ratios(extracted_map, company="Apple", fiscal_year="2024", doc_name="apple_10k.pdf")
    ratio_names = [r["metric"] for r in ratios]

    # Verify all 4 required calculated ratios are present
    assert "Net Profit Margin" in ratio_names
    assert "Debt-to-Equity Ratio" in ratio_names
    assert "ROA" in ratio_names
    assert "ROE" in ratio_names

    # Check that each ratio is explicitly labeled as calculated
    for r in ratios:
        assert r["is_calculated"] is True
        assert "Calculated from source values" in r["source_text"]
        assert "p." in r["calculation_formula"]

    # Verify calculations:
    # Net Profit Margin = (93736 / 383285) * 100 ≈ 24.46%
    npm = next(r for r in ratios if r["metric"] == "Net Profit Margin")
    assert "24.46%" in npm["value"]

    # Debt-to-Equity = 106629 / 66750 ≈ 1.60
    dte = next(r for r in ratios if r["metric"] == "Debt-to-Equity Ratio")
    assert "1.60" in dte["value"]
