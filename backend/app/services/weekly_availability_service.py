"""
Weekly availability management service.

Handles recurring work schedule setup and retrieval.
"""
from datetime import datetime, time
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.weekly_availability import WeeklyAvailability, DayOfWeek
from app.services.audit_service import audit_log


def set_weekly_schedule(
    db: Session,
    *,
    user_id: int,
    schedule: dict[str, dict],
    timezone: str = "UTC",
) -> list[WeeklyAvailability]:
    """
    Set or update the weekly work schedule for a user.
    
    Args:
        db: Database session
        user_id: User ID
        schedule: Dict mapping day names to {"start_time": "HH:MM", "end_time": "HH:MM"}
                  or None for days off
        timezone: Timezone string (default: UTC)
    
    Returns:
        List of WeeklyAvailability records created/updated
    """
    now = datetime.utcnow()
    created_records = []
    if set(k.lower() for k in schedule) != {d.value for d in DayOfWeek}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Configure all 7 days of the week")

    # Map day names (case-insensitive)
    day_map = {day.value.lower(): day for day in DayOfWeek}

    for day_name, times in schedule.items():
        day_lower = day_name.lower()
        if day_lower not in day_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid day: {day_name}",
            )

        day_enum = day_map[day_lower]

        # Mark old records as expired
        old_records = (
            db.query(WeeklyAvailability)
            .filter(
                WeeklyAvailability.user_id == user_id,
                WeeklyAvailability.day_of_week == day_enum,
                WeeklyAvailability.effective_to == None,  # noqa: E712
            )
            .all()
        )
        for old_record in old_records:
            old_record.effective_to = now

        # Create new record
        start_time = None
        end_time = None

        if times and times.get("start_time") and times.get("end_time"):
            # Parse time strings "HH:MM"
            try:
                start_time = datetime.strptime(times["start_time"], "%H:%M").time()
                end_time = datetime.strptime(times["end_time"], "%H:%M").time()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid time format for {day_name}. Use HH:MM",
                )

        availability = WeeklyAvailability(
            user_id=user_id,
            day_of_week=day_enum,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            effective_from=now,
            effective_to=None,
        )
        db.add(availability)
        created_records.append(availability)

    db.commit()
    for record in created_records:
        db.refresh(record)

    # Audit log
    audit_log(
        db,
        user_id=user_id,
        action="weekly_schedule_configured",
        entity_type="weekly_availability",
        changes={"timezone": timezone, "days_configured": len(created_records)},
    )

    return created_records


def get_weekly_schedule(db: Session, *, user_id: int) -> list[WeeklyAvailability]:
    """Get the current weekly schedule for a user."""
    return (
        db.query(WeeklyAvailability)
        .filter(
            WeeklyAvailability.user_id == user_id,
            WeeklyAvailability.effective_to == None,  # noqa: E712
        )
        .order_by(WeeklyAvailability.day_of_week)
        .all()
    )


def is_weekly_schedule_configured(db: Session, *, user_id: int) -> bool:
    """Check if a user has configured their weekly schedule."""
    count = (
        db.query(WeeklyAvailability)
        .filter(
            WeeklyAvailability.user_id == user_id,
            WeeklyAvailability.effective_to == None,  # noqa: E712
        )
        .count()
    )
    return count >= 7  # All 7 days configured


def get_working_hours_for_day(
    db: Session, *, user_id: int, day_of_week: DayOfWeek
) -> tuple[time | None, time | None]:
    """
    Get working hours for a specific day.
    
    Returns:
        Tuple of (start_time, end_time) or (None, None) if day off
    """
    availability = (
        db.query(WeeklyAvailability)
        .filter(
            WeeklyAvailability.user_id == user_id,
            WeeklyAvailability.day_of_week == day_of_week,
            WeeklyAvailability.effective_to == None,  # noqa: E712
        )
        .first()
    )

    if availability:
        return availability.start_time, availability.end_time
    return None, None


def calculate_available_hours(
    db: Session, *, user_id: int, from_days: int = 7
) -> dict:
    """
    Calculate total available working hours for a user.
    
    Args:
        user_id: User ID
        from_days: Calculate for next N days (default: 7)
    
    Returns:
        Dict with total_hours, weekdays, weekends, etc.
    """
    from datetime import datetime as dt, timedelta

    schedule = get_weekly_schedule(db, user_id=user_id)
    
    # Calculate hours per week
    hours_per_week = 0
    for availability in schedule:
        if availability.start_time and availability.end_time:
            start = datetime.combine(dt.today(), availability.start_time)
            end = datetime.combine(dt.today(), availability.end_time)
            delta = end - start
            hours_per_week += delta.total_seconds() / 3600

    # Estimate for the given days
    weeks = max(1, from_days / 7)
    total_hours = hours_per_week * weeks

    # Subtract approved full-day leave from the requested capacity window.
    from app.models.leave import LeaveRequest, LeaveStatus, LeaveType
    from datetime import date, timedelta
    start_date = date.today()
    end_date = start_date + timedelta(days=max(0, from_days - 1))
    leave_days = 0
    for req in db.query(LeaveRequest).filter(
        LeaveRequest.user_id == user_id, LeaveRequest.status == LeaveStatus.APPROVED,
        LeaveRequest.type == LeaveType.LEAVE, LeaveRequest.start_date <= end_date, LeaveRequest.end_date >= start_date,
    ).all():
        overlap_start, overlap_end = max(start_date, req.start_date), min(end_date, req.end_date)
        leave_days += (overlap_end - overlap_start).days + 1
    daily_hours = hours_per_week / 5 if hours_per_week else 0
    leave_hours = min(total_hours, leave_days * daily_hours)
    total_hours = max(0, total_hours - leave_hours)

    return {
        "total_available_hours": round(total_hours, 2),
        "hours_per_week": round(hours_per_week, 2),
        "approved_leave_hours": round(leave_hours, 2),
        "estimated_for_days": from_days,
    }


def get_today_capacity(db: Session, *, user_id: int, when: datetime | None = None) -> dict:
    """Return working-day/leave-aware capacity for the user's local day."""
    from datetime import date, timedelta
    from zoneinfo import ZoneInfo
    from app.models.leave import LeaveRequest, LeaveStatus, LeaveType

    now_utc = when or datetime.utcnow()
    schedule = get_weekly_schedule(db, user_id=user_id)
    timezone = schedule[0].timezone if schedule else "UTC"
    try:
        local_now = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(timezone))
    except Exception:
        timezone = "UTC"
        local_now = now_utc
    local_date = local_now.date()
    day = DayOfWeek(list(DayOfWeek)[local_date.weekday()].value)
    hours = get_working_hours_for_day(db, user_id=user_id, day_of_week=day)
    leave = db.query(LeaveRequest).filter(
        LeaveRequest.user_id == user_id,
        LeaveRequest.status == LeaveStatus.APPROVED,
        LeaveRequest.type == LeaveType.LEAVE,
        LeaveRequest.start_date <= local_date,
        LeaveRequest.end_date >= local_date,
    ).first()
    working = bool(hours[0] and hours[1]) and leave is None
    return {
        "date": local_date.isoformat(), "timezone": timezone, "is_working_day": working,
        "on_leave": leave is not None,
        "start_time": hours[0].isoformat() if hours[0] else None,
        "end_time": hours[1].isoformat() if hours[1] else None,
    }


def get_today_capacity(db: Session, *, user_id: int, when: datetime | None = None) -> dict:
    """Return working-day/leave-aware capacity for the user's local day."""
    from datetime import date, timedelta
    from zoneinfo import ZoneInfo
    from app.models.leave import LeaveRequest, LeaveStatus, LeaveType

    now_utc = when or datetime.utcnow()
    schedule = get_weekly_schedule(db, user_id=user_id)
    timezone = schedule[0].timezone if schedule else "UTC"
    try:
        local_now = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(timezone))
    except Exception:
        timezone = "UTC"
        local_now = now_utc
    local_date = local_now.date()
    day = DayOfWeek(list(DayOfWeek)[local_date.weekday()].value)
    hours = get_working_hours_for_day(db, user_id=user_id, day_of_week=day)
    leave = db.query(LeaveRequest).filter(
        LeaveRequest.user_id == user_id,
        LeaveRequest.status == LeaveStatus.APPROVED,
        LeaveRequest.type == LeaveType.LEAVE,
        LeaveRequest.start_date <= local_date,
        LeaveRequest.end_date >= local_date,
    ).first()
    working = bool(hours[0] and hours[1]) and leave is None
    return {
        "date": local_date.isoformat(), "timezone": timezone, "is_working_day": working,
        "on_leave": leave is not None,
        "start_time": hours[0].isoformat() if hours[0] else None,
        "end_time": hours[1].isoformat() if hours[1] else None,
    }
