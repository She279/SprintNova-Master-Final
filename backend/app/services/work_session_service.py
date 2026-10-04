"""
Work session management service.

Handles:
- Creating work sessions on login
- Retrieving active sessions
- Stopping work sessions
- Calculating work duration
- Preventing duplicate active sessions
"""
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.work_session import WorkSession, WorkSessionStatus
from app.services.audit_service import audit_log
from app.services.realtime_service import hub


def start_work_session(db: Session, *, user_id: int) -> WorkSession:
    """
    Start a new work session for a user.
    
    Prevents multiple active sessions for the same user.
    """
    # Do not start sessions on approved leave/non-working days.
    from app.services.weekly_availability_service import get_today_capacity
    capacity = get_today_capacity(db, user_id=user_id)
    if not capacity["is_working_day"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Today is not a configured working day or is an approved leave day.")

    # Check if user already has an active session
    active_session = (
        db.query(WorkSession)
        .filter(
            WorkSession.user_id == user_id,
            WorkSession.status == WorkSessionStatus.ACTIVE,
            WorkSession.ended_at == None,  # noqa: E712
        )
        .first()
    )

    if active_session:
        # Return the existing active session instead of creating a new one
        return active_session

    # Create new session
    session = WorkSession(
        user_id=user_id,
        started_at=datetime.utcnow(),
        status=WorkSessionStatus.ACTIVE,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Audit log
    audit_log(db, user_id=user_id, action="work_session_started", entity_type="work_session", entity_id=session.id)
    hub.publish_nowait({"type": "work_session.started", "user_id": user_id, "session_id": session.id, "started_at": session.started_at.isoformat()}, user_ids={user_id})

    return session


def get_active_session(db: Session, *, user_id: int) -> WorkSession | None:
    """Get the currently active work session for a user."""
    return (
        db.query(WorkSession)
        .filter(
            WorkSession.user_id == user_id,
            WorkSession.status == WorkSessionStatus.ACTIVE,
            WorkSession.ended_at == None,  # noqa: E712
        )
        .first()
    )


def stop_work_session(db: Session, *, user_id: int, session_id: int | None = None) -> WorkSession:
    """
    Stop a work session.
    
    If session_id is provided, stop that specific session.
    Otherwise, stop the active session for the user.
    """
    if session_id:
        session = db.query(WorkSession).filter(
            WorkSession.id == session_id,
            WorkSession.user_id == user_id,
        ).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work session not found",
            )
    else:
        session = get_active_session(db, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active work session found",
            )

    # Calculate duration
    ended_at = datetime.utcnow()
    duration = int((ended_at - session.started_at).total_seconds() / 60)  # in minutes

    # Update session
    session.ended_at = ended_at
    session.total_work_minutes = duration
    session.status = WorkSessionStatus.COMPLETED
    db.commit()
    db.refresh(session)

    # Audit log
    audit_log(
        db,
        user_id=user_id,
        action="work_session_stopped",
        entity_type="work_session",
        entity_id=session.id,
    )
    hub.publish_nowait({"type": "work_session.stopped", "user_id": user_id, "session_id": session.id, "total_work_minutes": session.total_work_minutes}, user_ids={user_id})

    return session


def get_work_session_by_id(db: Session, *, session_id: int) -> WorkSession | None:
    """Get a work session by ID."""
    return db.query(WorkSession).filter(WorkSession.id == session_id).first()


def get_user_work_sessions(
    db: Session, *, user_id: int, limit: int = 50, skip: int = 0
) -> tuple[list[WorkSession], int]:
    """Get all work sessions for a user with pagination."""
    query = db.query(WorkSession).filter(WorkSession.user_id == user_id)
    total = query.count()
    sessions = query.order_by(WorkSession.started_at.desc()).offset(skip).limit(limit).all()
    return sessions, total


def get_user_work_time_today(db: Session, *, user_id: int) -> int:
    """
    Calculate total work minutes for a user today.
    
    Includes completed sessions and partially counts active session.
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    sessions = (
        db.query(WorkSession)
        .filter(
            WorkSession.user_id == user_id,
            WorkSession.started_at >= today_start,
            WorkSession.started_at < today_end,
        )
        .all()
    )

    total_minutes = 0
    for session in sessions:
        if session.total_work_minutes:
            total_minutes += session.total_work_minutes
        elif session.status == WorkSessionStatus.ACTIVE:
            # For active sessions, calculate elapsed time
            elapsed = int((datetime.utcnow() - session.started_at).total_seconds() / 60)
            total_minutes += elapsed

    return total_minutes


def get_users_currently_working(db: Session) -> list[tuple[int, str, str]]:
    """
    Get list of users currently working (have active work sessions).
    
    Returns list of (user_id, first_name, last_name) tuples.
    """
    from app.models.user import User

    result = (
        db.query(User.id, User.first_name, User.last_name)
        .join(WorkSession, User.id == WorkSession.user_id)
        .filter(
            WorkSession.status == WorkSessionStatus.ACTIVE,
            WorkSession.ended_at == None,  # noqa: E712
        )
        .distinct()
        .all()
    )
    return result
