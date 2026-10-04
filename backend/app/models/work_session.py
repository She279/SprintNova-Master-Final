"""
Work session tracking for individual employees.

Records when an employee starts and stops working, enabling:
- Daily/weekly work time aggregation
- Workload calculations
- "Currently working" status on dashboards
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkSessionStatus(str):
    """Work session states."""
    ACTIVE = "active"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"


class WorkSession(Base):
    """Individual employee work session."""
    __tablename__ = "work_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Session lifecycle
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Duration in minutes (calculated on end)
    total_work_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status: active, completed, interrupted
    status: Mapped[str] = mapped_column(String(50), default=WorkSessionStatus.ACTIVE, nullable=False)

    # Track creation/update times
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
