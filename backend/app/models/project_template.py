from datetime import datetime

from sqlalchemy import String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectTemplate(Base):
    """
    Reusable project blueprints (spec: "maintain project templates").

    `default_milestones` is a JSON list of
    {"title": str, "phase": str | None, "offset_days": int} objects --
    `offset_days` is relative to the new project's start date, so applying
    the same template to different projects produces different due dates.

    `default_project_roles` is a JSON list of ProjectRole values the
    template suggests staffing for (used by the team-allocation AI
    suggestion and by the "apply template" UI as a checklist).
    """
    __tablename__ = "project_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    default_milestones: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    default_project_roles: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
