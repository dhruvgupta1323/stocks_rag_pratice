from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import ProviderException
from backend.app.providers.base import BaseMarketDataProvider
from backend.app.schemas.instrument import StockSearchResult
from backend.app.schemas.market_data import QuoteRead, PriceBarRead


class TwelveDataProvider(BaseMarketDataProvider):
    """Twelve Data API Market Data Provider Adapter for Indian Equities (NSE/BSE)."""

    BASE_URL = "https://api.twelvedata.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TWELVE_DATA_API_KEY
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    @property
    def provider_name(self) -> str:
        return "twelvedata"

    def _require_api_key(self):
        if not self.api_key:
            raise ProviderException(
                "Twelve Data API key is not configured. Please set TWELVE_DATA_API_KEY in your .env file.",
                provider="twelvedata",
                status_code=401,
            )

    async def search_instruments(
        self, query: str, exchange: Optional[str] = None
    ) -> List[StockSearchResult]:
        self._require_api_key()
        ex = exchange.upper() if exchange else "NSE"
        params = {
            "symbol": query.strip(),
            "exchange": ex,
            "apikey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.BASE_URL}/symbol_search", params=params)
                res.raise_for_status()
                data = res.json()

                if data.get("status") == "error":
                    raise ProviderException(data.get("message", "Symbol search failed"), provider="twelvedata", status_code=data.get("code"))

                results: List[StockSearchResult] = []
                for item in data.get("data", []):
                    results.append(
                        StockSearchResult(
                            instrument_id=f"{item.get('exchange', 'NSE')}_EQ|{item.get('symbol')}",
                            company_id="",
                            name=item.get("instrument_name", item.get("symbol")),
                            symbol=item.get("symbol"),
                            exchange=item.get("exchange", "NSE"),
                            sector=item.get("instrument_type", "Equity"),
                            industry="Equities",
                            currency=item.get("currency", "INR"),
                        )
                    )
                return results
        except httpx.HTTPError as e:
            logger.error(f"Twelve Data symbol search failed: {e}")
            raise ProviderException(f"Twelve Data search error: {str(e)}", provider="twelvedata")

    async def get_quote(
        self, symbol: str, exchange: str, provider_instrument_id: str
    ) -> QuoteRead:
        self._require_api_key()
        sym = symbol.upper()
        ex = exchange.upper() if exchange else "NSE"
        params = {
            "symbol": sym,
            "exchange": ex,
            "apikey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.BASE_URL}/quote", params=params)
                res.raise_for_status()
                data = res.json()

                if data.get("status") == "error":
                    code = data.get("code", 400)
                    msg = data.get("message", "Failed to retrieve quote")
                    raise ProviderException(msg, provider="twelvedata", status_code=code)

                last_price = float(data.get("close", data.get("open", 0.0)))
                prev_close = float(data.get("previous_close", last_price))
                change = round(float(data.get("change", last_price - prev_close)), 2)
                change_pct = round(float(data.get("percent_change", (change / prev_close) * 100 if prev_close else 0.0)), 2)

                now = datetime.now(timezone.utc)
                return QuoteRead(
                    instrument_id=provider_instrument_id or f"{ex}_EQ|{sym}",
                    symbol=sym,
                    exchange=ex,
                    last_price=last_price,
                    open=float(data.get("open", last_price)),
                    high=float(data.get("high", last_price)),
                    low=float(data.get("low", last_price)),
                    previous_close=prev_close,
                    change=change,
                    change_percent=change_pct,
                    volume=int(data.get("volume", 0)),
                    provider="twelvedata",
                    market_timestamp=now,
                    fetched_at=now,
                    data_status="realtime",
                    currency=data.get("currency", "INR"),
                )
        except httpx.HTTPError as e:
            logger.error(f"Twelve Data quote error for {symbol}: {e}")
            raise ProviderException(f"Twelve Data quote error: {str(e)}", provider="twelvedata")

    async def get_historical_bars(
        self,
        symbol: str,
        exchange: str,
        provider_instrument_id: str,
        interval: str = "1d",
        days: int = 90,
    ) -> List[PriceBarRead]:
        self._require_api_key()
        sym = symbol.upper()
        ex = exchange.upper() if exchange else "NSE"
        # Twelve data intervals: 1day, 1h, 15min
        td_interval = "1day" if interval in ("1d", "day") else "1h"

        params = {
            "symbol": sym,
            "exchange": ex,
            "interval": td_interval,
            "outputsize": min(days, 365),
            "apikey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.BASE_URL}/time_series", params=params)
                res.raise_for_status()
                data = res.json()

                if data.get("status") == "error":
                    code = data.get("code", 400)
                    msg = data.get("message", "Failed to retrieve historical bars")
                    raise ProviderException(msg, provider="twelvedata", status_code=code)

                values = data.get("values", [])
                bars: List[PriceBarRead] = []
                for v in values:
                    dt_str = v.get("datetime")
                    try:
                        ts = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
                    except Exception:
                        ts = datetime.now(timezone.utc)

                    bars.append(
                        PriceBarRead(
                            timestamp=ts,
                            open=float(v.get("open", 0.0)),
                            high=float(v.get("high", 0.0)),
                            low=float(v.get("low", 0.0)),
                            close=float(v.get("close", 0.0)),
                            volume=int(v.get("volume", 0)),
                        )
                    )
                # Sort ascending by timestamp
                bars.sort(key=lambda b: b.timestamp)
                return bars
        except httpx.HTTPError as e:
            logger.error(f"Twelve Data time_series error for {symbol}: {e}")
            raise ProviderException(f"Twelve Data historical bars error: {str(e)}", provider="twelvedata")

    async def get_available_fundamentals(
        self, symbol: str, exchange: str
    ) -> Dict[str, Any]:
        return {
            "provider": "twelvedata",
            "symbol": symbol,
            "note": "Twelve Data provides fundamental data through company profile endpoints.",
        }

    async def get_market_status(self, exchange: str = "NSE") -> Dict[str, Any]:
        self._require_api_key()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(
                    f"{self.BASE_URL}/market_state",
                    params={"exchange": exchange, "apikey": self.api_key},
                )
                res.raise_for_status()
                return res.json()
        except Exception:
            return {
                "exchange": exchange,
                "status": "OPEN",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
