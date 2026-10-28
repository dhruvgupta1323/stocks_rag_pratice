from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.exceptions import StockIntelligenceException
from backend.app.models.instrument import Instrument
from backend.app.models.financials import FinancialMetric
from backend.app.schemas.financials import FinancialMetricRead, CompanyFinancialsResponse
from backend.app.analytics.financial_ratios import FinancialAnalytics


class FinancialService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_company_financials(self, instrument_id: str) -> CompanyFinancialsResponse:
        stmt = (
            select(Instrument)
            .options(selectinload(Instrument.company))
            .where((Instrument.id == instrument_id) | (Instrument.symbol == instrument_id.upper()))
            .order_by(Instrument.exchange.desc())
        )
        res = await self.db.execute(stmt)
        inst = res.scalars().first()
        if not inst:
            raise StockIntelligenceException(f"Instrument '{instrument_id}' not found.")

        m_stmt = select(FinancialMetric).where(FinancialMetric.company_id == inst.company_id)
        m_res = await self.db.execute(m_stmt)
        all_metrics = m_res.scalars().all()

        annual = [FinancialMetricRead.model_validate(m) for m in all_metrics if m.period_type == "annual"]
        quarterly = [FinancialMetricRead.model_validate(m) for m in all_metrics if m.period_type == "quarterly"]
        ttm = [FinancialMetricRead.model_validate(m) for m in all_metrics if m.period_type == "ttm"]

        # Calculated ratios
        ratios: Dict[str, Any] = {}
        rev = next((m.value for m in all_metrics if m.metric_name == "Revenue"), None)
        pat = next((m.value for m in all_metrics if m.metric_name in ("Net Profit", "PAT")), None)
        pe = next((m.value for m in all_metrics if "PE" in m.metric_name), None)
        pb = next((m.value for m in all_metrics if "PB" in m.metric_name), None)
        op_margin = next((m.value for m in all_metrics if "Operating Margin" in m.metric_name), None)
        debt_equity = next((m.value for m in all_metrics if "Debt to Equity" in m.metric_name), None)

        if rev and pat:
            net_margin = round((pat / rev) * 100.0, 2)
            ratios["net_profit_margin_pct"] = net_margin
        if op_margin:
            ratios["operating_margin_pct"] = op_margin
        if pe:
            ratios["pe_ratio"] = pe
        if pb:
            ratios["pb_ratio"] = pb
        if debt_equity is not None:
            ratios["debt_to_equity"] = debt_equity

        return CompanyFinancialsResponse(
            company_id=inst.company_id,
            company_name=inst.company.name,
            symbol=inst.symbol,
            annual_metrics=annual,
            quarterly_metrics=quarterly,
            ttm_metrics=ttm,
            calculated_ratios=ratios,
        )
