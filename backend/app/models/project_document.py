import enum
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DocumentType(str, enum.Enum):
    DOCUMENTATION = "documentation"
    REQUIREMENT = "requirement"
    SPRINT_NOTE = "sprint_note"
    GUIDELINE = "guideline"
    TESTING_DOC = "testing_doc"


class ProjectDocument(Base):
    """
    Free-form project knowledge (requirements, sprint notes, guidelines,
    testing docs, ...) that the AI assistant retrieves from via ChromaDB
    to answer natural-language questions. This table is the source of
    truth; the Chroma collection is a derived index that can always be
    rebuilt from it (see rag_service.reindex_project).
    """
    __tablename__ = "project_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    doc_type: Mapped[DocumentType] = mapped_column(SAEnum(DocumentType), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
