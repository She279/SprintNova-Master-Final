"""
Daily work update management service.

Handles creation, retrieval, and updates to daily work summaries.
"""
from datetime import datetime, date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.daily_work_update import DailyWorkUpdate
from app.models.daily_work_update_analysis import DailyWorkUpdateAnalysis
from app.services.audit_service import audit_log
from app.services.realtime_service import hub


def create_daily_work_update(
    db: Session,
    *,
    user_id: int,
    work_done: str | None = None,
    completed_work: str | None = None,
    pending_work: str | None = None,
    blockers: str | None = None,
    additional_notes: str | None = None,
    progress_percentage: int | None = None,
    project_id: int | None = None,
    date_: date | None = None,
) -> DailyWorkUpdate:
    """
    Create a new daily work update.
    
    Prevents duplicate updates for the same user and date.
    """
    if date_ is None:
        date_ = date.today()

    from app.services.weekly_availability_service import is_weekly_schedule_configured, get_today_capacity
    from app.models.user import User
    from app.models.role import RoleEnum
    if not is_weekly_schedule_configured(db, user_id=user_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Configure your working availability before submitting a daily work update")
    if date_ is None:
        date_ = date.today()
    today_capacity = get_today_capacity(db, user_id=user_id)
    if date_ == date.today() and not today_capacity["is_working_day"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Today is not a configured working day or is an approved leave day")

    if project_id is not None:
        from app.models.project import Project
        from app.services.project_service import require_view_access, get_project_or_404
        project = get_project_or_404(db, project_id)
        require_view_access(db, project, db.get(User, user_id))

    # Client accounts are status-only and cannot submit internal updates.
    if db.get(User, user_id) and db.get(User, user_id).role == RoleEnum.CLIENT:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Client accounts cannot submit internal daily work updates")

    # Check for existing update for this date
    existing = (
        db.query(DailyWorkUpdate)
        .filter(
            DailyWorkUpdate.user_id == user_id,
            DailyWorkUpdate.date == date_,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Daily work update for {date_} already exists. Use PUT to update it.",
        )

    # Create new update
    update = DailyWorkUpdate(
        user_id=user_id,
        project_id=project_id,
        date=date_,
        work_done=work_done,
        completed_work=completed_work,
        pending_work=pending_work,
        blockers=blockers,
        additional_notes=additional_notes,
        progress_percentage=min(100, max(0, progress_percentage)) if progress_percentage else None,
        submitted_at=datetime.utcnow(),
    )

    db.add(update)
    db.commit()
    db.refresh(update)

    # Audit log
    audit_log(
        db,
        user_id=user_id,
        action="daily_work_update_submitted",
        entity_type="daily_work_update",
        entity_id=update.id,
    )
    hub.publish_nowait({"type": "daily_update.submitted", "user_id": user_id, "project_id": project_id, "update_id": update.id, "date": update.date.isoformat()}, user_ids={user_id}, project_id=project_id)

    return update


def get_daily_work_update(
    db: Session, *, update_id: int, user_id: int | None = None
) -> DailyWorkUpdate | None:
    """Get a specific daily work update."""
    query = db.query(DailyWorkUpdate).filter(DailyWorkUpdate.id == update_id)
    if user_id is not None:
        query = query.filter(DailyWorkUpdate.user_id == user_id)
    return query.first()


def get_user_daily_update(
    db: Session, *, user_id: int, date_: date | None = None
) -> DailyWorkUpdate | None:
    """Get the daily update for a user on a specific date (or today)."""
    if date_ is None:
        date_ = date.today()

    return (
        db.query(DailyWorkUpdate)
        .filter(
            DailyWorkUpdate.user_id == user_id,
            DailyWorkUpdate.date == date_,
        )
        .first()
    )


def update_daily_work_update(
    db: Session,
    *,
    update_id: int,
    user_id: int,
    work_done: str | None = None,
    completed_work: str | None = None,
    pending_work: str | None = None,
    blockers: str | None = None,
    additional_notes: str | None = None,
    progress_percentage: int | None = None,
) -> DailyWorkUpdate:
    """Update an existing daily work update."""
    update = get_daily_work_update(db, update_id=update_id, user_id=user_id)
    if not update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily work update not found",
        )

    # Track changes for audit
    changes = {}
    if work_done is not None and work_done != update.work_done:
        changes["work_done"] = {"old": update.work_done, "new": work_done}
        update.work_done = work_done
    if completed_work is not None and completed_work != update.completed_work:
        changes["completed_work"] = {"old": update.completed_work, "new": completed_work}
        update.completed_work = completed_work
    if pending_work is not None and pending_work != update.pending_work:
        changes["pending_work"] = {"old": update.pending_work, "new": pending_work}
        update.pending_work = pending_work
    if blockers is not None and blockers != update.blockers:
        changes["blockers"] = {"old": update.blockers, "new": blockers}
        update.blockers = blockers
    if additional_notes is not None and additional_notes != update.additional_notes:
        changes["additional_notes"] = {"old": update.additional_notes, "new": additional_notes}
        update.additional_notes = additional_notes
    if progress_percentage is not None:
        safe_progress = min(100, max(0, progress_percentage))
        if safe_progress != update.progress_percentage:
            changes["progress_percentage"] = {"old": update.progress_percentage, "new": safe_progress}
            update.progress_percentage = safe_progress

    update.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(update)

    # Audit log only if changes were made
    if changes:
        audit_log(
            db,
            user_id=user_id,
            action="daily_work_update_updated",
            entity_type="daily_work_update",
            entity_id=update.id,
            changes=changes,
        )
        hub.publish_nowait({"type": "daily_update.updated", "user_id": user_id, "project_id": update.project_id, "update_id": update.id}, user_ids={user_id}, project_id=update.project_id)

    return update


def get_user_daily_updates(
    db: Session,
    *,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 30,
    skip: int = 0,
) -> tuple[list[DailyWorkUpdate], int]:
    """
    Get daily updates for a user with optional date range.
    
    Returns:
        Tuple of (updates, total_count)
    """
    query = db.query(DailyWorkUpdate).filter(DailyWorkUpdate.user_id == user_id)

    if start_date:
        query = query.filter(DailyWorkUpdate.date >= start_date)
    if end_date:
        query = query.filter(DailyWorkUpdate.date <= end_date)

    total = query.count()
    updates = query.order_by(DailyWorkUpdate.date.desc()).offset(skip).limit(limit).all()

    return updates, total


def get_team_daily_updates(
    db: Session,
    *,
    team_member_ids: list[int],
    date_: date | None = None,
) -> dict[int, DailyWorkUpdate | None]:
    """
    Get daily updates for multiple team members on a specific date.
    
    Returns:
        Dict mapping user_id to DailyWorkUpdate (or None if no update)
    """
    if date_ is None:
        date_ = date.today()

    updates = (
        db.query(DailyWorkUpdate)
        .filter(
            DailyWorkUpdate.user_id.in_(team_member_ids),
            DailyWorkUpdate.date == date_,
        )
        .all()
    )

    result = {user_id: None for user_id in team_member_ids}
    for update in updates:
        result[update.user_id] = update

    return result


def check_pending_daily_updates(db: Session, *, user_id: int, date_: date | None = None) -> bool:
    """
    Check if a user has a pending (unsubmitted) daily update.
    
    Returns:
        True if update is pending, False if already submitted or not on working day
    """
    if date_ is None:
        date_ = date.today()

    from app.services.weekly_availability_service import get_today_capacity
    if not get_today_capacity(db, user_id=user_id)["is_working_day"]:
        return False

    # Check if user has submitted an update for today
    submitted = (
        db.query(DailyWorkUpdate)
        .filter(
            DailyWorkUpdate.user_id == user_id,
            DailyWorkUpdate.date == date_,
        )
        .first()
    )

    return submitted is None


def get_daily_update_analysis(
    db: Session, *, update_id: int
) -> DailyWorkUpdateAnalysis | None:
    """Get the AI analysis for a daily work update."""
    return (
        db.query(DailyWorkUpdateAnalysis)
        .filter(DailyWorkUpdateAnalysis.daily_update_id == update_id)
        .first()
    )
