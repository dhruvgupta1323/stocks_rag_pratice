from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.logging import logger
from backend.app.core.exceptions import InstrumentNotFoundException
from backend.app.models.company import Company
from backend.app.models.instrument import Instrument
from backend.app.models.market_data import MarketQuote, PriceBar
from backend.app.models.financials import FinancialMetric
from backend.app.providers.factory import get_market_data_provider
from backend.app.schemas.instrument import StockSearchResult
from backend.app.schemas.market_data import QuoteRead, StockOverview, HistoricalBarsResponse, PriceBarRead


class StockService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = get_market_data_provider()

    async def search_stocks(self, query: str, exchange: Optional[str] = None) -> List[StockSearchResult]:
        """Search instruments across database entities and data provider."""
        q = f"%{query.strip()}%"
        stmt = (
            select(Instrument)
            .join(Instrument.company)
            .options(selectinload(Instrument.company), selectinload(Instrument.quotes))
            .where(
                or_(
                    Instrument.symbol.ilike(q),
                    Company.name.ilike(q),
                    Company.sector.ilike(q),
                )
            )
        )
        if exchange:
            stmt = stmt.where(Instrument.exchange == exchange.upper())

        result = await self.db.execute(stmt)
        instruments = result.scalars().all()

        results: List[StockSearchResult] = []
        for inst in instruments:
            last_price = None
            if inst.quotes:
                # Most recent quote
                sorted_quotes = sorted(inst.quotes, key=lambda q: q.market_timestamp, reverse=True)
                last_price = sorted_quotes[0].last_price

            results.append(
                StockSearchResult(
                    instrument_id=inst.id,
                    company_id=inst.company_id,
                    name=inst.company.name,
                    symbol=inst.symbol,
                    exchange=inst.exchange,
                    isin=inst.isin,
                    sector=inst.company.sector,
                    industry=inst.company.industry,
                    last_price=last_price,
                    currency=inst.currency,
                )
            )

        # If database results are empty or query has no local match, search provider
        if not results:
            try:
                provider_results = await self.provider.search_instruments(query, exchange)
                results.extend(provider_results)
            except Exception as e:
                logger.warning(f"Active provider search failed for '{query}': {e}")

            if not results:
                try:
                    from backend.app.providers.yfinance import YahooFinanceProvider
                    yf = YahooFinanceProvider()
                    yf_results = await yf.search_instruments(query, exchange)
                    results.extend(yf_results)
                except Exception as yf_err:
                    logger.warning(f"Yahoo Finance search fallback failed for '{query}': {yf_err}")

        return results

    async def _onboard_instrument(self, instrument_id: str, exchange: Optional[str] = "NSE") -> Optional[Instrument]:
        """Dynamically onboard a searched instrument into local database."""
        import uuid
        from backend.app.providers.yfinance import YahooFinanceProvider

        # Extract symbol and exchange
        clean_id = instrument_id.strip()
        if "|" in clean_id:
            sym = clean_id.split("|")[-1].upper()
            ex = clean_id.split("_")[0].upper()
        else:
            sym = clean_id.upper()
            ex = exchange.upper() if exchange else "NSE"

        # Check if already present under (exchange, symbol)
        check_stmt = (
            select(Instrument)
            .options(selectinload(Instrument.company), selectinload(Instrument.quotes))
            .where(and_(Instrument.symbol == sym, Instrument.exchange == ex))
        )
        res = await self.db.execute(check_stmt)
        existing = res.scalars().first()
        if existing:
            return existing

        # Search provider for metadata
        company_name = f"{sym} Limited"
        sector = "Equities"
        industry = "Equities"
        provider_id = f"{ex}_EQ|{sym}"
        currency = "INR"

        results = []
        try:
            results = await self.provider.search_instruments(sym, ex)
        except Exception as e:
            logger.warning(f"Active provider search failed during onboarding for {sym}: {e}")

        if not results:
            try:
                yf = YahooFinanceProvider()
                results = await yf.search_instruments(sym, ex)
            except Exception as e:
                logger.warning(f"Yahoo Finance search failed during onboarding for {sym}: {e}")

        matched = next((r for r in results if r.symbol.upper() == sym), None)
        if not matched and results:
            matched = results[0]

        if matched:
            company_name = matched.name or company_name
            sector = matched.sector or sector
            industry = matched.industry or industry
            provider_id = matched.instrument_id or provider_id
            currency = matched.currency or currency
        else:
            # Verify valid symbol with Yahoo Finance before onboarding
            try:
                yf = YahooFinanceProvider()
                quote = await yf.get_quote(sym, ex, provider_id)
                if not quote or not quote.last_price:
                    return None
                company_name = f"{sym} Limited"
            except Exception:
                return None

        # Check or create Company
        c_stmt = select(Company).where(Company.name.ilike(company_name))
        c_res = await self.db.execute(c_stmt)
        company = c_res.scalars().first()
        if not company:
            company = Company(
                id=str(uuid.uuid4()),
                name=company_name,
                sector=sector,
                industry=industry,
                description=f"{company_name} ({sym}) listed on {ex}.",
            )
            self.db.add(company)
            await self.db.flush()

        inst = Instrument(
            id=str(uuid.uuid4()),
            company_id=company.id,
            exchange=ex,
            symbol=sym,
            provider_instrument_id=provider_id,
            currency=currency,
            active=True,
        )
        self.db.add(inst)
        await self.db.commit()

        # Eager reload
        re_stmt = (
            select(Instrument)
            .options(selectinload(Instrument.company), selectinload(Instrument.quotes))
            .where(Instrument.id == inst.id)
        )
        final_res = await self.db.execute(re_stmt)
        return final_res.scalar_one_or_none()

    async def get_instrument_by_id(self, instrument_id: str, exchange: Optional[str] = "NSE") -> Instrument:
        stmt = (
            select(Instrument)
            .options(selectinload(Instrument.company), selectinload(Instrument.quotes))
            .where(
                or_(
                    Instrument.id == instrument_id,
                    Instrument.symbol == instrument_id.upper(),
                    Instrument.provider_instrument_id == instrument_id,
                )
            )
        )
        if exchange:
            stmt = stmt.order_by(Instrument.exchange.desc())

        result = await self.db.execute(stmt)
        instruments = result.scalars().all()
        if not instruments:
            new_inst = await self._onboard_instrument(instrument_id, exchange)
            if new_inst:
                return new_inst
            raise InstrumentNotFoundException(f"Instrument '{instrument_id}' not found in registry.")

        # If multiple instruments exist (e.g. NSE and BSE for same symbol), prefer the requested exchange (NSE by default)
        if exchange:
            preferred = next((i for i in instruments if i.exchange == exchange.upper()), None)
            if preferred:
                return preferred

        return instruments[0]

    async def get_stock_overview(self, instrument_id: str) -> StockOverview:
        instrument = await self.get_instrument_by_id(instrument_id)
        company = instrument.company

        # Retrieve quote from provider
        quote = None
        try:
            quote = await self.provider.get_quote(
                symbol=instrument.symbol,
                exchange=instrument.exchange,
                provider_instrument_id=instrument.provider_instrument_id,
            )
        except Exception as e:
            logger.warning(f"Live quote fetch failed for {instrument.symbol} using {self.provider.provider_name}: {e}.")
            if self.provider.provider_name != "yfinance":
                try:
                    from backend.app.providers.yfinance import YahooFinanceProvider
                    yf = YahooFinanceProvider()
                    quote = await yf.get_quote(instrument.symbol, instrument.exchange, instrument.provider_instrument_id)
                except Exception as yf_err:
                    logger.warning(f"Yahoo Finance fallback quote failed: {yf_err}")

        if quote:
            # Persist quote to DB
            db_quote = MarketQuote(
                instrument_id=instrument.id,
                last_price=quote.last_price,
                open=quote.open,
                high=quote.high,
                low=quote.low,
                previous_close=quote.previous_close,
                volume=quote.volume,
                provider=quote.provider,
                market_timestamp=quote.market_timestamp,
                fetched_at=quote.fetched_at,
                data_status=quote.data_status,
            )
            self.db.add(db_quote)
            await self.db.commit()
        else:
            # Use cached quote if exists
            stmt = select(MarketQuote).where(MarketQuote.instrument_id == instrument.id).order_by(desc(MarketQuote.market_timestamp))
            res = await self.db.execute(stmt)
            cached_quote = res.scalars().first()
            if cached_quote:
                change = round(cached_quote.last_price - cached_quote.previous_close, 2)
                change_pct = round((change / cached_quote.previous_close) * 100, 2) if cached_quote.previous_close else 0.0
                quote = QuoteRead(
                    id=cached_quote.id,
                    instrument_id=instrument.id,
                    symbol=instrument.symbol,
                    exchange=instrument.exchange,
                    last_price=cached_quote.last_price,
                    open=cached_quote.open,
                    high=cached_quote.high,
                    low=cached_quote.low,
                    previous_close=cached_quote.previous_close,
                    change=change,
                    change_percent=change_pct,
                    volume=cached_quote.volume,
                    provider=cached_quote.provider,
                    market_timestamp=cached_quote.market_timestamp,
                    fetched_at=cached_quote.fetched_at,
                    data_status="cached",
                )
            else:
                # If no quote exists at all, fetch from mock provider
                from backend.app.providers.mock import MockMarketDataProvider
                mock_prov = MockMarketDataProvider()
                quote = await mock_prov.get_quote(instrument.symbol, instrument.exchange, instrument.provider_instrument_id)

        # Retrieve valuation metrics from database
        fin_stmt = select(FinancialMetric).where(FinancialMetric.company_id == company.id)
        fin_res = await self.db.execute(fin_stmt)
        metrics = fin_res.scalars().all()
        pe = next((m.value for m in metrics if "PE" in m.metric_name), None)
        pb = next((m.value for m in metrics if "PB" in m.metric_name), None)

        return StockOverview(
            instrument_id=instrument.id,
            company_id=company.id,
            name=company.name,
            symbol=instrument.symbol,
            exchange=instrument.exchange,
            sector=company.sector,
            industry=company.industry,
            description=company.description,
            quote=quote,
            high_52w=round(quote.last_price * 1.15, 2),
            low_52w=round(quote.last_price * 0.78, 2),
            market_cap_crores=round(quote.last_price * (quote.volume / 100000), 2),
            pe_ratio=pe,
            pb_ratio=pb,
            data_status=quote.data_status,
            last_updated=quote.fetched_at,
        )

    async def get_historical_bars(
        self, instrument_id: str, interval: str = "1d", days: int = 90
    ) -> HistoricalBarsResponse:
        instrument = await self.get_instrument_by_id(instrument_id)
        bars = None
        data_status = "mock"
        provider_name = self.provider.provider_name

        try:
            bars = await self.provider.get_historical_bars(
                symbol=instrument.symbol,
                exchange=instrument.exchange,
                provider_instrument_id=instrument.provider_instrument_id,
                interval=interval,
                days=days,
            )
            data_status = "mock" if self.provider.provider_name == "mock" else "realtime"
        except Exception as e:
            logger.warning(
                f"Historical bars fetch failed for {instrument.symbol} using {self.provider.provider_name}: {e}. "
                "Trying Yahoo Finance fallback."
            )
            if self.provider.provider_name != "yfinance":
                try:
                    from backend.app.providers.yfinance import YahooFinanceProvider
                    yf = YahooFinanceProvider()
                    bars = await yf.get_historical_bars(
                        symbol=instrument.symbol,
                        exchange=instrument.exchange,
                        provider_instrument_id=instrument.provider_instrument_id,
                        interval=interval,
                        days=days,
                    )
                    data_status = "realtime"
                    provider_name = "yfinance"
                except Exception as yf_err:
                    logger.warning(f"Yahoo Finance fallback bars failed: {yf_err}")

        if not bars:
            from backend.app.providers.mock import MockMarketDataProvider
            mock_prov = MockMarketDataProvider()
            bars = await mock_prov.get_historical_bars(
                instrument.symbol, instrument.exchange, instrument.provider_instrument_id, interval, days
            )
            data_status = "mock"
            provider_name = "mock_fallback"

        return HistoricalBarsResponse(
            instrument_id=instrument.id,
            symbol=instrument.symbol,
            exchange=instrument.exchange,
            interval=interval,
            bars=bars,
            provider=provider_name,
            data_status=data_status,
        )
