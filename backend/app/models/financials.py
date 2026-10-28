import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.company import Company


class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="INR Crores")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    reporting_period: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "Q1 FY25", "FY24"
    period_type: Mapped[str] = mapped_column(String(20), nullable=False, default="quarterly")  # quarterly, annual, ttm, ytd
    reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_fin_company_metric_period", "company_id", "metric_name", "reporting_period"),
    )

    company: Mapped["Company"] = relationship("Company", back_populates="financial_metrics")

