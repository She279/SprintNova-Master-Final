from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.sprint import Sprint
from app.models.user_story import UserStory
from app.models.scrum_enums import SprintStatus, StoryStatus
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.sprint import (
    SprintCreateRequest, SprintUpdateRequest, SprintDetailResponse,
    BurndownResponse, BurndownPoint, VelocityResponse, VelocityEntry,
)
from app.schemas.user_story import UserStoryBrief
from app.services import notification_service
from app.services.realtime_service import hub


def create_sprint(db: Session, project: Project, payload: SprintCreateRequest, created_by: User) -> Sprint:
    if payload.end_date < payload.start_date:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "end_date cannot be before start_date")
    sprint = Sprint(project_id=project.id, created_by_id=created_by.id, **payload.model_dump())
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    hub.publish_nowait({"type": "sprint.created", "project_id": project.id, "sprint_id": sprint.id, "status": sprint.status.value, "name": sprint.name}, project_id=project.id)
    return sprint


def list_sprints(db: Session, project_id: int) -> list[Sprint]:
    return db.query(Sprint).filter(Sprint.project_id == project_id).order_by(Sprint.start_date.desc()).all()


def get_sprint_or_404(db: Session, project_id: int, sprint_id: int) -> Sprint:
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project_id).first()
    if not sprint:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sprint not found")
    return sprint


def update_sprint(db: Session, sprint: Sprint, payload: SprintUpdateRequest) -> Sprint:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sprint, field, value)
    db.commit()
    db.refresh(sprint)
    hub.publish_nowait({"type": "sprint.updated", "project_id": sprint.project_id, "sprint_id": sprint.id, "status": sprint.status.value, "name": sprint.name}, project_id=sprint.project_id)
    return sprint


def _team_members(db: Session, project_id: int) -> list[User]:
    member_ids = [m.user_id for m in db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()]
    return [u for u in (db.get(User, uid) for uid in member_ids) if u]


def start_sprint(db: Session, sprint: Sprint) -> Sprint:
    if sprint.status != SprintStatus.PLANNED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only a planned sprint can be started")
    if db.query(Sprint).filter(Sprint.project_id == sprint.project_id, Sprint.status == SprintStatus.ACTIVE).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "This project already has an active sprint")

    sprint.status = SprintStatus.ACTIVE
    db.commit()
    db.refresh(sprint)

    project = db.get(Project, sprint.project_id)
    hub.publish_nowait({"type": "sprint.started", "project_id": sprint.project_id, "sprint_id": sprint.id, "status": sprint.status.value, "name": sprint.name}, project_id=sprint.project_id)
    notification_service.notify_many(
        db, users=_team_members(db, sprint.project_id), type=NotificationType.SPRINT_STARTED,
        title=f"Sprint \"{sprint.name}\" has started",
        body=(sprint.goal or f"Sprint {sprint.name} for {project.code} is now active.") if project else sprint.name,
        related_project_id=sprint.project_id, also_email=False,
    )
    return sprint


def close_sprint(db: Session, sprint: Sprint) -> Sprint:
    if sprint.status != SprintStatus.ACTIVE:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only an active sprint can be closed")

    sprint.status = SprintStatus.COMPLETED
    db.commit()
    db.refresh(sprint)

    # Anything not Done gets pushed back to the backlog, mirroring real Scrum practice.
    unfinished = (
        db.query(UserStory)
        .filter(UserStory.sprint_id == sprint.id, UserStory.status != StoryStatus.DONE)
        .all()
    )
    for story in unfinished:
        story.sprint_id = None
        story.status = StoryStatus.BACKLOG
    db.commit()

    project = db.get(Project, sprint.project_id)
    completed_points = sum(
        s.story_points or 0
        for s in db.query(UserStory).filter(UserStory.sprint_id == sprint.id, UserStory.status == StoryStatus.DONE).all()
    )
    hub.publish_nowait({"type": "sprint.completed", "project_id": sprint.project_id, "sprint_id": sprint.id, "status": sprint.status.value, "name": sprint.name}, project_id=sprint.project_id)
    notification_service.notify_many(
        db, users=_team_members(db, sprint.project_id), type=NotificationType.SPRINT_COMPLETED,
        title=f"Sprint \"{sprint.name}\" completed",
        body=f"Completed {completed_points} story points. {len(unfinished)} unfinished item(s) returned to the backlog.",
        related_project_id=sprint.project_id, also_email=False,
    )
    return sprint


def cancel_sprint(db: Session, sprint: Sprint) -> Sprint:
    if sprint.status not in (SprintStatus.PLANNED, SprintStatus.ACTIVE):
        raise HTTPException(status.HTTP_409_CONFLICT, "Only a planned or active sprint can be cancelled")
    sprint.status = SprintStatus.CANCELLED
    db.commit()
    db.refresh(sprint)

    stories = db.query(UserStory).filter(UserStory.sprint_id == sprint.id).all()
    for story in stories:
        story.sprint_id = None
        if story.status == StoryStatus.IN_SPRINT:
            story.status = StoryStatus.BACKLOG
    db.commit()
    return sprint


def get_sprint_detail(db: Session, sprint: Sprint) -> SprintDetailResponse:
    stories = db.query(UserStory).filter(UserStory.sprint_id == sprint.id).all()
    total_points = sum(s.story_points or 0 for s in stories)
    completed_points = sum(s.story_points or 0 for s in stories if s.status == StoryStatus.DONE)
    return SprintDetailResponse(
        **{c: getattr(sprint, c) for c in ["id", "project_id", "name", "goal", "start_date", "end_date", "status", "created_by_id", "created_at"]},
        stories=[UserStoryBrief.model_validate(s) for s in stories],
        total_points=total_points,
        completed_points=completed_points,
    )


def get_burndown(db: Session, sprint: Sprint) -> BurndownResponse:
    stories = db.query(UserStory).filter(UserStory.sprint_id == sprint.id).all()
    total_points = sum(s.story_points or 0 for s in stories)

    total_days = (sprint.end_date - sprint.start_date).days
    today = date.today()

    points = []
    d = sprint.start_date
    day_index = 0
    while d <= sprint.end_date:
        ideal_remaining = total_points if total_days == 0 else total_points * (1 - day_index / total_days)

        # Actual remaining as of end-of-day `d`: total minus everything Done
        # by then (using updated_at as the completion signal, same approach
        # as Module 2's milestone progress).
        if sprint.status == SprintStatus.PLANNED or d > today:
            actual_remaining = None
        else:
            done_by_then = sum(
                s.story_points or 0 for s in stories
                if s.status == StoryStatus.DONE and s.updated_at.date() <= d
            )
            actual_remaining = total_points - done_by_then

        points.append(BurndownPoint(date=d, ideal_remaining=round(ideal_remaining, 1), actual_remaining=actual_remaining))
        d += timedelta(days=1)
        day_index += 1

    return BurndownResponse(sprint_id=sprint.id, total_points=total_points, points=points)


def get_velocity(db: Session, project_id: int, last_n: int = 6) -> VelocityResponse:
    completed_sprints = (
        db.query(Sprint)
        .filter(Sprint.project_id == project_id, Sprint.status == SprintStatus.COMPLETED)
        .order_by(Sprint.end_date.desc())
        .limit(last_n)
        .all()
    )

    entries = []
    for sprint in reversed(completed_sprints):
        completed_points = sum(
            s.story_points or 0
            for s in db.query(UserStory).filter(UserStory.sprint_id == sprint.id, UserStory.status == StoryStatus.DONE).all()
        )
        entries.append(VelocityEntry(sprint_id=sprint.id, sprint_name=sprint.name, completed_points=completed_points))

    average = round(sum(e.completed_points for e in entries) / len(entries), 1) if entries else 0.0
    return VelocityResponse(project_id=project_id, sprints=entries, average_velocity=average)
