from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_db
from app.models.user import User
from app.models.role import RoleEnum
from app.models.task_enums import TaskStatus
from app.schemas.task import (
    TaskCreateRequest, TaskUpdateRequest, TaskResponse,
    TaskCommentCreateRequest, TaskCommentResponse, TaskHistoryEntry,
)
from app.api.deps import require_password_already_set
from app.services import project_service, task_service

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Tasks & Kanban"])

_FULL_EDIT_FIELDS = {"status"}  # fields any project member may change (drag-and-drop the card)


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(project_id: int, payload: TaskCreateRequest, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")  # any project member can add a card
    return task_service.create_task(db, project, payload, reporter=user)


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    project_id: int, status: TaskStatus | None = Query(None), sprint_id: int | None = Query(None),
    assignee_id: int | None = Query(None), db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    return task_service.list_tasks(db, project_id, status_filter=status, sprint_id=sprint_id, assignee_id=assignee_id)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    project_id: int, task_id: int, payload: TaskUpdateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    task = task_service.get_task_or_404(db, project_id, task_id)

    changes = set(payload.model_dump(exclude_unset=True).keys())
    is_privileged = (
        project_service.is_product_owner_on_project(db, project, user)
        or project_service.is_scrum_master_on_project(db, project, user)
        or task.reporter_id == user.id
    )
    if not is_privileged and changes - _FULL_EDIT_FIELDS:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only the reporter, Product Owner, Scrum Master, or an Admin can edit task details; "
            "any team member may move the card's status",
        )

    return task_service.update_task(db, task, payload, changed_by=user)


@router.delete("/{task_id}", status_code=204)
def delete_task(project_id: int, task_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    task = task_service.get_task_or_404(db, project_id, task_id)
    is_privileged = (
        project_service.is_product_owner_on_project(db, project, user)
        or project_service.is_scrum_master_on_project(db, project, user)
        or task.reporter_id == user.id
    )
    if not is_privileged:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the reporter, Product Owner, Scrum Master, or an Admin can delete a task")
    task_service.delete_task(db, task)


@router.post("/{task_id}/comments", response_model=TaskCommentResponse, status_code=201)
def add_comment(
    project_id: int, task_id: int, payload: TaskCommentCreateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    task = task_service.get_task_or_404(db, project_id, task_id)
    return task_service.add_comment(db, task, payload, author=user)


@router.get("/{task_id}/comments", response_model=list[TaskCommentResponse])
def list_comments(project_id: int, task_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    task_service.get_task_or_404(db, project_id, task_id)
    return task_service.list_comments(db, task_id)


@router.get("/{task_id}/history", response_model=list[TaskHistoryEntry])
def get_history(project_id: int, task_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    task_service.get_task_or_404(db, project_id, task_id)
    return task_service.list_history(db, task_id)
