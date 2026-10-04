from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.project_enums import ProjectRole


class ProjectMember(Base):
    """
    The team roster for a project -- who's on it and in what project role.
    Future modules (Sprints, Kanban, Bugs) will check membership here before
    allowing someone to be assigned a task/story/bug on the project.
    """
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    project_role: Mapped[ProjectRole] = mapped_column(SAEnum(ProjectRole), nullable=False)

    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="members")
