from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_db
from app.models.user import User
from app.models.role import RoleEnum
from app.models.testing_enums import BugStatus, BugSeverity
from app.schemas.bug import (
    BugCreateRequest, BugUpdateRequest, BugResponse,
    BugCommentCreateRequest, BugCommentResponse, BugHistoryEntry,
)
from app.api.deps import require_password_already_set
from app.services import project_service, bug_service

router = APIRouter(prefix="/projects/{project_id}/bugs", tags=["Bugs"])

_FULL_EDIT_FIELDS = {"status"}  # any project member may move a bug through its lifecycle


@router.post("", response_model=BugResponse, status_code=201)
def create_bug(project_id: int, payload: BugCreateRequest, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")  # any project member can report a bug
    return bug_service.create_bug(db, project, payload, reporter=user)


@router.get("", response_model=list[BugResponse])
def list_bugs(
    project_id: int, status: BugStatus | None = Query(None), severity: BugSeverity | None = Query(None),
    assignee_id: int | None = Query(None), db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    return bug_service.list_bugs(db, project_id, status_filter=status, severity_filter=severity, assignee_id=assignee_id)


@router.patch("/{bug_id}", response_model=BugResponse)
def update_bug(
    project_id: int, bug_id: int, payload: BugUpdateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    bug = bug_service.get_bug_or_404(db, project_id, bug_id)

    is_privileged = (
        project_service.is_tester_on_project(db, project, user)
        or project_service.is_product_owner_on_project(db, project, user)
        or project_service.is_scrum_master_on_project(db, project, user)
        or bug.reporter_id == user.id
        or bug.assignee_id == user.id
    )
    changes = set(payload.model_dump(exclude_unset=True).keys())
    if not is_privileged and changes - _FULL_EDIT_FIELDS:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only the reporter, assignee, a Tester, Product Owner, Scrum Master, or Admin can edit bug details; "
            "any team member may update its status",
        )

    return bug_service.update_bug(db, bug, payload, changed_by=user)


@router.post("/{bug_id}/comments", response_model=BugCommentResponse, status_code=201)
def add_comment(
    project_id: int, bug_id: int, payload: BugCommentCreateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    bug = bug_service.get_bug_or_404(db, project_id, bug_id)
    return bug_service.add_comment(db, bug, payload, author=user)


@router.get("/{bug_id}/comments", response_model=list[BugCommentResponse])
def list_comments(project_id: int, bug_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    bug_service.get_bug_or_404(db, project_id, bug_id)
    return bug_service.list_comments(db, bug_id)


@router.get("/{bug_id}/history", response_model=list[BugHistoryEntry])
def get_history(project_id: int, bug_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    bug_service.get_bug_or_404(db, project_id, bug_id)
    return bug_service.list_history(db, bug_id)
