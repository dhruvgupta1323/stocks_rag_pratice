import pytest
from backend.app.providers.twelvedata import TwelveDataProvider
from backend.app.core.exceptions import ProviderException


def test_twelvedata_requires_api_key():
    prov = TwelveDataProvider(api_key=None)
    with pytest.raises(ProviderException) as exc_info:
        prov._require_api_key()
    assert "Twelve Data API key is not configured" in str(exc_info.value)
    assert exc_info.value.provider == "twelvedata"
    assert exc_info.value.status_code == 401


def test_twelvedata_provider_name():
    prov = TwelveDataProvider(api_key="demo_key")
    assert prov.provider_name == "twelvedata"
