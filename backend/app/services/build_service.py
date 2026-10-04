from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.build import Build
from app.models.testing_enums import BuildStatus
from app.schemas.build import BuildCreateRequest, BuildUpdateRequest


def create_build(db: Session, project_id: int, payload: BuildCreateRequest, triggered_by) -> Build:
    build = Build(project_id=project_id, triggered_by_id=triggered_by.id, **payload.model_dump())
    db.add(build)
    db.commit()
    db.refresh(build)
    return build


def list_builds(db: Session, project_id: int) -> list[Build]:
    return db.query(Build).filter(Build.project_id == project_id).order_by(Build.created_at.desc()).all()


def get_build_or_404(db: Session, project_id: int, build_id: int) -> Build:
    build = db.query(Build).filter(Build.id == build_id, Build.project_id == project_id).first()
    if not build:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Build not found")
    return build


def update_build(db: Session, build: Build, payload: BuildUpdateRequest) -> Build:
    build.status = payload.status
    if payload.log_summary is not None:
        build.log_summary = payload.log_summary
    if payload.status in (BuildStatus.SUCCESSFUL, BuildStatus.FAILED):
        build.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(build)
    return build
