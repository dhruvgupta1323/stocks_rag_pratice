from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class CompanyRead(BaseModel):
    id: str
    name: str
    sector: str
    industry: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InstrumentRead(BaseModel):
    id: str
    company_id: str
    exchange: str
    symbol: str
    isin: Optional[str] = None
    provider_instrument_id: str
    currency: str
    active: bool
    company: Optional[CompanyRead] = None

    model_config = ConfigDict(from_attributes=True)


class StockSearchResult(BaseModel):
    instrument_id: str
    company_id: str
    name: str
    symbol: str
    exchange: str
    isin: Optional[str] = None
    sector: str
    industry: str
    last_price: Optional[float] = None
    currency: str = "INR"

    model_config = ConfigDict(from_attributes=True)

