from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.testing_enums import BuildStatus


class Build(Base):
    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)

    label: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "build-142" or a commit-ish
    status: Mapped[BuildStatus] = mapped_column(SAEnum(BuildStatus), default=BuildStatus.RUNNING, nullable=False)
    log_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    triggered_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
