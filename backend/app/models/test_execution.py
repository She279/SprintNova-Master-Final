from datetime import datetime

from sqlalchemy import Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.testing_enums import ExecutionResult


class TestExecution(Base):
    """
    One execution attempt of a TestCase. A test case can be run many times
    across builds/regressions -- this table is the history; TestCase.status
    reflects the most recent execution's result.
    """
    __tablename__ = "test_executions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"), nullable=False, index=True)
    executed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    result: Mapped[ExecutionResult] = mapped_column(SAEnum(ExecutionResult), nullable=False)
    actual_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
