from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.project_document import DocumentType


class ProjectDocumentCreateRequest(BaseModel):
    title: str
    doc_type: DocumentType
    content: str


class ProjectDocumentUpdateRequest(BaseModel):
    title: str | None = None
    doc_type: DocumentType | None = None
    content: str | None = None


class ProjectDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    doc_type: DocumentType
    content: str
    created_by_id: int
    created_at: datetime
    updated_at: datetime
