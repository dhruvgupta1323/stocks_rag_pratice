from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class FinancialMetricRead(BaseModel):
    id: str
    company_id: str
    metric_name: str
    value: float
    unit: str
    currency: str
    reporting_period: str
    period_type: str  # quarterly, annual, ttm, ytd
    reported_at: Optional[datetime] = None
    source_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CompanyFinancialsResponse(BaseModel):
    company_id: str
    company_name: str
    symbol: str
    annual_metrics: List[FinancialMetricRead]
    quarterly_metrics: List[FinancialMetricRead]
    ttm_metrics: List[FinancialMetricRead]
    calculated_ratios: Dict[str, Any]

