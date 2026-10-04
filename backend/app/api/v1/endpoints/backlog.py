from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_db
from app.models.user import User
from app.models.scrum_enums import StoryStatus
from app.schemas.user_story import (
    UserStoryCreateRequest, UserStoryUpdateRequest, UserStoryResponse,
    BacklogReorderRequest, AssignToSprintRequest,
)
from app.api.deps import require_password_already_set
from app.services import project_service, backlog_service

router = APIRouter(prefix="/projects/{project_id}/backlog", tags=["Backlog"])


@router.post("", response_model=UserStoryResponse, status_code=201)
def create_story(
    project_id: int, payload: UserStoryCreateRequest, db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_backlog_manage_access(db, project, user)
    return backlog_service.create_story(db, project, payload, reporter=user)


@router.get("", response_model=list[UserStoryResponse])
def list_backlog(
    project_id: int, sprint_id: int | None = Query(None), status: StoryStatus | None = Query(None),
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return backlog_service.list_backlog(db, project_id, sprint_id=sprint_id, status_filter=status)


@router.patch("/{story_id}", response_model=UserStoryResponse)
def update_story(
    project_id: int, story_id: int, payload: UserStoryUpdateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    story = backlog_service.get_story_or_404(db, project_id, story_id)

    is_po = project_service.is_product_owner_on_project(db, project, user)
    is_owner_of_story = story.assignee_id == user.id
    changes = payload.model_dump(exclude_unset=True)

    if not is_po:
        # Non-Product-Owners (e.g. the assignee moving their own story
        # through the workflow) may only change `status`.
        if not is_owner_of_story or set(changes.keys()) - {"status"}:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Only the Product Owner can edit story details; the assignee may update its status",
            )

    return backlog_service.update_story(db, story, payload)


@router.delete("/{story_id}", status_code=204)
def delete_story(project_id: int, story_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_backlog_manage_access(db, project, user)
    story = backlog_service.get_story_or_404(db, project_id, story_id)
    backlog_service.delete_story(db, story)


@router.post("/reorder", response_model=list[UserStoryResponse])
def reorder_backlog(
    project_id: int, payload: BacklogReorderRequest, db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_backlog_manage_access(db, project, user)
    return backlog_service.reorder_backlog(db, project_id, payload)


@router.patch("/{story_id}/sprint", response_model=UserStoryResponse)
def assign_to_sprint(
    project_id: int, story_id: int, payload: AssignToSprintRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_manage_access(db, project, user)  # PO or SM (sprint planning is collaborative)
    story = backlog_service.get_story_or_404(db, project_id, story_id)
    return backlog_service.assign_to_sprint(db, story, payload)
