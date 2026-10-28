from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import ProviderException
from backend.app.providers.base import BaseMarketDataProvider
from backend.app.schemas.instrument import StockSearchResult
from backend.app.schemas.market_data import QuoteRead, PriceBarRead


class YahooFinanceProvider(BaseMarketDataProvider):
    """Free real-time & historical market data provider for Indian Equities (NSE/BSE).
    Requires zero API keys. Uses Yahoo Finance's public chart and quote endpoints.
    """

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance"

    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "yfinance"

    def _format_ticker(self, symbol: str, exchange: str) -> str:
        sym = symbol.upper().strip()
        ex = exchange.upper().strip() if exchange else "NSE"
        suffix = ".NS" if ex == "NSE" else ".BO"
        return f"{sym}{suffix}"

    async def search_instruments(
        self, query: str, exchange: Optional[str] = None
    ) -> List[StockSearchResult]:
        q = query.strip()
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                res = await client.get(f"https://query2.finance.yahoo.com/v1/finance/search?q={q}&quotesCount=10&newsCount=0")
                res.raise_for_status()
                data = res.json()

                results: List[StockSearchResult] = []
                for item in data.get("quotes", []):
                    ticker = item.get("symbol", "")
                    ex = "NSE" if ticker.endswith(".NS") else "BSE" if ticker.endswith(".BO") else item.get("exchange", "")
                    if exchange and ex != exchange.upper():
                        continue

                    raw_sym = ticker.replace(".NS", "").replace(".BO", "")
                    results.append(
                        StockSearchResult(
                            instrument_id=f"{ex}_EQ|{raw_sym}",
                            company_id="",
                            name=item.get("shortname", item.get("longname", raw_sym)),
                            symbol=raw_sym,
                            exchange=ex,
                            sector=item.get("sector", "Equities"),
                            industry=item.get("industry", "Equities"),
                            currency="INR",
                        )
                    )
                return results
        except Exception as e:
            logger.warning(f"Yahoo Finance search error: {e}")
            return []

    async def get_quote(
        self, symbol: str, exchange: str, provider_instrument_id: str
    ) -> QuoteRead:
        ticker = self._format_ticker(symbol, exchange)
        url = f"{self.BASE_URL}/chart/{ticker}?range=1d&interval=1m"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                res = await client.get(url)
                res.raise_for_status()
                data = res.json()
                result = data.get("chart", {}).get("result", [])
                if not result:
                    raise ProviderException(f"No chart data found for {ticker}", provider="yfinance", status_code=404)

                meta = result[0].get("meta", {})
                last_price = float(meta.get("regularMarketPrice", 0.0))
                prev_close = float(meta.get("chartPreviousClose", meta.get("previousClose", last_price)))
                change = round(last_price - prev_close, 2)
                change_pct = round((change / prev_close) * 100.0, 2) if prev_close else 0.0

                now = datetime.now(timezone.utc)
                market_ts = (
                    datetime.fromtimestamp(meta.get("regularMarketTime"), tz=timezone.utc)
                    if meta.get("regularMarketTime")
                    else now
                )

                return QuoteRead(
                    instrument_id=provider_instrument_id or f"{exchange}_EQ|{symbol}",
                    symbol=symbol.upper(),
                    exchange=exchange.upper(),
                    last_price=last_price,
                    open=float(meta.get("regularMarketDayOpen", last_price)),
                    high=float(meta.get("regularMarketDayHigh", last_price)),
                    low=float(meta.get("regularMarketDayLow", last_price)),
                    previous_close=prev_close,
                    change=change,
                    change_percent=change_pct,
                    volume=int(meta.get("regularMarketVolume", 0)),
                    provider="yfinance",
                    market_timestamp=market_ts,
                    fetched_at=now,
                    data_status="realtime",
                    currency=meta.get("currency", "INR"),
                )
        except Exception as e:
            logger.error(f"Yahoo Finance quote fetch error for {symbol}: {e}")
            raise ProviderException(f"Yahoo Finance quote error: {str(e)}", provider="yfinance")

    async def get_historical_bars(
        self,
        symbol: str,
        exchange: str,
        provider_instrument_id: str,
        interval: str = "1d",
        days: int = 90,
    ) -> List[PriceBarRead]:
        ticker = self._format_ticker(symbol, exchange)
        # Yahoo Finance ranges: 1mo, 3mo, 6mo, 1y
        range_str = "1y" if days > 180 else "6mo" if days > 90 else "3mo" if days > 30 else "1mo"
        url = f"{self.BASE_URL}/chart/{ticker}?range={range_str}&interval=1d"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                res = await client.get(url)
                res.raise_for_status()
                data = res.json()
                result = data.get("chart", {}).get("result", [])
                if not result:
                    raise ProviderException(f"No chart data found for {ticker}", provider="yfinance", status_code=404)

                timestamps = result[0].get("timestamp", [])
                indicators = result[0].get("indicators", {}).get("quote", [{}])[0]

                opens = indicators.get("open", [])
                highs = indicators.get("high", [])
                lows = indicators.get("low", [])
                closes = indicators.get("close", [])
                volumes = indicators.get("volume", [])

                bars: List[PriceBarRead] = []
                for i in range(len(timestamps)):
                    c = closes[i] if i < len(closes) else None
                    if c is None or c <= 0:
                        continue  # Skip null holiday bars

                    ts = datetime.fromtimestamp(timestamps[i], tz=timezone.utc)
                    o = opens[i] if i < len(opens) and opens[i] is not None else c
                    h = highs[i] if i < len(highs) and highs[i] is not None else c
                    l = lows[i] if i < len(lows) and lows[i] is not None else c
                    v = int(volumes[i]) if i < len(volumes) and volumes[i] is not None else 0

                    bars.append(
                        PriceBarRead(
                            timestamp=ts,
                            open=round(float(o), 2),
                            high=round(float(h), 2),
                            low=round(float(l), 2),
                            close=round(float(c), 2),
                            volume=v,
                        )
                    )

                bars.sort(key=lambda b: b.timestamp)
                return bars
        except Exception as e:
            logger.error(f"Yahoo Finance historical bars error for {symbol}: {e}")
            raise ProviderException(f"Yahoo Finance historical data error: {str(e)}", provider="yfinance")

    async def get_available_fundamentals(
        self, symbol: str, exchange: str
    ) -> Dict[str, Any]:
        return {
            "provider": "yfinance",
            "symbol": symbol,
            "status": "realtime",
        }

    async def get_market_status(self, exchange: str = "NSE") -> Dict[str, Any]:
        return {
            "exchange": exchange,
            "status": "OPEN",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "yfinance",
        }

