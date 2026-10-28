import asyncio
import sys
import os
from datetime import datetime, timezone

# Add workspace to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.db.session import AsyncSessionLocal, init_db, close_db
from backend.app.models.instrument import Instrument
from backend.app.crawler.feed_crawler import ResearchFeedCrawler


async def run_ingestion_cycle():
    """Executes a single cycle of financial research ingestion for all active equities."""
    setup_logging()
    logger.info("Starting background research ingestion cycle...")

    async with AsyncSessionLocal() as db:
        stmt = select(Instrument).where(Instrument.active == True)
        res = await db.execute(stmt)
        instruments = res.scalars().all()

        crawler = ResearchFeedCrawler(db)
        total_ingested = 0

        for inst in instruments:
            try:
                count = await crawler.ingest_news_for_company(
                    company_id=inst.company_id,
                    company_name=inst.company.name if inst.company else inst.symbol,
                    symbol=inst.symbol,
                )
                total_ingested += count
            except Exception as e:
                logger.error(f"Ingestion error for {inst.symbol}: {e}")

        logger.info(f"Ingestion cycle completed. Ingested {total_ingested} new articles across {len(instruments)} instruments.")


async def start_worker_loop():
    """Runs periodic ingestion loop based on NEWS_INGESTION_INTERVAL_MINUTES."""
    await init_db()
    interval_sec = settings.NEWS_INGESTION_INTERVAL_MINUTES * 60

    try:
        while True:
            await run_ingestion_cycle()
            logger.info(f"Sleeping for {settings.NEWS_INGESTION_INTERVAL_MINUTES} minutes until next cycle...")
            await asyncio.sleep(interval_sec)
    except asyncio.CancelledError:
        logger.info("Worker loop cancelled.")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(start_worker_loop())

