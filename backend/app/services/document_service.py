from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project_document import ProjectDocument
from app.models.user import User
from app.schemas.document import ProjectDocumentCreateRequest, ProjectDocumentUpdateRequest
from app.services import rag_service


def create_document(db: Session, project_id: int, payload: ProjectDocumentCreateRequest, author: User) -> ProjectDocument:
    doc = ProjectDocument(project_id=project_id, created_by_id=author.id, **payload.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    rag_service.index_document(doc)
    return doc


def list_documents(db: Session, project_id: int) -> list[ProjectDocument]:
    return (
        db.query(ProjectDocument)
        .filter(ProjectDocument.project_id == project_id)
        .order_by(ProjectDocument.created_at.desc())
        .all()
    )


def get_document_or_404(db: Session, project_id: int, document_id: int) -> ProjectDocument:
    doc = (
        db.query(ProjectDocument)
        .filter(ProjectDocument.id == document_id, ProjectDocument.project_id == project_id)
        .first()
    )
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return doc


def update_document(db: Session, doc: ProjectDocument, payload: ProjectDocumentUpdateRequest) -> ProjectDocument:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
    db.commit()
    db.refresh(doc)
    rag_service.index_document(doc)  # re-index with the updated content
    return doc


def delete_document(db: Session, doc: ProjectDocument) -> None:
    rag_service.remove_document(doc.project_id, doc.id)
    db.delete(doc)
    db.commit()
