from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import time
import httpx
import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.base import utc_now
from backend.app.models.company import Company
from backend.app.models.instrument import Instrument
from backend.app.models.research import ResearchSource, ResearchRecord
from backend.app.crawler.normalizer import ContentNormalizer
from backend.app.crawler.registry import FEED_REGISTRY


class ResearchFeedCrawler:
    """Automated financial news and announcement crawler for Indian equities."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    async def fetch_rss_feed(self, url: str) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed with HTTP headers and timeout."""
        headers = {"User-Agent": settings.USER_AGENT}
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                res = await client.get(url, headers=headers)
                res.raise_for_status()
                parsed = feedparser.parse(res.text)
                return parsed.entries
        except Exception as e:
            logger.warning(f"Failed to fetch RSS from {url}: {e}")
            return []

    async def ingest_news_for_company(
        self, company_id: str, company_name: str, symbol: str
    ) -> int:
        """Fetch, sanitize, resolve, and persist latest news articles for a company."""
        # Use Google News RSS query for this specific stock
        query = f"{company_name} {symbol}"
        url = f"https://news.google.com/rss/search?q={query}+share+price+NSE&hl=en-IN&gl=IN&ceid=IN:en"

        entries = await self.fetch_rss_feed(url)
        inserted_count = 0

        for entry in entries[:settings.MAX_NEWS_PER_REFRESH]:
            raw_title = getattr(entry, "title", "")
            raw_summary = getattr(entry, "summary", "") or raw_title
            raw_link = getattr(entry, "link", "")
            publisher = getattr(entry, "source", {}).get("title", "Financial News Feed")

            if not raw_title or not raw_link:
                continue

            normalized = ContentNormalizer.normalize_article(raw_title, raw_summary, raw_link)

            # Check if source with this content_hash already exists
            stmt = select(ResearchSource).where(ResearchSource.content_hash == normalized["content_hash"])
            res = await self.db.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                continue

            # Parse publication timestamp
            pub_date = utc_now()
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)

            # Create ResearchSource
            source = ResearchSource(
                company_id=company_id,
                source_type="news",
                title=normalized["title"][:490],
                publisher=publisher[:190],
                url=normalized["url"][:990],
                published_at=pub_date,
                retrieved_at=utc_now(),
                content_hash=normalized["content_hash"],
                processing_status="processed",
                licensing_notes="Public RSS headline under fair-use research indexing.",
            )
            self.db.add(source)
            await self.db.flush()

            # Create ResearchRecord
            record = ResearchRecord(
                source_id=source.id,
                company_id=company_id,
                normalized_text=normalized["normalized_text"],
                extracted_entities={"symbol": symbol, "company_name": company_name},
                metadata_json={"publisher": publisher, "published_at": pub_date.isoformat()},
                created_at=utc_now(),
            )
            self.db.add(record)
            inserted_count += 1

        if inserted_count > 0:
            await self.db.commit()
            logger.info(f"Ingested {inserted_count} new research articles for {symbol} ({company_name})")

        return inserted_count

