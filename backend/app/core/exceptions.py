from typing import Any, Optional


class StockIntelligenceException(Exception):
    """Base exception for all domain errors in the platform."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class ProviderException(StockIntelligenceException):
    """Raised when market data provider fails or returns unparseable data."""
    def __init__(self, message: str, provider: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message, details)
        self.provider = provider
        self.status_code = status_code


class InstrumentNotFoundException(StockIntelligenceException):
    """Raised when an instrument or symbol cannot be resolved."""
    pass


class StaleDataException(StockIntelligenceException):
    """Raised when requested data is older than allowed freshness threshold."""
    pass


class GuardrailViolationException(StockIntelligenceException):
    """Raised when an agent safety or citation validation guardrail trips."""
    pass


class CalculationException(StockIntelligenceException):
    """Raised when financial mathematical calculation encounters invalid input."""
    pass

