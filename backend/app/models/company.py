import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, utc_now

if TYPE_CHECKING:
    from backend.app.models.instrument import Instrument
    from backend.app.models.financials import FinancialMetric
    from backend.app.models.research import ResearchRecord


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sector: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    industry: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    instruments: Mapped[List["Instrument"]] = relationship("Instrument", back_populates="company", cascade="all, delete-orphan")
    financial_metrics: Mapped[List["FinancialMetric"]] = relationship("FinancialMetric", back_populates="company", cascade="all, delete-orphan")
    research_records: Mapped[List["ResearchRecord"]] = relationship("ResearchRecord", back_populates="company", cascade="all, delete-orphan")

