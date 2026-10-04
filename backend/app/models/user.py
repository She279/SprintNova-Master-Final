"""
Core `users` table -- the identity foundation every other SprintNova module
(Projects, Sprints, Kanban, Bugs, Reports, AI...) will reference via
user_id foreign keys. Do not put project/sprint/task fields here; this
model stays scoped to identity & auth.
"""
from datetime import datetime, date

from sqlalchemy import String, Boolean, DateTime, Date, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.role import RoleEnum


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    employee_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Real-world address the employee owns -- used for account notifications,
    # temp password delivery, OTP, password recovery. Any valid provider allowed.
    personal_email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Auto-generated SprintNova login identity, e.g. arun.kumar@sprintnova.com
    company_email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    role: Mapped[RoleEnum] = mapped_column(SAEnum(RoleEnum), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    skills: Mapped[str | None] = mapped_column(String(500), nullable=True)  # comma-separated for now
    experience: Mapped[str | None] = mapped_column(String(100), nullable=True)
    joining_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    personal_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
