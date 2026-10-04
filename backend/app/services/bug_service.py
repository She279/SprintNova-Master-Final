from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.bug import Bug
from app.models.bug_comment import BugComment
from app.models.bug_history import BugHistory
from app.models.testing_enums import BugStatus
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.bug import BugCreateRequest, BugUpdateRequest, BugCommentCreateRequest
from app.services import notification_service
from app.services.realtime_service import hub

_TRACKED_FIELDS = {"status", "assignee_id", "severity", "priority"}
_RESOLVED_STATUSES = {BugStatus.VERIFIED, BugStatus.CLOSED}


def _next_key(db: Session, project: Project) -> str:
    count = db.query(Bug).filter(Bug.project_id == project.id).count()
    return f"{project.code}-BUG{count + 1}"


def _stringify(value):
    if value is None:
        return None
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def create_bug(db: Session, project: Project, payload: BugCreateRequest, reporter: User) -> Bug:
    bug = Bug(project_id=project.id, key=_next_key(db, project), reporter_id=reporter.id, **payload.model_dump())
    db.add(bug)
    db.commit()
    db.refresh(bug)

    if bug.assignee_id:
        _notify_assignment(db, bug, project)
    hub.publish_nowait({"type": "bug.created", "project_id": project.id, "bug_id": bug.id, "key": bug.key, "status": bug.status.value}, project_id=project.id)

    return bug


def list_bugs(
    db: Session, project_id: int, status_filter: BugStatus | None = None,
    severity_filter=None, assignee_id: int | None = None,
) -> list[Bug]:
    query = db.query(Bug).filter(Bug.project_id == project_id)
    if status_filter:
        query = query.filter(Bug.status == status_filter)
    if severity_filter:
        query = query.filter(Bug.severity == severity_filter)
    if assignee_id is not None:
        query = query.filter(Bug.assignee_id == assignee_id)
    return query.order_by(Bug.created_at.desc()).all()


def get_bug_or_404(db: Session, project_id: int, bug_id: int) -> Bug:
    bug = db.query(Bug).filter(Bug.id == bug_id, Bug.project_id == project_id).first()
    if not bug:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bug not found")
    return bug


def update_bug(db: Session, bug: Bug, payload: BugUpdateRequest, changed_by: User) -> Bug:
    changes = payload.model_dump(exclude_unset=True)

    for field, new_value in changes.items():
        old_value = getattr(bug, field)
        if field in _TRACKED_FIELDS and old_value != new_value:
            db.add(BugHistory(
                bug_id=bug.id, user_id=changed_by.id, field_changed=field,
                old_value=_stringify(old_value), new_value=_stringify(new_value),
            ))
        setattr(bug, field, new_value)

    if "status" in changes:
        bug.resolved_at = datetime.utcnow() if bug.status in _RESOLVED_STATUSES else None

    db.commit()
    db.refresh(bug)

    project = db.get(Project, bug.project_id)

    if "assignee_id" in changes and bug.assignee_id:
        _notify_assignment(db, bug, project)

    if "status" in changes:
        recipients = {bug.assignee_id, bug.reporter_id} - {None, changed_by.id}
        for uid in recipients:
            user = db.get(User, uid)
            if user:
                notification_service.notify(
                    db, user=user, type=NotificationType.BUG_STATUS_CHANGED,
                    title=f"{bug.key} is now {bug.status.value.replace('_', ' ')}",
                    body=f"\"{bug.title}\" in {project.code if project else ''} is now {bug.status.value.replace('_', ' ')}.",
                    related_project_id=bug.project_id, also_email=False,
                )

    hub.publish_nowait({"type": "bug.updated", "project_id": bug.project_id, "bug_id": bug.id, "key": bug.key, "status": bug.status.value}, project_id=bug.project_id)
    return bug


def _notify_assignment(db: Session, bug: Bug, project: Project) -> None:
    assignee = db.get(User, bug.assignee_id)
    if assignee:
        notification_service.notify(
            db, user=assignee, type=NotificationType.BUG_ASSIGNED,
            title=f"You've been assigned {bug.key}",
            body=f"\"{bug.title}\" ({bug.severity.value} severity) in {project.code} — {project.name} is now assigned to you.",
            related_project_id=project.id,
        )


def add_comment(db: Session, bug: Bug, payload: BugCommentCreateRequest, author: User) -> BugComment:
    comment = BugComment(bug_id=bug.id, author_id=author.id, body=payload.body)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    recipients = {bug.assignee_id, bug.reporter_id} - {None, author.id}
    for uid in recipients:
        user = db.get(User, uid)
        if user:
            notification_service.notify(
                db, user=user, type=NotificationType.BUG_COMMENT_ADDED,
                title=f"New comment on {bug.key}",
                body=f"{author.first_name} {author.last_name} commented on \"{bug.title}\".",
                related_project_id=bug.project_id, also_email=False,
            )

    hub.publish_nowait({"type": "bug.comment.created", "project_id": bug.project_id, "bug_id": bug.id, "comment_id": comment.id}, project_id=bug.project_id)
    return comment


def list_comments(db: Session, bug_id: int) -> list[BugComment]:
    return db.query(BugComment).filter(BugComment.bug_id == bug_id).order_by(BugComment.created_at).all()


def list_history(db: Session, bug_id: int) -> list[BugHistory]:
    return db.query(BugHistory).filter(BugHistory.bug_id == bug_id).order_by(BugHistory.created_at.desc()).all()
