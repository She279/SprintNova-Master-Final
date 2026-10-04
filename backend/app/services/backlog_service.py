from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user_story import UserStory
from app.models.scrum_enums import StoryStatus
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.user_story import (
    UserStoryCreateRequest, UserStoryUpdateRequest, BacklogReorderRequest, AssignToSprintRequest,
)
from app.services import notification_service
from app.services.realtime_service import hub


def _next_key(db: Session, project: Project) -> str:
    count = db.query(UserStory).filter(UserStory.project_id == project.id).count()
    return f"{project.code}-{count + 1}"


def create_story(db: Session, project: Project, payload: UserStoryCreateRequest, reporter: User) -> UserStory:
    max_rank = db.query(UserStory).filter(UserStory.project_id == project.id).count()
    story = UserStory(
        project_id=project.id,
        key=_next_key(db, project),
        reporter_id=reporter.id,
        backlog_rank=max_rank,
        **payload.model_dump(),
    )
    db.add(story)
    db.commit()
    db.refresh(story)

    if story.assignee_id:
        _notify_assignment(db, story, project)
    hub.publish_nowait({"type": "story.created", "project_id": project.id, "story_id": story.id, "key": story.key}, project_id=project.id)

    return story


def list_backlog(db: Session, project_id: int, sprint_id: int | None = None, status_filter: StoryStatus | None = None) -> list[UserStory]:
    query = db.query(UserStory).filter(UserStory.project_id == project_id)
    if sprint_id is not None:
        query = query.filter(UserStory.sprint_id == sprint_id)
    if status_filter:
        query = query.filter(UserStory.status == status_filter)
    return query.order_by(UserStory.backlog_rank).all()


def get_story_or_404(db: Session, project_id: int, story_id: int) -> UserStory:
    story = db.query(UserStory).filter(UserStory.id == story_id, UserStory.project_id == project_id).first()
    if not story:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User story not found")
    return story


def update_story(db: Session, story: UserStory, payload: UserStoryUpdateRequest) -> UserStory:
    changes = payload.model_dump(exclude_unset=True)
    assignee_changed = "assignee_id" in changes and changes["assignee_id"] != story.assignee_id

    for field, value in changes.items():
        setattr(story, field, value)
    db.commit()
    db.refresh(story)

    if assignee_changed and story.assignee_id:
        project = db.get(Project, story.project_id)
        _notify_assignment(db, story, project)
    hub.publish_nowait({"type": "story.updated", "project_id": story.project_id, "story_id": story.id, "key": story.key, "status": story.status.value}, project_id=story.project_id)

    return story


def _notify_assignment(db: Session, story: UserStory, project: Project) -> None:
    assignee = db.get(User, story.assignee_id)
    if assignee:
        notification_service.notify(
            db, user=assignee, type=NotificationType.STORY_ASSIGNED,
            title=f"You've been assigned {story.key}",
            body=f"\"{story.title}\" in {project.code} — {project.name} is now assigned to you.",
            related_project_id=project.id,
        )


def reorder_backlog(db: Session, project_id: int, payload: BacklogReorderRequest) -> list[UserStory]:
    stories = {s.id: s for s in db.query(UserStory).filter(UserStory.project_id == project_id).all()}
    for rank, story_id in enumerate(payload.story_ids_in_order):
        if story_id in stories:
            stories[story_id].backlog_rank = rank
    db.commit()
    hub.publish_nowait({"type": "backlog.reordered", "project_id": project_id}, project_id=project_id)
    return list_backlog(db, project_id)


def assign_to_sprint(db: Session, story: UserStory, payload: AssignToSprintRequest) -> UserStory:
    story.sprint_id = payload.sprint_id
    if payload.sprint_id is not None and story.status == StoryStatus.BACKLOG:
        story.status = StoryStatus.IN_SPRINT
    elif payload.sprint_id is None and story.status == StoryStatus.IN_SPRINT:
        story.status = StoryStatus.BACKLOG
    db.commit()
    db.refresh(story)
    hub.publish_nowait({"type": "story.sprint_changed", "project_id": story.project_id, "story_id": story.id, "sprint_id": story.sprint_id}, project_id=story.project_id)
    return story


def delete_story(db: Session, story: UserStory) -> None:
    db.delete(story)
    db.commit()
