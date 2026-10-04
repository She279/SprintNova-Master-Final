from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.leave import LeaveRequest, LeaveStatus
from app.models.user import User
from app.models.availability import Availability, AvailabilityStatus
from app.models.notification import NotificationType
from app.models.role import RoleEnum
from app.schemas.leave import LeaveRequestCreateRequest, LeaveDecisionRequest
from app.services import notification_service
from app.services.audit_service import audit_log


def create_request(db: Session, user: User, payload: LeaveRequestCreateRequest) -> LeaveRequest:
    request = LeaveRequest(user_id=user.id, **payload.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)

    # Notify every Admin so someone acts on it.
    admins = db.query(User).filter(User.role == RoleEnum.OWNER_ADMIN, User.is_active == True).all()  # noqa: E712
    notification_service.notify_many(
        db, users=admins, type=NotificationType.LEAVE_REQUEST_SUBMITTED,
        title=f"{user.first_name} {user.last_name} requested {request.type.value}",
        body=f"{request.type.value.title()} from {request.start_date} to {request.end_date}.",
        also_email=False,
    )
    return request


def list_own(db: Session, user_id: int) -> list[LeaveRequest]:
    return db.query(LeaveRequest).filter(LeaveRequest.user_id == user_id).order_by(LeaveRequest.created_at.desc()).all()


def list_all(db: Session, status_filter: LeaveStatus | None = None) -> list[LeaveRequest]:
    query = db.query(LeaveRequest)
    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)
    return query.order_by(LeaveRequest.created_at.desc()).all()


def get_or_404(db: Session, request_id: int) -> LeaveRequest:
    request = db.get(LeaveRequest, request_id)
    if not request:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Leave request not found")
    return request


def decide(db: Session, request: LeaveRequest, reviewer: User, payload: LeaveDecisionRequest) -> LeaveRequest:
    if request.status != LeaveStatus.PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "This request has already been reviewed")

    request.status = LeaveStatus.APPROVED if payload.approve else LeaveStatus.REJECTED
    request.reviewed_by_id = reviewer.id
    request.reviewed_at = datetime.utcnow()
    request.review_note = payload.review_note
    db.commit()
    db.refresh(request)

    # An approved LEAVE blocks the employee's availability for that range.
    if payload.approve and request.type.value == "leave":
        d = request.start_date
        while d <= request.end_date:
            existing = db.query(Availability).filter(
                Availability.user_id == request.user_id, Availability.date == d
            ).first()
            if existing:
                existing.status = AvailabilityStatus.UNAVAILABLE
                existing.note = "On approved leave"
            else:
                db.add(Availability(
                    user_id=request.user_id, date=d, status=AvailabilityStatus.UNAVAILABLE,
                    note="On approved leave",
                ))
            d += timedelta(days=1)
        db.commit()

    audit_log(db, user_id=reviewer.id, action="leave_approved" if payload.approve else "leave_rejected", entity_type="leave_request", entity_id=request.id, changes={"status": request.status.value})

    employee = db.get(User, request.user_id)
    if employee:
        notification_service.notify(
            db, user=employee, type=NotificationType.LEAVE_REQUEST_DECIDED,
            title=f"Your {request.type.value} request was {request.status.value}",
            body=(payload.review_note or f"Your {request.type.value} request from {request.start_date} "
                  f"to {request.end_date} was {request.status.value}."),
        )

    return request
