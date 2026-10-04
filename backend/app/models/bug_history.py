from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BugHistory(Base):
    """Field-level activity log for a bug, same pattern as TaskHistory --
    populated automatically by bug_service on every status/assignee/
    severity/priority change."""
    __tablename__ = "bug_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bug_id: Mapped[int] = mapped_column(ForeignKey("bugs.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    field_changed: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
