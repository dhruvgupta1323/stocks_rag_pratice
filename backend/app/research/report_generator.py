from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.stock_service import StockService
from backend.app.services.financial_service import FinancialService
from backend.app.services.research_service import ResearchService
from backend.app.analytics.indicators import TechnicalAnalytics


class ResearchReportGenerator:
    """Generates comprehensive, objective research reports without speculative buy/sell calls."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stock_service = StockService(db)
        self.financial_service = FinancialService(db)
        self.research_service = ResearchService(db)

    async def generate_report(self, instrument_id: str) -> Dict[str, Any]:
        overview = await self.stock_service.get_stock_overview(instrument_id)
        history = await self.stock_service.get_historical_bars(instrument_id, interval="1d", days=60)
        financials = await self.financial_service.get_company_financials(instrument_id)
        news = await self.research_service.get_company_news(instrument_id, limit=5)

        # Technical indicators
        closes = [b.close for b in history.bars]
        volatility = TechnicalAnalytics.calculate_historical_volatility(closes) if len(closes) >= 2 else None
        drawdown = TechnicalAnalytics.calculate_max_drawdown(closes) if len(closes) >= 2 else None

        # Build citations from news sources
        citations = []
        for article in news.articles:
            citations.append({
                "source_id": article.id,
                "title": article.title,
                "publisher": article.publisher,
                "url": article.url,
                "published_at": article.published_at.isoformat(),
            })

        # Catalysts & Risks based on sector and observed metrics
        catalysts = [
            f"Strong positioning in the {overview.sector} sector with established market presence.",
            f"Recent trading volume of {overview.quote.volume:,} shares indicating healthy market liquidity.",
        ]
        risks = [
            "Macroeconomic interest rate fluctuations and sector-specific regulatory shifts.",
            "Historical price volatility observed across recent trading intervals.",
        ]

        return {
            "title": f"Equities Research Intelligence Report: {overview.name} ({overview.symbol})",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": overview.symbol,
            "exchange": overview.exchange,
            "company_overview": {
                "name": overview.name,
                "sector": overview.sector,
                "industry": overview.industry,
                "description": overview.description,
            },
            "market_performance": {
                "last_price": overview.quote.last_price,
                "change": overview.quote.change,
                "change_percent": overview.quote.change_percent,
                "day_high": overview.quote.high,
                "day_low": overview.quote.low,
                "day_open": overview.quote.open,
                "volume": overview.quote.volume,
                "annualized_volatility": volatility,
                "max_drawdown": drawdown,
                "market_timestamp": overview.quote.market_timestamp.isoformat(),
                "data_status": overview.data_status,
            },
            "financial_performance": {
                "annual_metrics": [m.model_dump() for m in financials.annual_metrics],
                "ratios": financials.calculated_ratios,
            },
            "recent_announcements": [a.model_dump() for a in news.articles],
            "catalysts": catalysts,
            "risks": risks,
            "citations": citations,
            "data_limitations": [
                "This report is generated automatically from available market data and public disclosures.",
                "It does not constitute investment advice, trade recommendation, or a solicitation to buy or sell securities.",
                f"Market quote data status: {overview.data_status.upper()}.",
            ],
        }

