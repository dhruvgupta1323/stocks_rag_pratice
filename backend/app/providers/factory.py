from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.providers.base import BaseMarketDataProvider
from backend.app.providers.upstox import UpstoxProvider
from backend.app.providers.twelvedata import TwelveDataProvider
from backend.app.providers.yfinance import YahooFinanceProvider
from backend.app.providers.mock import MockMarketDataProvider

_provider_instance: BaseMarketDataProvider = None


def get_market_data_provider() -> BaseMarketDataProvider:
    """Factory returning the active market data provider adapter based on environment configuration."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    prov = settings.DATA_PROVIDER.lower().strip()

    if prov == "yfinance":
        logger.info("Initializing Yahoo Finance (Free Real-time & Historical Data) adapter.")
        _provider_instance = YahooFinanceProvider()
    elif prov == "twelvedata" and settings.TWELVE_DATA_API_KEY:
        logger.info("Initializing Twelve Data market data provider adapter.")
        _provider_instance = TwelveDataProvider()
    elif prov == "upstox" and settings.UPSTOX_ACCESS_TOKEN:
        logger.info("Initializing Upstox live market data provider adapter.")
        _provider_instance = UpstoxProvider()
    else:
        logger.info(
            f"Active provider '{settings.DATA_PROVIDER}' has no live credentials configured or requires mock mode. "
            "Using MockMarketDataProvider (deterministic simulated NSE/BSE quotes labeled with data_status='mock')."
        )
        _provider_instance = MockMarketDataProvider()

    return _provider_instance
