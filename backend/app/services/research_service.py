from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.exceptions import StockIntelligenceException
from backend.app.models.instrument import Instrument
from backend.app.models.research import ResearchSource, ResearchRecord
from backend.app.schemas.research import ResearchSourceRead, StockNewsResponse, ResearchRecordRead
from backend.app.crawler.feed_crawler import ResearchFeedCrawler


class ResearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crawler = ResearchFeedCrawler(db)

    async def get_company_news(self, instrument_id: str, limit: int = 15) -> StockNewsResponse:
        # Resolve instrument
        stmt = (
            select(Instrument)
            .options(selectinload(Instrument.company))
            .where((Instrument.id == instrument_id) | (Instrument.symbol == instrument_id.upper()))
            .order_by(Instrument.exchange.desc())
        )
        res = await self.db.execute(stmt)
        inst = res.scalars().first()
        if not inst:
            raise StockIntelligenceException(f"Instrument '{instrument_id}' not found.")

        # Query existing research sources
        source_stmt = (
            select(ResearchSource)
            .where(ResearchSource.company_id == inst.company_id)
            .order_by(desc(ResearchSource.published_at))
            .limit(limit)
        )
        s_res = await self.db.execute(source_stmt)
        sources = s_res.scalars().all()

        # If zero articles exist, trigger ingestion automatically
        if not sources:
            await self.crawler.ingest_news_for_company(
                company_id=inst.company_id,
                company_name=inst.company.name,
                symbol=inst.symbol,
            )
            s_res = await self.db.execute(source_stmt)
            sources = s_res.scalars().all()

        articles = [ResearchSourceRead.model_validate(s) for s in sources]
        return StockNewsResponse(
            symbol=inst.symbol,
            company_name=inst.company.name,
            total_articles=len(articles),
            articles=articles,
        )

    async def get_source_by_id(self, source_id: str) -> ResearchSourceRead:
        stmt = select(ResearchSource).where(ResearchSource.id == source_id)
        res = await self.db.execute(stmt)
        source = res.scalar_one_or_none()
        if not source:
            raise StockIntelligenceException(f"Research source '{source_id}' not found.")
        return ResearchSourceRead.model_validate(source)

    async def search_records(self, company_id: str, query: str, limit: int = 5) -> List[ResearchRecord]:
        q = f"%{query}%"
        stmt = (
            select(ResearchRecord)
            .options(selectinload(ResearchRecord.source))
            .where(
                ResearchRecord.company_id == company_id,
                ResearchRecord.normalized_text.ilike(q),
            )
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
