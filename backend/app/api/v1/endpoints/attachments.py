from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from app.core.database import get_db
from app.models.user import User
from app.api.deps import require_password_already_set
from app.services import project_service, attachment_service

router = APIRouter(prefix="/projects/{project_id}/attachments", tags=["Project Attachments"])

@router.post("", response_model=dict, status_code=201)
def upload_attachment(project_id: int, file: UploadFile = File(...), db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role.value == "client":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Client accounts cannot upload internal project files")
    item = attachment_service.save_attachment(db, project_id, user, file)
    return {"id": item.id, "project_id": item.project_id, "original_name": item.original_name, "content_type": item.content_type, "size_bytes": item.size_bytes, "created_at": item.created_at}

@router.get("", response_model=list)
def list_project_attachments(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role.value == "client":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Client accounts cannot access internal project attachments")
    return attachment_service.list_attachments(db, project_id)

@router.get("/{attachment_id}/download")
def download_attachment(project_id: int, attachment_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role.value == "client":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Client accounts cannot access internal project attachments")
    item = attachment_service.get_attachment(db, project_id, attachment_id)
    path = attachment_service.UPLOAD_ROOT / item.stored_name
    return FileResponse(path, filename=item.original_name, media_type=item.content_type or "application/octet-stream")

@router.delete("/{attachment_id}", status_code=204)
def delete_attachment(project_id: int, attachment_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    item = attachment_service.get_attachment(db, project_id, attachment_id)
    if user.role.value != "owner_admin" and item.uploaded_by_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the uploader or an admin can delete this file")
    attachment_service.delete_attachment(db, item)
