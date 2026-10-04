"""
Work session management endpoints.

Handles work session lifecycle: start, stop, retrieve active.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.work_session import WorkSessionResponse, WorkSessionDetailResponse
from app.services.work_session_service import (
    start_work_session,
    stop_work_session,
    get_active_session,
    get_work_session_by_id,
    get_user_work_sessions,
    get_user_work_time_today,
    get_users_currently_working,
)

router = APIRouter(prefix="/work-sessions", tags=["Work Sessions"])


@router.post("/start")
def start_session(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WorkSessionResponse:
    """
    Start a work session for the authenticated user.
    
    Returns existing active session if one exists, otherwise creates new one.
    """
    session = start_work_session(db, user_id=user.id)
    return WorkSessionResponse.model_validate(session)


@router.get("/current")
def get_current_session(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WorkSessionDetailResponse | None:
    """Get the currently active work session for the authenticated user."""
    session = get_active_session(db, user_id=user.id)
    if not session:
        return None

    # Compute elapsed time for active session
    from datetime import datetime
    elapsed = int((datetime.utcnow() - session.started_at).total_seconds() / 60)

    response = WorkSessionDetailResponse.model_validate(session)
    response.elapsed_minutes = elapsed
    return response


@router.post("/{session_id}/stop")
def stop_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WorkSessionResponse:
    """Stop a work session."""
    session = stop_work_session(db, user_id=user.id, session_id=session_id)
    return WorkSessionResponse.model_validate(session)


@router.get("/today-total")
def get_today_total_minutes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Get total work minutes for today."""
    total_minutes = get_user_work_time_today(db, user_id=user.id)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return {
        "total_minutes": total_minutes,
        "formatted": f"{hours:02d}:{minutes:02d}",
        "hours": hours,
        "minutes": minutes,
    }


@router.get("/history")
def get_sessions_history(
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Get work session history for the authenticated user."""
    sessions, total = get_user_work_sessions(db, user_id=user.id, limit=limit, skip=skip)
    return {
        "sessions": [WorkSessionResponse.model_validate(s) for s in sessions],
        "total": total,
        "limit": limit,
        "skip": skip,
    }


@router.get("/currently-working")
def get_currently_working_users(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """
    Get list of employees currently working.
    
    Visible to admin/scrum master for team coordination.
    """
    from app.models.role import RoleEnum

    # Check permission
    if user.role not in [RoleEnum.OWNER_ADMIN, RoleEnum.SCRUM_MASTER, RoleEnum.PROJECT_MANAGER, RoleEnum.TEAM_LEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and scrum masters can view this",
        )

    users_working = get_users_currently_working(db)
    return {
        "count": len(users_working),
        "users": [
            {"user_id": uid, "full_name": f"{fname} {lname}"}
            for uid, fname, lname in users_working
        ],
    }
