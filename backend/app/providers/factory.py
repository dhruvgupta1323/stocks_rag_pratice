from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.providers.base import BaseMarketDataProvider
from backend.app.providers.upstox import UpstoxProvider
from backend.app.providers.mock import MockMarketDataProvider

_provider_instance: BaseMarketDataProvider = None


def get_market_data_provider() -> BaseMarketDataProvider:
    """Factory returning the active market data provider adapter based on environment configuration."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    if settings.DATA_PROVIDER.lower() == "upstox" and settings.UPSTOX_ACCESS_TOKEN:
        logger.info("Initializing Upstox live market data provider adapter.")
        _provider_instance = UpstoxProvider()
    else:
        logger.info(
            "Using MockMarketDataProvider (deterministic simulated NSE/BSE quotes with explicit mock status labels). "
            "To use live Upstox data, configure UPSTOX_API_KEY and UPSTOX_ACCESS_TOKEN in backend environment."
        )
        _provider_instance = MockMarketDataProvider()

    return _provider_instance

