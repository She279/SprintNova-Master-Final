from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.milestone import Milestone
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.models.notification import NotificationType
from app.models.project_enums import MilestoneStatus
from app.schemas.project import (
    MilestoneCreateRequest, MilestoneUpdateRequest, RoadmapPhase, RoadmapResponse,
    ProjectProgressResponse, ProgressPoint,
)
from app.services import notification_service
from app.services.realtime_service import hub

_UNPHASED = "Unphased"


def create_milestone(db: Session, project_id: int, payload: MilestoneCreateRequest) -> Milestone:
    milestone = Milestone(project_id=project_id, **payload.model_dump())
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


def list_milestones(db: Session, project_id: int) -> list[Milestone]:
    return (
        db.query(Milestone)
        .filter(Milestone.project_id == project_id)
        .order_by(Milestone.sort_order, Milestone.due_date.is_(None), Milestone.due_date)
        .all()
    )


def get_milestone_or_404(db: Session, project_id: int, milestone_id: int) -> Milestone:
    milestone = (
        db.query(Milestone)
        .filter(Milestone.id == milestone_id, Milestone.project_id == project_id)
        .first()
    )
    if not milestone:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Milestone not found")
    return milestone


def update_milestone(db: Session, milestone: Milestone, payload: MilestoneUpdateRequest) -> Milestone:
    changes = payload.model_dump(exclude_unset=True)
    status_changed = "status" in changes and changes["status"] != milestone.status

    for field, value in changes.items():
        setattr(milestone, field, value)
    db.commit()
    db.refresh(milestone)

    hub.publish_nowait({"type": "milestone.updated", "project_id": milestone.project_id, "milestone_id": milestone.id, "status": milestone.status.value}, project_id=milestone.project_id)

    if status_changed:
        project = db.get(Project, milestone.project_id)
        members = db.query(ProjectMember).filter(ProjectMember.project_id == milestone.project_id).all()
        recipients = [db.get(User, m.user_id) for m in members]
        notification_service.notify_many(
            db, users=[u for u in recipients if u],
            type=NotificationType.MILESTONE_STATUS_CHANGED,
            title=f"Milestone \"{milestone.title}\" is now {milestone.status.value.replace('_', ' ')}",
            body=f"In {project.code if project else 'project'}, milestone \"{milestone.title}\" changed to {milestone.status.value.replace('_', ' ')}.",
            related_project_id=milestone.project_id,
        )

    return milestone


def get_roadmap(db: Session, project_id: int) -> RoadmapResponse:
    """Groups milestones into their `phase` for a roadmap/timeline view --
    the same underlying data as the plain milestone list, presented as
    ordered stages (spec: "track ... project roadmaps")."""
    milestones = list_milestones(db, project_id)

    grouped: dict[str, list[Milestone]] = {}
    for m in milestones:
        grouped.setdefault(m.phase or _UNPHASED, []).append(m)

    phases = [RoadmapPhase(phase=phase_name, milestones=items) for phase_name, items in grouped.items()]
    return RoadmapResponse(project_id=project_id, phases=phases)


def get_progress(db: Session, project_id: int) -> ProjectProgressResponse:
    """Milestone-completion progress -- see ProjectProgressResponse
    docstring for why this stands in for a sprint burndown chart until
    Module 3 (Scrum/Sprints) exists."""
    milestones = list_milestones(db, project_id)
    total = len(milestones)
    completed = [m for m in milestones if m.status == MilestoneStatus.COMPLETED]
    missed = [m for m in milestones if m.status == MilestoneStatus.MISSED]

    # Build a cumulative-completed-over-time series from each completed
    # milestone's last-updated date (the closest real signal we have to a
    # completion timestamp).
    completed_sorted = sorted(completed, key=lambda m: m.updated_at)
    timeline = []
    running = 0
    for m in completed_sorted:
        running += 1
        timeline.append(ProgressPoint(date=m.updated_at.date(), cumulative_completed=running))

    return ProjectProgressResponse(
        project_id=project_id,
        total_milestones=total,
        completed_milestones=len(completed),
        missed_milestones=len(missed),
        percent_complete=round((len(completed) / total) * 100, 1) if total else 0.0,
        timeline=timeline,
    )
