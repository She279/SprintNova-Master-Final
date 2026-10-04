from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models.user import User
from app.schemas.epic import EpicCreateRequest, EpicResponse
from app.api.deps import require_password_already_set
from app.services import project_service, epic_service

router = APIRouter(prefix="/projects/{project_id}/epics", tags=["Backlog"])


@router.post("", response_model=EpicResponse, status_code=201)
def create_epic(project_id: int, payload: EpicCreateRequest, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_backlog_manage_access(db, project, user)
    return epic_service.create_epic(db, project_id, payload)


@router.get("", response_model=list[EpicResponse])
def list_epics(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return epic_service.list_epics(db, project_id)
