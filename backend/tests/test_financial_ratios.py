import pytest
from backend.app.analytics.financial_ratios import FinancialAnalytics


def test_growth_rate_positive():
    res = FinancialAnalytics.calculate_growth_rate(current_value=120.0, previous_value=100.0)
    assert res["growth_pct"] == 20.0
    assert res["status"] == "valid"


def test_growth_rate_zero_denominator():
    res = FinancialAnalytics.calculate_growth_rate(current_value=50.0, previous_value=0.0)
    assert res["growth_pct"] is None
    assert res["status"] == "zero_denominator_cannot_calculate"


def test_valuation_ratios():
    res = FinancialAnalytics.calculate_valuation_ratios(
        market_price=3000.0,
        shares_outstanding=1000000,
        eps=100.0,
        book_value_per_share=1500.0,
    )
    assert res["pe_ratio"] == 30.0
    assert res["pb_ratio"] == 2.0


def test_compare_companies():
    comp_a = {"name": "TCS", "metrics": {"Revenue": 240000.0, "Operating Margin": 25.0}}
    comp_b = {"name": "INFY", "metrics": {"Revenue": 150000.0, "Operating Margin": 21.0}}
    comp = FinancialAnalytics.compare_companies(comp_a, comp_b)
    assert comp["metrics"]["Revenue"]["difference"] == 90000.0
    assert comp["metrics"]["Operating Margin"]["difference"] == 4.0

