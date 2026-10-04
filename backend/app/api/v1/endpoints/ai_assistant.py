from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.ai import WorkloadSummaryResponse, TeamAllocationResponse, SprintPlanningResponse, TaskRiskResponse, QualityRiskResponse, CompletionPredictionResponse, WhatIfSimulationRequest
from app.api.deps import require_role, require_password_already_set
from app.services import ai_service, project_service, command_center_service, simulation_service

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

_ORG_AI_ROLES = require_role(RoleEnum.OWNER_ADMIN)
_PROJECT_AI_ROLES = require_role(RoleEnum.OWNER_ADMIN, RoleEnum.PROJECT_MANAGER, RoleEnum.PRODUCT_OWNER, RoleEnum.SCRUM_MASTER, RoleEnum.TEAM_LEAD)


@router.get("/command-center", response_model=dict)
def command_center(db=Depends(get_db), _user: User = Depends(_ORG_AI_ROLES)):
    return command_center_service.get_command_center(db)


@router.post("/simulate", response_model=dict)
def simulate(payload: WhatIfSimulationRequest, db=Depends(get_db), user: User = Depends(_PROJECT_AI_ROLES)):
    if payload.project_id:
        project = project_service.get_project_or_404(db, payload.project_id)
        project_service.require_view_access(db, project, user)
    return simulation_service.simulate(db, payload, user)


@router.get("/workload-summary", response_model=WorkloadSummaryResponse)
def workload_summary(db=Depends(get_db), _user: User = Depends(_ORG_AI_ROLES)):
    summary = ai_service.workload_summary(db)
    recommendation, ai_generated = ai_service.workload_recommendation(summary)
    return WorkloadSummaryResponse(team=summary, recommendation=recommendation, ai_generated=ai_generated)


@router.get("/projects/{project_id}/team-allocation", response_model=TeamAllocationResponse)
def team_allocation(project_id: int, db=Depends(get_db), user: User = Depends(_PROJECT_AI_ROLES)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return ai_service.team_allocation_suggestion(db, project)


@router.get("/projects/{project_id}/sprint-planning", response_model=SprintPlanningResponse)
def sprint_planning(project_id: int, db=Depends(get_db), user: User = Depends(_PROJECT_AI_ROLES)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return ai_service.sprint_planning_recommendation(db, project)


@router.get("/projects/{project_id}/task-risk", response_model=TaskRiskResponse)
def task_risk(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    """Open to any project member (not just planning roles) -- developers
    and testers benefit from seeing overdue/at-risk tasks just as much as
    the Product Owner or Scrum Master do."""
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return ai_service.task_risk_analysis(db, project)


@router.get("/projects/{project_id}/quality-risk", response_model=QualityRiskResponse)
def quality_risk(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    """Open to any project member, same reasoning as task-risk above."""
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return ai_service.quality_risk_analysis(db, project)


@router.get("/projects/{project_id}/completion-prediction", response_model=CompletionPredictionResponse)
def completion_prediction(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return ai_service.completion_prediction(db, project)
