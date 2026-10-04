import enum
from datetime import datetime, date

from sqlalchemy import DateTime, Date, ForeignKey, String, Float, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class Availability(Base):
    """
    Per-employee, per-day availability. Sprint planning (Module 3) and the
    AI workload/allocation suggestions in this module both read this table
    to know real capacity rather than assuming everyone is always free.
    """
    __tablename__ = "availability"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_availability_user_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    status: Mapped[AvailabilityStatus] = mapped_column(SAEnum(AvailabilityStatus), nullable=False)
    hours_available: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
