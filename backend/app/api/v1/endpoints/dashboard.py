"""
Module 6: Reports & Dashboards.

`/dashboard` returns whichever shape matches the caller's own role --
deliberately un-typed at the FastAPI response_model level (a plain dict)
because the six role dashboards have genuinely different shapes (see
app/schemas/dashboard.py), and forcing one shared Pydantic model would
mean every dashboard carries a pile of nulls for fields that don't apply
to that role.

The project-scoped report endpoints below (`/reports/...`) return
strictly-typed Chart.js-ready data for a specific project.
"""
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models.user import User
from app.models.role import RoleEnum
from app.schemas.dashboard import BugStatsResponse, TaskCompletionResponse, TestingProgressResponse
from app.schemas.project_health import ProjectHealthResponse
from app.api.deps import require_password_already_set
from app.services import dashboard_service, project_service, project_health_service

router = APIRouter(tags=["Reports & Dashboards"])


@router.get("/dashboard")
def get_my_dashboard(db=Depends(get_db), user: User = Depends(require_password_already_set)):
    if user.role == RoleEnum.OWNER_ADMIN:
        return dashboard_service.get_admin_dashboard(db)
    if user.role == RoleEnum.PRODUCT_OWNER:
        return dashboard_service.get_product_owner_dashboard(db, user)
    if user.role == RoleEnum.PROJECT_MANAGER:
        return dashboard_service.get_project_manager_dashboard(db, user)
    if user.role == RoleEnum.SCRUM_MASTER:
        return dashboard_service.get_scrum_master_dashboard(db, user)
    if user.role == RoleEnum.TEAM_LEAD:
        return dashboard_service.get_team_lead_dashboard(db, user)
    if user.role == RoleEnum.DEVELOPER:
        return dashboard_service.get_developer_dashboard(db, user)
    if user.role == RoleEnum.TESTER:
        return dashboard_service.get_tester_dashboard(db, user)
    return dashboard_service.get_client_dashboard(db, user)


@router.get("/reports/projects/{project_id}/bug-stats", response_model=BugStatsResponse)
def bug_stats(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return dashboard_service.get_bug_stats(db, project_id)


@router.get("/reports/projects/{project_id}/task-completion", response_model=TaskCompletionResponse)
def task_completion(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return dashboard_service.get_task_completion(db, project_id)


@router.get("/reports/projects/{project_id}/testing-progress", response_model=TestingProgressResponse)
def testing_progress(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return dashboard_service.get_testing_progress(db, project_id)


@router.get("/reports/projects/{project_id}/health", response_model=ProjectHealthResponse)
def project_health(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    """Unified project-health snapshot from real delivery, sprint, quality and capacity data."""
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return project_health_service.build_project_health(db, project)
