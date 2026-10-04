from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models.user import User
from app.schemas.sprint import (
    SprintCreateRequest, SprintUpdateRequest, SprintResponse, SprintDetailResponse,
    BurndownResponse, VelocityResponse,
)
from app.api.deps import require_password_already_set
from app.services import project_service, sprint_service

router = APIRouter(prefix="/projects/{project_id}/sprints", tags=["Sprints"])


@router.post("", response_model=SprintResponse, status_code=201)
def create_sprint(project_id: int, payload: SprintCreateRequest, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_sprint_manage_access(db, project, user)
    return sprint_service.create_sprint(db, project, payload, created_by=user)


@router.get("", response_model=list[SprintResponse])
def list_sprints(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return sprint_service.list_sprints(db, project_id)


@router.get("/velocity", response_model=VelocityResponse)
def get_velocity(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return sprint_service.get_velocity(db, project_id)


@router.get("/{sprint_id}", response_model=SprintDetailResponse)
def get_sprint(project_id: int, sprint_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    sprint = sprint_service.get_sprint_or_404(db, project_id, sprint_id)
    return sprint_service.get_sprint_detail(db, sprint)


@router.patch("/{sprint_id}", response_model=SprintResponse)
def update_sprint(
    project_id: int, sprint_id: int, payload: SprintUpdateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_sprint_manage_access(db, project, user)
    sprint = sprint_service.get_sprint_or_404(db, project_id, sprint_id)
    return sprint_service.update_sprint(db, sprint, payload)


@router.post("/{sprint_id}/start", response_model=SprintResponse)
def start_sprint(project_id: int, sprint_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_sprint_manage_access(db, project, user)
    sprint = sprint_service.get_sprint_or_404(db, project_id, sprint_id)
    return sprint_service.start_sprint(db, sprint)


@router.post("/{sprint_id}/close", response_model=SprintResponse)
def close_sprint(project_id: int, sprint_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_sprint_manage_access(db, project, user)
    sprint = sprint_service.get_sprint_or_404(db, project_id, sprint_id)
    return sprint_service.close_sprint(db, sprint)


@router.post("/{sprint_id}/cancel", response_model=SprintResponse)
def cancel_sprint(project_id: int, sprint_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_sprint_manage_access(db, project, user)
    sprint = sprint_service.get_sprint_or_404(db, project_id, sprint_id)
    return sprint_service.cancel_sprint(db, sprint)


@router.get("/{sprint_id}/burndown", response_model=BurndownResponse)
def get_burndown(project_id: int, sprint_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    sprint = sprint_service.get_sprint_or_404(db, project_id, sprint_id)
    return sprint_service.get_burndown(db, sprint)
