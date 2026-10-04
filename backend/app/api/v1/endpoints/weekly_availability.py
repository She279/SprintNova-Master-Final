"""
Weekly availability management endpoints.

Handles recurring work schedule setup and retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_and_user,get_db, require_role
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.weekly_availability import (
    WeeklyAvailabilityResponse,
    WeeklyScheduleSetup,
    FullWeeklyScheduleResponse,
)
from app.services.weekly_availability_service import (
    set_weekly_schedule,
    get_weekly_schedule,
    is_weekly_schedule_configured,
    calculate_available_hours, get_today_capacity,
)

router = APIRouter(prefix="/availability/weekly", tags=["Weekly Availability"])


@router.post("/setup")
def setup_weekly_schedule(
    schedule_setup: WeeklyScheduleSetup,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FullWeeklyScheduleResponse:
    """
    Set up or update the weekly work schedule.
    
    Expects a schedule with all 7 days of the week.
    Use null/None for start_time and end_time to mark a day as off.
    """
    try:
        records = set_weekly_schedule(
            db,
            user_id=user.id,
            schedule=schedule_setup.schedule,
            timezone=schedule_setup.timezone,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return FullWeeklyScheduleResponse(
        user_id=user.id,
        timezone=schedule_setup.timezone,
        schedule=[WeeklyAvailabilityResponse.model_validate(r) for r in records],
        is_configured=True,
    )


@router.get("/schedule")
def get_user_weekly_schedule(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FullWeeklyScheduleResponse:
    """Get the current weekly schedule for the authenticated user."""
    schedule = get_weekly_schedule(db, user_id=user.id)
    configured = is_weekly_schedule_configured(db, user_id=user.id)

    # Get timezone from first record
    timezone = schedule[0].timezone if schedule else "UTC"

    return FullWeeklyScheduleResponse(
        user_id=user.id,
        timezone=timezone,
        schedule=[WeeklyAvailabilityResponse.model_validate(s) for s in schedule],
        is_configured=configured,
    )


@router.get("/is-configured")
def check_availability_configured(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Check if user has configured their weekly schedule."""
    configured = is_weekly_schedule_configured(db, user_id=user.id)
    return {
        "is_configured": configured,
        "user_id": user.id,
    }


@router.get("/today")
def get_today_availability(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return get_today_capacity(db, user_id=user.id)


@router.get("/today")
def get_today_availability(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return get_today_capacity(db, user_id=user.id)


@router.get("/available-hours")
def get_available_hours(
    days: int = 7,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Calculate available working hours for the user."""
    hours_info = calculate_available_hours(db, user_id=user.id, from_days=days)
    return hours_info


@router.get("/{user_id}/schedule")
def get_team_member_availability(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get weekly schedule for a specific user.
    
    Admin/PM/Scrum Master can view team member availability.
    """
    # Permission check
    if current_user.id != user_id and current_user.role == RoleEnum.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other users' availability",
        )

    schedule = get_weekly_schedule(db, user_id=user_id)
    configured = is_weekly_schedule_configured(db, user_id=user_id)
    timezone = schedule[0].timezone if schedule else "UTC"

    return {
        "user_id": user_id,
        "timezone": timezone,
        "schedule": [WeeklyAvailabilityResponse.model_validate(s) for s in schedule],
        "is_configured": configured,
    }
