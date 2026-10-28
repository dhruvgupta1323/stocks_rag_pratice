from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import ProviderException
from backend.app.providers.base import BaseMarketDataProvider
from backend.app.schemas.instrument import StockSearchResult
from backend.app.schemas.market_data import QuoteRead, PriceBarRead


class UpstoxProvider(BaseMarketDataProvider):
    """Upstox API v2 Market Data Provider Adapter for Indian Equities."""

    BASE_URL = "https://api.upstox.com/v2"

    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None):
        self.api_key = api_key or settings.UPSTOX_API_KEY
        self.access_token = access_token or settings.UPSTOX_ACCESS_TOKEN
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    @property
    def provider_name(self) -> str:
        return "upstox"

    def _get_headers(self) -> Dict[str, str]:
        if not self.access_token:
            raise ProviderException(
                "Upstox access token is not configured. Please provide UPSTOX_ACCESS_TOKEN in backend environment.",
                provider="upstox",
                status_code=401,
            )
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": settings.USER_AGENT,
        }

    async def search_instruments(
        self, query: str, exchange: Optional[str] = None
    ) -> List[StockSearchResult]:
        # Upstox provides an instrument master dump file or search endpoint
        # In live mode with token, we query the search endpoint
        headers = self._get_headers()
        params = {"query": query}
        if exchange:
            params["exchange"] = exchange.upper()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.BASE_URL}/market/instruments", headers=headers, params=params)
                if res.status_code == 429:
                    raise ProviderException("Upstox rate limit exceeded.", provider="upstox", status_code=429)
                res.raise_for_status()
                data = res.json()
                results = []
                for item in data.get("data", []):
                    results.append(
                        StockSearchResult(
                            instrument_id=item.get("instrument_key", ""),
                            company_id="",
                            name=item.get("name", item.get("trading_symbol", "")),
                            symbol=item.get("trading_symbol", ""),
                            exchange=item.get("exchange", "NSE"),
                            isin=item.get("isin"),
                            sector="Equities",
                            industry="Equities",
                            last_price=item.get("last_price"),
                            currency="INR",
                        )
                    )
                return results
        except httpx.HTTPError as e:
            logger.error(f"Upstox instrument search failed: {e}")
            raise ProviderException(f"Upstox search error: {str(e)}", provider="upstox")

    async def get_quote(
        self, symbol: str, exchange: str, provider_instrument_id: str
    ) -> QuoteRead:
        headers = self._get_headers()
        key = provider_instrument_id or f"{exchange}_EQ|{symbol}"
        params = {"instrument_key": key}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.BASE_URL}/market-quote/quotes", headers=headers, params=params)
                if res.status_code == 429:
                    raise ProviderException("Upstox rate limit exceeded.", provider="upstox", status_code=429)
                res.raise_for_status()
                data = res.json()
                quote_data = data.get("data", {}).get(key)
                if not quote_data:
                    raise ProviderException(f"Instrument quote not found for key: {key}", provider="upstox", status_code=404)

                ohlc = quote_data.get("ohlc", {})
                last_price = float(quote_data.get("last_price", 0.0))
                prev_close = float(ohlc.get("close", last_price))
                change = round(last_price - prev_close, 2)
                change_percent = round((change / prev_close) * 100, 2) if prev_close != 0 else 0.0

                market_ts = datetime.fromtimestamp(quote_data.get("timestamp", 0) / 1000, tz=timezone.utc) if quote_data.get("timestamp") else datetime.now(timezone.utc)

                return QuoteRead(
                    instrument_id=provider_instrument_id,
                    symbol=symbol,
                    exchange=exchange,
                    last_price=last_price,
                    open=float(ohlc.get("open", last_price)),
                    high=float(ohlc.get("high", last_price)),
                    low=float(ohlc.get("low", last_price)),
                    previous_close=prev_close,
                    change=change,
                    change_percent=change_percent,
                    volume=int(quote_data.get("volume", 0)),
                    provider="upstox",
                    market_timestamp=market_ts,
                    fetched_at=datetime.now(timezone.utc),
                    data_status="realtime",
                    currency="INR",
                )
        except httpx.HTTPError as e:
            logger.error(f"Upstox get_quote failed for {symbol}: {e}")
            raise ProviderException(f"Upstox quote error: {str(e)}", provider="upstox")

    async def get_historical_bars(
        self,
        symbol: str,
        exchange: str,
        provider_instrument_id: str,
        interval: str = "1d",
        days: int = 90,
    ) -> List[PriceBarRead]:
        headers = self._get_headers()
        key = provider_instrument_id or f"{exchange}_EQ|{symbol}"
        to_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

        unit = "day" if interval in ("1d", "day") else "30minute"
        url = f"{self.BASE_URL}/historical-candle/{key}/{unit}/{to_date}/{from_date}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 429:
                    raise ProviderException("Upstox rate limit exceeded.", provider="upstox", status_code=429)
                res.raise_for_status()
                data = res.json()
                candles = data.get("data", {}).get("candles", [])

                bars = []
                for c in candles:
                    # [timestamp, open, high, low, close, volume, open_interest]
                    ts = datetime.fromisoformat(c[0])
                    bars.append(
                        PriceBarRead(
                            timestamp=ts,
                            open=float(c[1]),
                            high=float(c[2]),
                            low=float(c[3]),
                            close=float(c[4]),
                            volume=int(c[5]),
                        )
                    )
                # Sort ascending by timestamp
                bars.sort(key=lambda b: b.timestamp)
                return bars
        except httpx.HTTPError as e:
            logger.error(f"Upstox historical bars failed for {symbol}: {e}")
            raise ProviderException(f"Upstox historical data error: {str(e)}", provider="upstox")

    async def get_available_fundamentals(
        self, symbol: str, exchange: str
    ) -> Dict[str, Any]:
        return {"note": "Fundamentals from Upstox require premium add-on feed."}

    async def get_market_status(self, exchange: str = "NSE") -> Dict[str, Any]:
        headers = self._get_headers()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.BASE_URL}/market/status/{exchange.lower()}", headers=headers)
                res.raise_for_status()
                return res.json()
        except Exception as e:
            return {
                "exchange": exchange,
                "status": "UNKNOWN",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            }

