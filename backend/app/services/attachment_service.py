from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from app.models.project_attachment import ProjectAttachment
from app.models.user import User

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads" / "projects"
MAX_BYTES = 10 * 1024 * 1024

def _safe_name(name: str) -> str:
    return Path(name or "attachment").name[:255]

def save_attachment(db: Session, project_id: int, user: User, file: UploadFile) -> ProjectAttachment:
    original = _safe_name(file.filename or "attachment")
    content = file.file.read(MAX_BYTES + 1)
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uploaded file is empty")
    if len(content) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds the 10 MB project attachment limit")
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid4().hex}_{original}"
    (UPLOAD_ROOT / stored).write_bytes(content)
    item = ProjectAttachment(project_id=project_id, uploaded_by_id=user.id, original_name=original, stored_name=stored, content_type=file.content_type, size_bytes=len(content))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def list_attachments(db: Session, project_id: int):
    return db.query(ProjectAttachment).filter(ProjectAttachment.project_id == project_id).order_by(ProjectAttachment.created_at.desc()).all()

def get_attachment(db: Session, project_id: int, attachment_id: int) -> ProjectAttachment:
    item = db.query(ProjectAttachment).filter(ProjectAttachment.project_id == project_id, ProjectAttachment.id == attachment_id).first()
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Attachment not found")
    return item

def delete_attachment(db: Session, item: ProjectAttachment):
    path = UPLOAD_ROOT / item.stored_name
    if path.exists():
        path.unlink()
    db.delete(item)
    db.commit()
