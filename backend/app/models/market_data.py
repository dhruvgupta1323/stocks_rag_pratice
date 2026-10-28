import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Float, BigInteger, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, utc_now

if TYPE_CHECKING:
    from backend.app.models.instrument import Instrument


class MarketQuote(Base):
    __tablename__ = "market_quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    instrument_id: Mapped[str] = mapped_column(String(36), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    last_price: Mapped[float] = mapped_column(Float, nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    previous_close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    market_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    data_status: Mapped[str] = mapped_column(String(30), nullable=False, default="realtime")  # realtime, delayed, cached, mock, unavailable

    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="quotes")


class PriceBar(Base):
    __tablename__ = "price_bars"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    instrument_id: Mapped[str] = mapped_column(String(36), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    interval: Mapped[str] = mapped_column(String(10), nullable=False)  # 1d, 1h, 15m, 5m
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("instrument_id", "interval", "timestamp", name="uq_instrument_interval_time"),
        Index("idx_bars_instrument_time", "instrument_id", "interval", "timestamp"),
    )

    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="price_bars")

