import asyncio
import sys
import os

# Add root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.app.core.logging import setup_logging, logger
from backend.app.db.session import init_db, close_db, AsyncSessionLocal
from backend.app.models.company import Company
from backend.app.models.instrument import Instrument
from backend.app.models.market_data import MarketQuote, PriceBar
from backend.app.models.financials import FinancialMetric
from backend.app.db.base import utc_now
from sqlalchemy import select

# Seed data for prominent Indian equities across key sectors
SEED_COMPANIES = [
    {
        "name": "Reliance Industries Limited",
        "sector": "Energy",
        "industry": "Oil & Gas Refining & Marketing",
        "description": "Reliance Industries is India's largest private sector enterprise, with businesses in petrochemicals, refining, oil & gas, telecom (Jio), and retail.",
        "symbol": "RELIANCE",
        "isin": "INE002A01018",
        "provider_instrument_id": "NSE_EQ|INE002A01018",
        "quote": {
            "last_price": 2980.50,
            "open": 2965.00,
            "high": 2998.00,
            "low": 2952.10,
            "previous_close": 2960.20,
            "volume": 6842000,
        },
        "metrics": [
            {"metric_name": "Revenue", "value": 901064.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Net Profit", "value": 69621.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Operating Margin", "value": 18.2, "unit": "%", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "PE Ratio", "value": 28.4, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "PB Ratio", "value": 2.3, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "Debt to Equity", "value": 0.42, "unit": "ratio", "reporting_period": "FY24", "period_type": "annual"},
        ]
    },
    {
        "name": "Tata Consultancy Services Limited",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "description": "TCS is a global leader in IT services, digital and business solutions, partnering with many of the world's largest businesses.",
        "symbol": "TCS",
        "isin": "INE467B01029",
        "provider_instrument_id": "NSE_EQ|INE467B01029",
        "quote": {
            "last_price": 4125.75,
            "open": 4095.00,
            "high": 4148.00,
            "low": 4088.50,
            "previous_close": 4102.30,
            "volume": 2154000,
        },
        "metrics": [
            {"metric_name": "Revenue", "value": 240893.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Net Profit", "value": 46099.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Operating Margin", "value": 24.6, "unit": "%", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "PE Ratio", "value": 31.8, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "PB Ratio", "value": 14.1, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "Debt to Equity", "value": 0.0, "unit": "ratio", "reporting_period": "FY24", "period_type": "annual"},
        ]
    },
    {
        "name": "HDFC Bank Limited",
        "sector": "Financial Services",
        "industry": "Private Sector Bank",
        "description": "HDFC Bank is India's largest private sector bank by assets and market capitalization, providing retail, wholesale, and treasury banking.",
        "symbol": "HDFCBANK",
        "isin": "INE040A01034",
        "provider_instrument_id": "NSE_EQ|INE040A01034",
        "quote": {
            "last_price": 1675.20,
            "open": 1660.00,
            "high": 1682.40,
            "low": 1655.00,
            "previous_close": 1662.80,
            "volume": 12850000,
        },
        "metrics": [
            {"metric_name": "Revenue", "value": 285421.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Net Profit", "value": 64060.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Net Interest Margin", "value": 3.63, "unit": "%", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "PE Ratio", "value": 19.5, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "PB Ratio", "value": 2.8, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "Gross NPA", "value": 1.24, "unit": "%", "reporting_period": "FY24", "period_type": "annual"},
        ]
    },
    {
        "name": "Infosys Limited",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "description": "Infosys is a global leader in next-generation digital services and consulting, enabling clients across 56 countries to navigate digital transformation.",
        "symbol": "INFY",
        "isin": "INE009A01021",
        "provider_instrument_id": "NSE_EQ|INE009A01021",
        "quote": {
            "last_price": 1845.60,
            "open": 1830.00,
            "high": 1858.00,
            "low": 1822.40,
            "previous_close": 1832.10,
            "volume": 5420000,
        },
        "metrics": [
            {"metric_name": "Revenue", "value": 153670.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Net Profit", "value": 26233.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Operating Margin", "value": 20.7, "unit": "%", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "PE Ratio", "value": 27.2, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "PB Ratio", "value": 8.9, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "Debt to Equity", "value": 0.05, "unit": "ratio", "reporting_period": "FY24", "period_type": "annual"},
        ]
    },
    {
        "name": "Tata Motors Limited",
        "sector": "Automobile",
        "industry": "Passenger Cars & Commercial Vehicles",
        "description": "Tata Motors is a leading global automobile manufacturer with a portfolio that includes cars, utility vehicles, buses, trucks, and luxury cars under Jaguar Land Rover.",
        "symbol": "TATAMOTORS",
        "isin": "INE155A01022",
        "provider_instrument_id": "NSE_EQ|INE155A01022",
        "quote": {
            "last_price": 965.40,
            "open": 950.00,
            "high": 972.50,
            "low": 948.10,
            "previous_close": 953.20,
            "volume": 8412000,
        },
        "metrics": [
            {"metric_name": "Revenue", "value": 437928.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Net Profit", "value": 31807.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Operating Margin", "value": 14.3, "unit": "%", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "PE Ratio", "value": 11.2, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "PB Ratio", "value": 3.7, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "Debt to Equity", "value": 0.65, "unit": "ratio", "reporting_period": "FY24", "period_type": "annual"},
        ]
    },
    {
        "name": "State Bank of India",
        "sector": "Financial Services",
        "industry": "Public Sector Bank",
        "description": "State Bank of India is a Fortune 500 company and India's largest commercial bank with a 200+ year heritage and 22,000+ branches.",
        "symbol": "SBIN",
        "isin": "INE062A01020",
        "provider_instrument_id": "NSE_EQ|INE062A01020",
        "quote": {
            "last_price": 820.15,
            "open": 815.00,
            "high": 825.80,
            "low": 812.30,
            "previous_close": 814.90,
            "volume": 14210000,
        },
        "metrics": [
            {"metric_name": "Revenue", "value": 406440.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Net Profit", "value": 61077.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Net Interest Margin", "value": 3.28, "unit": "%", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "PE Ratio", "value": 11.5, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "PB Ratio", "value": 1.7, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "Gross NPA", "value": 2.24, "unit": "%", "reporting_period": "FY24", "period_type": "annual"},
        ]
    },
    {
        "name": "ITC Limited",
        "sector": "Consumer Goods",
        "industry": "Diversified FMCG",
        "description": "ITC is one of India's foremost private sector companies with presence in FMCG, Hotels, Packaging, Paperboards & Specialty Papers, and Agri-Business.",
        "symbol": "ITC",
        "isin": "INE154A01025",
        "provider_instrument_id": "NSE_EQ|INE154A01025",
        "quote": {
            "last_price": 482.35,
            "open": 479.00,
            "high": 485.50,
            "low": 477.80,
            "previous_close": 480.10,
            "volume": 7650000,
        },
        "metrics": [
            {"metric_name": "Revenue", "value": 70251.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Net Profit", "value": 20422.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Operating Margin", "value": 36.8, "unit": "%", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "PE Ratio", "value": 27.6, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "PB Ratio", "value": 7.4, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "Debt to Equity", "value": 0.0, "unit": "ratio", "reporting_period": "FY24", "period_type": "annual"},
        ]
    },
    {
        "name": "Bharti Airtel Limited",
        "sector": "Telecommunication",
        "industry": "Telecom Services",
        "description": "Bharti Airtel is a leading global telecommunications company with operations in 18 countries across South Asia and Africa.",
        "symbol": "BHARTIARTL",
        "isin": "INE397D01024",
        "provider_instrument_id": "NSE_EQ|INE397D01024",
        "quote": {
            "last_price": 1690.45,
            "open": 1675.00,
            "high": 1705.00,
            "low": 1670.00,
            "previous_close": 1680.25,
            "volume": 4980000,
        },
        "metrics": [
            {"metric_name": "Revenue", "value": 149982.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Net Profit", "value": 7467.0, "unit": "INR Crores", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "Operating Margin", "value": 52.3, "unit": "%", "reporting_period": "FY24", "period_type": "annual"},
            {"metric_name": "PE Ratio", "value": 68.4, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "PB Ratio", "value": 8.5, "unit": "x", "reporting_period": "TTM", "period_type": "ttm"},
            {"metric_name": "Debt to Equity", "value": 1.72, "unit": "ratio", "reporting_period": "FY24", "period_type": "annual"},
        ]
    }
]


async def seed_database():
    setup_logging()
    logger.info("Initializing database schema...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(Company))
        existing_companies = result.scalars().all()
        if existing_companies:
            logger.info(f"Database already contains {len(existing_companies)} companies. Skipping seed.")
            return

        logger.info(f"Seeding {len(SEED_COMPANIES)} initial Indian equity companies & instruments...")
        now = utc_now()

        for c_data in SEED_COMPANIES:
            company = Company(
                name=c_data["name"],
                sector=c_data["sector"],
                industry=c_data["industry"],
                description=c_data["description"],
                created_at=now,
                updated_at=now
            )
            session.add(company)
            await session.flush()

            # Create NSE instrument
            nse_instrument = Instrument(
                company_id=company.id,
                exchange="NSE",
                symbol=c_data["symbol"],
                isin=c_data["isin"],
                provider_instrument_id=c_data["provider_instrument_id"],
                currency="INR",
                active=True
            )
            session.add(nse_instrument)

            # Create BSE instrument
            bse_instrument = Instrument(
                company_id=company.id,
                exchange="BSE",
                symbol=c_data["symbol"],
                isin=c_data["isin"],
                provider_instrument_id=f"BSE_EQ|{c_data['symbol']}",
                currency="INR",
                active=True
            )
            session.add(bse_instrument)
            await session.flush()

            # Create latest market quote for NSE instrument
            q = c_data["quote"]
            quote = MarketQuote(
                instrument_id=nse_instrument.id,
                last_price=q["last_price"],
                open=q["open"],
                high=q["high"],
                low=q["low"],
                previous_close=q["previous_close"],
                volume=q["volume"],
                provider="mock_seed",
                market_timestamp=now,
                fetched_at=now,
                data_status="realtime"
            )
            session.add(quote)

            # Create financial metrics
            for m in c_data.get("metrics", []):
                metric = FinancialMetric(
                    company_id=company.id,
                    metric_name=m["metric_name"],
                    value=m["value"],
                    unit=m["unit"],
                    currency="INR",
                    reporting_period=m["reporting_period"],
                    period_type=m["period_type"],
                    reported_at=now,
                    source_id="annual_report_seed"
                )
                session.add(metric)

        await session.commit()
        logger.info("Database seeding completed successfully.")

    await close_db()


if __name__ == "__main__":
    asyncio.run(seed_database())

