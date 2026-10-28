from typing import Dict, Any, List, Optional
import math
from backend.app.core.exceptions import CalculationException


class FinancialAnalytics:
    """Deterministic financial analytics and fundamental metrics calculations."""

    @staticmethod
    def calculate_growth_rate(
        current_value: float, previous_value: float, period_label: str = "YoY"
    ) -> Dict[str, Any]:
        """Calculate percentage growth rate with zero and negative denominator checks."""
        if previous_value is None or math.isnan(previous_value):
            return {"growth_pct": None, "status": "missing_previous_period"}
        if previous_value == 0:
            return {"growth_pct": None, "status": "zero_denominator_cannot_calculate"}

        # For negative base values (e.g. from loss to profit), use absolute base
        growth = ((current_value - previous_value) / abs(previous_value)) * 100.0
        return {
            "growth_pct": round(growth, 2),
            "period": period_label,
            "status": "valid",
        }

    @staticmethod
    def calculate_valuation_ratios(
        market_price: float,
        shares_outstanding: float,
        eps: Optional[float] = None,
        book_value_per_share: Optional[float] = None,
        sales_per_share: Optional[float] = None,
    ) -> Dict[str, Optional[float]]:
        """Calculate PE, PB, and PS ratios deterministically."""
        pe = round(market_price / eps, 2) if (eps and eps > 0) else None
        pb = round(market_price / book_value_per_share, 2) if (book_value_per_share and book_value_per_share > 0) else None
        ps = round(market_price / sales_per_share, 2) if (sales_per_share and sales_per_share > 0) else None

        return {
            "pe_ratio": pe,
            "pb_ratio": pb,
            "ps_ratio": ps,
        }

    @staticmethod
    def calculate_leverage_ratios(
        total_debt: float,
        total_equity: float,
        operating_income: Optional[float] = None,
        interest_expense: Optional[float] = None,
    ) -> Dict[str, Optional[float]]:
        """Calculate Debt-to-Equity and Interest Coverage ratios."""
        debt_to_equity = round(total_debt / total_equity, 2) if (total_equity and total_equity > 0) else None
        interest_coverage = (
            round(operating_income / interest_expense, 2)
            if (operating_income is not None and interest_expense and interest_expense > 0)
            else None
        )

        return {
            "debt_to_equity": debt_to_equity,
            "interest_coverage": interest_coverage,
        }

    @staticmethod
    def compare_companies(
        company_a: Dict[str, Any], company_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Align and compare metrics between two companies with unit and currency consistency."""
        metrics_a = company_a.get("metrics", {})
        metrics_b = company_b.get("metrics", {})

        comparison: Dict[str, Any] = {
            "company_a": company_a.get("name"),
            "company_b": company_b.get("name"),
            "currency": "INR",
            "metrics": {},
        }

        shared_keys = set(metrics_a.keys()).union(set(metrics_b.keys()))
        for key in shared_keys:
            val_a = metrics_a.get(key)
            val_b = metrics_b.get(key)
            diff = None
            if val_a is not None and val_b is not None:
                diff = round(val_a - val_b, 2)

            comparison["metrics"][key] = {
                "company_a_value": val_a,
                "company_b_value": val_b,
                "difference": diff,
            }

        return comparison

