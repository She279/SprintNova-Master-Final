import enum
from datetime import datetime

from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NotificationType(str, enum.Enum):
    PROJECT_CREATED = "project_created"
    PROJECT_STATUS_CHANGED = "project_status_changed"
    TEAM_MEMBER_ADDED = "team_member_added"
    TEAM_MEMBER_REMOVED = "team_member_removed"
    MILESTONE_STATUS_CHANGED = "milestone_status_changed"
    LEAVE_REQUEST_SUBMITTED = "leave_request_submitted"
    LEAVE_REQUEST_DECIDED = "leave_request_decided"
    STORY_ASSIGNED = "story_assigned"
    SPRINT_STARTED = "sprint_started"
    SPRINT_COMPLETED = "sprint_completed"
    TASK_ASSIGNED = "task_assigned"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_COMMENT_ADDED = "task_comment_added"
    BUG_ASSIGNED = "bug_assigned"
    BUG_STATUS_CHANGED = "bug_status_changed"
    BUG_COMMENT_ADDED = "bug_comment_added"
    DAILY_UPDATE_PENDING = "daily_update_pending"
    AVAILABILITY_REQUIRED = "availability_required"
    AI_RISK_DETECTED = "ai_risk_detected"


class Notification(Base):
    """
    In-app notification center, backing the "project notifications" spec
    requirement. Every notification here is also, where relevant, emailed
    through `email_service` -- this table is what powers a bell icon /
    notification list in the UI so the person doesn't have to rely on email.
    """
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
