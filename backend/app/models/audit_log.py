"""
Audit logging for important system events.

Tracks:
- Work session start/stop
- Availability changes
- Daily update submissions
- AI suggestion acceptances/rejections
- Permission-protected operations
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """Record of a significant system action."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Who performed the action
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # What action
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # e.g., "work_session_started", "daily_update_submitted", "ai_suggestion_accepted"

    # What entity was affected
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    # e.g., "work_session", "daily_work_update", "task"

    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # e.g., work_session.id or daily_work_update.id

    # What changed
    changes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON representation of the change (old values vs. new values)

    # Context
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
