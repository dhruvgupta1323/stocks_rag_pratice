import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.company import Company
    from backend.app.models.market_data import MarketQuote, PriceBar


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(10), nullable=False, default="NSE")  # NSE, BSE
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    isin: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    provider_instrument_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("exchange", "symbol", name="uq_exchange_symbol"),
        UniqueConstraint("exchange", "provider_instrument_id", name="uq_exchange_provider_id"),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="instruments")
    quotes: Mapped[List["MarketQuote"]] = relationship("MarketQuote", back_populates="instrument", cascade="all, delete-orphan")
    price_bars: Mapped[List["PriceBar"]] = relationship("PriceBar", back_populates="instrument", cascade="all, delete-orphan")

