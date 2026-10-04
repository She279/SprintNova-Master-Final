from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.epic import Epic
from app.schemas.epic import EpicCreateRequest


def create_epic(db: Session, project_id: int, payload: EpicCreateRequest) -> Epic:
    epic = Epic(project_id=project_id, **payload.model_dump())
    db.add(epic)
    db.commit()
    db.refresh(epic)
    return epic


def list_epics(db: Session, project_id: int) -> list[Epic]:
    return db.query(Epic).filter(Epic.project_id == project_id).order_by(Epic.created_at).all()


def get_epic_or_404(db: Session, project_id: int, epic_id: int) -> Epic:
    epic = db.query(Epic).filter(Epic.id == epic_id, Epic.project_id == project_id).first()
    if not epic:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Epic not found")
    return epic
