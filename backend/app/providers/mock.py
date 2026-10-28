from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
import math
from backend.app.providers.base import BaseMarketDataProvider
from backend.app.schemas.instrument import StockSearchResult
from backend.app.schemas.market_data import QuoteRead, PriceBarRead

# Baseline mock prices for major Indian equities
BASELINE_PRICES: Dict[str, Dict[str, Any]] = {
    "RELIANCE": {"name": "Reliance Industries Limited", "price": 2980.50, "isin": "INE002A01018", "sector": "Energy", "industry": "Oil & Gas"},
    "TCS": {"name": "Tata Consultancy Services Limited", "price": 4125.75, "isin": "INE467B01029", "sector": "Information Technology", "industry": "IT Services"},
    "HDFCBANK": {"name": "HDFC Bank Limited", "price": 1675.20, "isin": "INE040A01034", "sector": "Financial Services", "industry": "Private Bank"},
    "INFY": {"name": "Infosys Limited", "price": 1845.60, "isin": "INE009A01021", "sector": "Information Technology", "industry": "IT Services"},
    "TATAMOTORS": {"name": "Tata Motors Limited", "price": 965.40, "isin": "INE155A01022", "sector": "Automobile", "industry": "Automotive"},
    "SBIN": {"name": "State Bank of India", "price": 820.15, "isin": "INE062A01020", "sector": "Financial Services", "industry": "Public Bank"},
    "ITC": {"name": "ITC Limited", "price": 482.35, "isin": "INE154A01025", "sector": "Consumer Goods", "industry": "FMCG"},
    "BHARTIARTL": {"name": "Bharti Airtel Limited", "price": 1690.45, "isin": "INE397D01024", "sector": "Telecommunication", "industry": "Telecom Services"},
}


class MockMarketDataProvider(BaseMarketDataProvider):
    """Documented mock adapter providing deterministic market data labeled clearly with data_status='mock'."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def search_instruments(
        self, query: str, exchange: Optional[str] = None
    ) -> List[StockSearchResult]:
        q = query.strip().upper()
        results: List[StockSearchResult] = []

        for symbol, info in BASELINE_PRICES.items():
            if q in symbol or q in info["name"].upper():
                for ex in (["NSE", "BSE"] if not exchange else [exchange.upper()]):
                    results.append(
                        StockSearchResult(
                            instrument_id=f"{ex}_EQ|{symbol}",
                            company_id="",
                            name=info["name"],
                            symbol=symbol,
                            exchange=ex,
                            isin=info["isin"],
                            sector=info["sector"],
                            industry=info["industry"],
                            last_price=info["price"],
                            currency="INR",
                        )
                    )
        return results

    async def get_quote(
        self, symbol: str, exchange: str, provider_instrument_id: str
    ) -> QuoteRead:
        sym = symbol.upper()
        base = BASELINE_PRICES.get(sym, {"price": 1000.0, "name": sym})
        base_price = base["price"]

        now = datetime.now(timezone.utc)
        # Deterministic micro-variation based on minute of day
        variation = math.sin(now.minute / 10.0) * (base_price * 0.008)
        last_price = round(base_price + variation, 2)
        prev_close = base_price
        change = round(last_price - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2) if prev_close != 0 else 0.0

        open_price = round(base_price * 0.998, 2)
        high_price = max(last_price, open_price, round(base_price * 1.012, 2))
        low_price = min(last_price, open_price, round(base_price * 0.988, 2))

        return QuoteRead(
            instrument_id=provider_instrument_id or f"{exchange}_EQ|{sym}",
            symbol=sym,
            exchange=exchange.upper(),
            last_price=last_price,
            open=open_price,
            high=high_price,
            low=low_price,
            previous_close=prev_close,
            change=change,
            change_percent=change_pct,
            volume=5240000,
            provider="mock",
            market_timestamp=now,
            fetched_at=now,
            data_status="mock",
            currency="INR",
        )

    async def get_historical_bars(
        self,
        symbol: str,
        exchange: str,
        provider_instrument_id: str,
        interval: str = "1d",
        days: int = 90,
    ) -> List[PriceBarRead]:
        sym = symbol.upper()
        base = BASELINE_PRICES.get(sym, {"price": 1000.0})
        base_price = base["price"]

        bars: List[PriceBarRead] = []
        now = datetime.now(timezone.utc)

        # Generate realistic historical trajectory backwards
        current_price = base_price
        for i in range(days, 0, -1):
            ts = now - timedelta(days=i)
            # Skip weekend trading days
            if ts.weekday() >= 5:
                continue

            # Deterministic pseudo-random walk using sine waves
            wave1 = math.sin(i * 0.15) * 0.015
            wave2 = math.cos(i * 0.07) * 0.02
            daily_drift = wave1 + wave2

            open_p = round(current_price * (1.0 + wave1 * 0.5), 2)
            close_p = round(current_price * (1.0 + daily_drift), 2)
            high_p = round(max(open_p, close_p) * (1.0 + abs(wave2) * 0.6), 2)
            low_p = round(min(open_p, close_p) * (1.0 - abs(wave1) * 0.6), 2)
            vol = int(3000000 + abs(wave1 * 10000000))

            bars.append(
                PriceBarRead(
                    timestamp=ts,
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=vol,
                )
            )
            current_price = close_p

        # Append today's bar
        bars.append(
            PriceBarRead(
                timestamp=now,
                open=round(base_price * 0.998, 2),
                high=round(base_price * 1.012, 2),
                low=round(base_price * 0.988, 2),
                close=base_price,
                volume=4500000,
            )
        )
        return bars

    async def get_available_fundamentals(
        self, symbol: str, exchange: str
    ) -> Dict[str, Any]:
        return {
            "source": "Mock Fundamentals Registry",
            "status": "mock",
            "symbol": symbol,
            "currency": "INR",
        }

    async def get_market_status(self, exchange: str = "NSE") -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "exchange": exchange.upper(),
            "status": "OPEN",
            "timestamp": now.isoformat(),
            "provider": "mock",
        }

