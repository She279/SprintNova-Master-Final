"""
Daily work updates submitted by employees at end of working day.

Captures what was accomplished, what's pending, blockers, and risks.
AI analysis of these updates creates actionable insights.
"""
from datetime import datetime, date

from sqlalchemy import DateTime, Date, ForeignKey, Text, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DailyWorkUpdate(Base):
    """
    Daily work update submitted by an employee.
    
    Fields capture:
    - What work was done
    - What was completed
    - What is still pending
    - Blockers encountered
    - Progress percentage
    """
    __tablename__ = "daily_work_updates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True, index=True)

    # Date of the update
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Update content
    work_done: Mapped[str | None] = mapped_column(Text, nullable=True)  # What did you work on?
    completed_work: Mapped[str | None] = mapped_column(Text, nullable=True)  # What did you complete?
    pending_work: Mapped[str | None] = mapped_column(Text, nullable=True)  # What is still pending?
    blockers: Mapped[str | None] = mapped_column(Text, nullable=True)  # Any blockers?
    additional_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Extra notes

    # Progress tracking
    progress_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100

    # Audit trail
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
