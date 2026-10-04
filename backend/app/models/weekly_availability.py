"""
Weekly/recurring work schedule configuration.

Employees set their working hours once (e.g., Monday 9-5, Tuesday 9-5).
This is separate from the per-day availability model, which tracks actual daily status.

Used for:
- Initial availability setup (mandatory on first login)
- Workload calculations
- Expected capacity planning
"""
from datetime import datetime, time
import enum

from sqlalchemy import DateTime, ForeignKey, String, Time, Integer, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DayOfWeek(str, enum.Enum):
    """Days of the week (ISO 8601 style: Monday=0, Sunday=6)."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class WeeklyAvailability(Base):
    """
    Recurring weekly work schedule for an employee.
    
    Example: Employee works Mon-Fri 9:00-17:30, unavailable weekends.
    """
    __tablename__ = "weekly_availability"
    __table_args__ = (
        UniqueConstraint("user_id", "day_of_week", name="uq_weekly_availability_user_day"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Day of week
    day_of_week: Mapped[DayOfWeek] = mapped_column(SAEnum(DayOfWeek), nullable=False)

    # Working hours for this day (nullable = day off/unavailable)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    # Optional: timezone for international teams
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True, default="UTC")

    # Version tracking: when this schedule became effective
    effective_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # NULL = current

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
