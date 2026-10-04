from datetime import datetime

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.scrum_enums import StoryPriority, StoryStatus


class UserStory(Base):
    """
    A backlog item, structured as: "As a [user], I want [feature], so that
    [benefit]." `key` is a human-readable ticket code like "SN-001-7"
    (project code + sequence), the same idea as a Jira issue key.
    """
    __tablename__ = "user_stories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    epic_id: Mapped[int | None] = mapped_column(ForeignKey("epics.id"), nullable=True)
    sprint_id: Mapped[int | None] = mapped_column(ForeignKey("sprints.id"), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)

    priority: Mapped[StoryPriority] = mapped_column(SAEnum(StoryPriority), default=StoryPriority.MEDIUM, nullable=False)
    story_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[StoryStatus] = mapped_column(SAEnum(StoryStatus), default=StoryStatus.BACKLOG, nullable=False)
    labels: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Backlog-wide manual ordering (drag-and-drop priority), independent of
    # the `priority` field -- two stories can both be "High" but still need
    # a relative order within the backlog.
    backlog_rank: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
