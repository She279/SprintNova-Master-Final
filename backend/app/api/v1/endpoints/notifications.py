from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.api.deps import require_password_already_set
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = False, db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    return notification_service.list_for_user(db, user.id, unread_only=unread_only)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(notification_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    record = notification_service.mark_read(db, user.id, notification_id)
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    return record


@router.post("/mark-all-read", status_code=204)
def mark_all_read(db=Depends(get_db), user: User = Depends(require_password_already_set)):
    notification_service.mark_all_read(db, user.id)
