from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QuoteRead(BaseModel):
    id: Optional[str] = None
    instrument_id: str
    symbol: str
    exchange: str
    last_price: float
    open: float
    high: float
    low: float
    previous_close: float
    change: float
    change_percent: float
    volume: int
    provider: str
    market_timestamp: datetime
    fetched_at: datetime
    data_status: str  # realtime, delayed, cached, mock, unavailable
    currency: str = "INR"

    model_config = ConfigDict(from_attributes=True)


class PriceBarRead(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    model_config = ConfigDict(from_attributes=True)


class HistoricalBarsResponse(BaseModel):
    instrument_id: str
    symbol: str
    exchange: str
    interval: str
    bars: List[PriceBarRead]
    provider: str
    data_status: str

    model_config = ConfigDict(from_attributes=True)


class StockOverview(BaseModel):
    instrument_id: str
    company_id: str
    name: str
    symbol: str
    exchange: str
    sector: str
    industry: str
    description: Optional[str] = None
    quote: QuoteRead
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    market_cap_crores: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    data_status: str
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)

