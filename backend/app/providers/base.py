from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from backend.app.schemas.instrument import StockSearchResult
from backend.app.schemas.market_data import QuoteRead, PriceBarRead


class BaseMarketDataProvider(ABC):
    """Abstract interface for all market data provider adapters (Upstox, Mock, etc.)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'upstox', 'mock')."""
        pass

    @abstractmethod
    async def search_instruments(
        self, query: str, exchange: Optional[str] = None
    ) -> List[StockSearchResult]:
        """Search instruments on NSE / BSE by name or ticker symbol."""
        pass

    @abstractmethod
    async def get_quote(
        self, symbol: str, exchange: str, provider_instrument_id: str
    ) -> QuoteRead:
        """Retrieve latest market quote for an equity instrument."""
        pass

    @abstractmethod
    async def get_historical_bars(
        self,
        symbol: str,
        exchange: str,
        provider_instrument_id: str,
        interval: str = "1d",
        days: int = 90,
    ) -> List[PriceBarRead]:
        """Retrieve historical OHLCV price bars."""
        pass

    @abstractmethod
    async def get_available_fundamentals(
        self, symbol: str, exchange: str
    ) -> Dict[str, Any]:
        """Retrieve key financial fundamental metrics available from the provider."""
        pass

    @abstractmethod
    async def get_market_status(self, exchange: str = "NSE") -> Dict[str, Any]:
        """Check market status (OPEN, CLOSED, PRE_OPEN) with timestamp."""
        pass

