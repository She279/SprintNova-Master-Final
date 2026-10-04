"""
Daily work update endpoints.

Handles daily work summary creation, retrieval, updates, and AI analysis.
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_db_and_user, require_role
from app.models.role import RoleEnum
from app.models.user import User
from app.models.task import Task
from app.models.task_enums import TaskStatus
from app.services.audit_service import audit_log
from app.schemas.daily_work_update import (
    DailyWorkUpdateCreate,
    DailyWorkUpdateUpdate,
    DailyWorkUpdateResponse,
    DailyWorkUpdateDetailResponse,
)
from app.schemas.daily_work_update_analysis import DailyWorkUpdateAnalysisResponse
from app.services.daily_work_update_service import (
    create_daily_work_update,
    get_daily_work_update,
    get_user_daily_update,
    update_daily_work_update,
    get_user_daily_updates,
    get_team_daily_updates,
    check_pending_daily_updates,
    get_daily_update_analysis,
)
from app.services.daily_work_update_analysis_service import (
    analyze_daily_update,
    get_analysis_or_create,
)

router = APIRouter(prefix="/daily-updates", tags=["Daily Work Updates"])


@router.post("")
def create_update(
    update_data: DailyWorkUpdateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DailyWorkUpdateResponse:
    """
    Create a daily work update for today.
    
    Prevents duplicate updates for the same date.
    """
    try:
        update = create_daily_work_update(
            db,
            user_id=user.id,
            work_done=update_data.work_done,
            completed_work=update_data.completed_work,
            pending_work=update_data.pending_work,
            blockers=update_data.blockers,
            additional_notes=update_data.additional_notes,
            progress_percentage=update_data.progress_percentage,
            project_id=update_data.project_id,
            date_=update_data.date,
        )
    except HTTPException as e:
        raise e

    # Generate and persist analysis immediately; failures fall back inside the analysis service.
    try:
        analyze_daily_update(db, user_id=user.id, daily_update=update)
    except Exception:
        # The update itself remains valid even if an optional AI provider fails.
        pass
    return DailyWorkUpdateResponse.model_validate(update)


@router.get("/me/today")
def get_today_update(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DailyWorkUpdateDetailResponse | None:
    """Get today's daily work update for the authenticated user."""
    update = get_user_daily_update(db, user_id=user.id, date_=date.today())
    if not update:
        return None

    response = DailyWorkUpdateDetailResponse.model_validate(update)

    # Try to include analysis if it exists
    analysis = get_daily_update_analysis(db, update_id=update.id)
    if analysis:
        response.analysis = DailyWorkUpdateAnalysisResponse.model_validate(analysis).model_dump()

    return response


@router.get("/me/pending")
def check_pending_update(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Check if user has pending daily work update for today."""
    is_pending = check_pending_daily_updates(db, user_id=user.id)
    if is_pending:
        from app.models.notification import Notification, NotificationType
        from app.services.notification_service import notify
        from datetime import datetime
        existing = db.query(Notification).filter(Notification.user_id == user.id, Notification.type == NotificationType.DAILY_UPDATE_PENDING, Notification.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)).first()
        if not existing:
            notify(db, user=user, type=NotificationType.DAILY_UPDATE_PENDING, title="Today's work update is pending", body="Please submit your daily work update before ending your working day.", also_email=False)
    return {
        "user_id": user.id,
        "is_pending": is_pending,
        "date": date.today().isoformat(),
    }


@router.get("/me/history")
def get_user_update_history(
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 30,
    skip: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Get daily work update history for the authenticated user."""
    updates, total = get_user_daily_updates(
        db,
        user_id=user.id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        skip=skip,
    )

    return {
        "updates": [DailyWorkUpdateResponse.model_validate(u) for u in updates],
        "total": total,
        "limit": limit,
        "skip": skip,
    }


@router.put("/{update_id}")
def update_daily_update(
    update_id: int,
    update_data: DailyWorkUpdateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DailyWorkUpdateResponse:
    """Update an existing daily work update (if not yet analyzed)."""
    update = update_daily_work_update(
        db,
        update_id=update_id,
        user_id=user.id,
        work_done=update_data.work_done,
        completed_work=update_data.completed_work,
        pending_work=update_data.pending_work,
        blockers=update_data.blockers,
        additional_notes=update_data.additional_notes,
        progress_percentage=update_data.progress_percentage,
    )

    return DailyWorkUpdateResponse.model_validate(update)


@router.get("/{update_id}/analysis")
def get_update_analysis(
    update_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DailyWorkUpdateAnalysisResponse:
    """Get AI analysis for a daily work update."""
    update = get_daily_work_update(db, update_id=update_id, user_id=user.id)
    if not update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Update not found")

    # Get or create analysis
    analysis = get_analysis_or_create(db, user_id=user.id, daily_update=update)

    return DailyWorkUpdateAnalysisResponse.model_validate(analysis)


@router.post("/{update_id}/analyze")
def trigger_analysis(
    update_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DailyWorkUpdateAnalysisResponse:
    """
    Explicitly trigger AI analysis for a daily work update.
    
    Recreates analysis if it already exists.
    """
    update = get_daily_work_update(db, update_id=update_id, user_id=user.id)
    if not update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Update not found")

    analysis = analyze_daily_update(db, user_id=user.id, daily_update=update)

    return DailyWorkUpdateAnalysisResponse.model_validate(analysis)


@router.get("/team/today")
def get_team_updates_today(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(RoleEnum.SCRUM_MASTER, RoleEnum.PROJECT_MANAGER, RoleEnum.TEAM_LEAD, RoleEnum.OWNER_ADMIN)),
) -> dict:
    """
    Get daily updates submitted by team members today.
    
    Only accessible to authorized project managers, team leads, scrum masters, and admins.
    """
    from app.models.project_member import ProjectMember
    from app.models.project import Project

    # Get projects where user is a team member/lead
    projects = (
        db.query(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .filter(ProjectMember.user_id == user.id)
        .all()
    )

    if not projects:
        return {"team_updates": {}, "date": date.today().isoformat()}

    # Get team members in these projects
    team_members = (
        db.query(ProjectMember.user_id)
        .filter(ProjectMember.project_id.in_([p.id for p in projects]))
        .distinct()
        .all()
    )
    team_member_ids = [tm[0] for tm in team_members]

    # Get updates
    updates_dict = get_team_daily_updates(db, team_member_ids=team_member_ids, date_=date.today())

    return {
        "team_updates": {
            user_id: DailyWorkUpdateResponse.model_validate(upd).model_dump() if upd else None
            for user_id, upd in updates_dict.items()
        },
        "date": date.today().isoformat(),
        "total_team_members": len(team_member_ids),
        "submitted_count": sum(1 for u in updates_dict.values() if u),
    }


@router.post("/{update_id}/task-suggestions/{task_id}/review")
def review_task_suggestion(update_id: int, task_id: int, accepted: bool, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    update = get_daily_work_update(db, update_id=update_id, user_id=user.id)
    if not update:
        raise HTTPException(status_code=404, detail="Update not found")
    task = db.get(Task, task_id)
    if not task or task.assignee_id != user.id:
        raise HTTPException(status_code=404, detail="Assigned task not found")
    analysis = get_analysis_or_create(db, user_id=user.id, daily_update=update)
    import json
    suggestions = json.loads(analysis.task_suggestions or "[]")
    suggestion = next((x for x in suggestions if x.get("task_id") == task_id), None)
    if not suggestion:
        raise HTTPException(status_code=400, detail="No AI suggestion exists for this task")
    audit_log(db, user_id=user.id, action="ai_suggestion_accepted" if accepted else "ai_suggestion_rejected", entity_type="task", entity_id=task_id, changes={"suggestion": suggestion})
    if accepted:
        task.status = TaskStatus(suggestion["suggested_status"])
        db.commit(); db.refresh(task)
        audit_log(db, user_id=user.id, action="task_changed_based_on_ai_suggestion", entity_type="task", entity_id=task_id, changes={"new_status": task.status.value})
    return {"accepted": accepted, "task_id": task.id, "status": task.status.value}
