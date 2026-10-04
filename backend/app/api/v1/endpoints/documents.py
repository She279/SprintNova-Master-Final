from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models.user import User
from app.schemas.document import ProjectDocumentCreateRequest, ProjectDocumentUpdateRequest, ProjectDocumentResponse
from app.api.deps import require_password_already_set
from app.services import project_service, document_service

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["Project Knowledge (RAG)"])


@router.post("", response_model=ProjectDocumentResponse, status_code=201)
def create_document(
    project_id: int, payload: ProjectDocumentCreateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role.value == "client":
        from fastapi import HTTPException, status
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Client accounts cannot access internal project knowledge")
    return document_service.create_document(db, project_id, payload, author=user)


@router.get("", response_model=list[ProjectDocumentResponse])
def list_documents(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role.value == "client":
        from fastapi import HTTPException, status
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Client accounts cannot access internal project knowledge")
    return document_service.list_documents(db, project_id)


@router.patch("/{document_id}", response_model=ProjectDocumentResponse)
def update_document(
    project_id: int, document_id: int, payload: ProjectDocumentUpdateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role.value == "client":
        from fastapi import HTTPException, status
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Client accounts cannot modify internal project knowledge")
    doc = document_service.get_document_or_404(db, project_id, document_id)
    return document_service.update_document(db, doc, payload)


@router.delete("/{document_id}", status_code=204)
def delete_document(project_id: int, document_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role.value == "client":
        from fastapi import HTTPException, status
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Client accounts cannot modify internal project knowledge")
    doc = document_service.get_document_or_404(db, project_id, document_id)
    document_service.delete_document(db, doc)
