"""
Single place every Module 2 event routes through to notify a user, both
in-app (Notification row) and by email (via the shared email_service).
Future modules (Sprints, Kanban, Bugs) should call `notify` the same way
rather than sending email or writing Notification rows directly.
"""
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.services.email_service import email_service
from app.services.realtime_service import hub


def notify(
    db: Session, *, user: User, type: NotificationType, title: str, body: str | None = None,
    related_project_id: int | None = None, also_email: bool = True,
) -> Notification:
    record = Notification(
        user_id=user.id, type=type, title=title, body=body, related_project_id=related_project_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    if also_email:
        email_service.send_project_notification_email(
            personal_email=user.personal_email, subject=f"SprintNova – {title}",
            body=body or title,
        )

    hub.publish_nowait(
        {
            "type": "notification.created",
            "notification": {
                "id": record.id,
                "user_id": user.id,
                "type": record.type.value,
                "title": record.title,
                "body": record.body,
                "related_project_id": record.related_project_id,
                "is_read": record.is_read,
                "created_at": record.created_at.isoformat(),
            },
        },
        user_ids={user.id},
        project_id=related_project_id,
    )
    return record


def notify_many(db: Session, *, users: list[User], **kwargs) -> None:
    for user in users:
        notify(db, user=user, **kwargs)


def list_for_user(db: Session, user_id: int, unread_only: bool = False) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)  # noqa: E712
    return query.order_by(Notification.created_at.desc()).all()


def mark_read(db: Session, user_id: int, notification_id: int) -> Notification | None:
    record = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if record:
        record.is_read = True
        db.commit()
        db.refresh(record)
    return record


def mark_all_read(db: Session, user_id: int) -> None:
    db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).update(  # noqa: E712
        {"is_read": True}
    )
    db.commit()
