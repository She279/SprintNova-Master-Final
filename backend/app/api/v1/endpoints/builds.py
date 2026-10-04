from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.models.user import User
from app.models.role import RoleEnum
from app.schemas.build import BuildCreateRequest, BuildUpdateRequest, BuildResponse
from app.api.deps import require_password_already_set
from app.services import project_service, build_service

router = APIRouter(prefix="/projects/{project_id}/builds", tags=["XP Quality"])


@router.post("", response_model=BuildResponse, status_code=201)
def create_build(project_id: int, payload: BuildCreateRequest, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    return build_service.create_build(db, project_id, payload, triggered_by=user)


@router.get("", response_model=list[BuildResponse])
def list_builds(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    return build_service.list_builds(db, project_id)


@router.patch("/{build_id}", response_model=BuildResponse)
def update_build(
    project_id: int, build_id: int, payload: BuildUpdateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    build = build_service.get_build_or_404(db, project_id, build_id)
    return build_service.update_build(db, build, payload)
