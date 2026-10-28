from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.services.stock_service import StockService
from backend.app.services.financial_service import FinancialService
from backend.app.services.research_service import ResearchService
from backend.app.research.report_generator import ResearchReportGenerator
from backend.app.schemas.instrument import StockSearchResult
from backend.app.schemas.market_data import StockOverview, HistoricalBarsResponse
from backend.app.schemas.financials import CompanyFinancialsResponse
from backend.app.schemas.research import StockNewsResponse

router = APIRouter(prefix="/stocks", tags=["Stocks & Market Data"])


@router.get("/search", response_model=List[StockSearchResult])
async def search_stocks(
    q: str = Query(..., min_length=1, description="Company name, symbol, or sector"),
    exchange: Optional[str] = Query(None, description="Filter by exchange (NSE, BSE)"),
    db: AsyncSession = Depends(get_db),
):
    """Search Indian stocks listed on NSE and BSE."""
    service = StockService(db)
    return await service.search_stocks(q, exchange)


@router.get("/{instrument_id}/overview", response_model=StockOverview)
async def get_stock_overview(
    instrument_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get latest available quotes, 52-week metrics, and company overview."""
    service = StockService(db)
    return await service.get_stock_overview(instrument_id)


@router.get("/{instrument_id}/history", response_model=HistoricalBarsResponse)
async def get_historical_bars(
    instrument_id: str,
    interval: str = Query("1d", description="Bar interval: 1d, 1h, 15m"),
    days: int = Query(90, ge=5, le=365, description="Number of historical days"),
    db: AsyncSession = Depends(get_db),
):
    """Get historical OHLCV price bars for charting."""
    service = StockService(db)
    return await service.get_historical_bars(instrument_id, interval, days)


@router.get("/{instrument_id}/financials", response_model=CompanyFinancialsResponse)
async def get_stock_financials(
    instrument_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get quarterly, annual, and TTM financial metrics and calculated ratios."""
    service = FinancialService(db)
    return await service.get_company_financials(instrument_id)


@router.get("/{instrument_id}/news", response_model=StockNewsResponse)
async def get_stock_news(
    instrument_id: str,
    limit: int = Query(15, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get financial news, announcements, and disclosures for the stock."""
    service = ResearchService(db)
    return await service.get_company_news(instrument_id, limit)


@router.get("/{instrument_id}/report")
async def get_stock_research_report(
    instrument_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Generate a comprehensive, objective equity research report."""
    generator = ResearchReportGenerator(db)
    return await generator.generate_report(instrument_id)

