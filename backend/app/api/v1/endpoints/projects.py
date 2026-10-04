from fastapi import APIRouter, Depends, File, UploadFile

from app.core.database import get_db
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest, ProjectUpdateRequest, ProjectResponse, ProjectDetailResponse,
    AddProjectMemberRequest, ProjectMemberBrief,
    MilestoneCreateRequest, MilestoneUpdateRequest, MilestoneResponse, RoadmapResponse,
    ProjectProgressResponse,
)
from app.api.deps import require_role, require_password_already_set
from app.services import project_service, project_member_service, milestone_service, project_intelligence_service

router = APIRouter(prefix="/projects", tags=["Projects & Teams"])

_CAN_CREATE_PROJECT = require_role(RoleEnum.OWNER_ADMIN, RoleEnum.PRODUCT_OWNER)


@router.post("/analyze-abstract", response_model=dict)
def analyze_project_abstract(file: UploadFile = File(...), user: User = Depends(_CAN_CREATE_PROJECT)):
    return project_intelligence_service.analyze_abstract(file)


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(payload: ProjectCreateRequest, db=Depends(get_db), user: User = Depends(_CAN_CREATE_PROJECT)):
    return project_service.create_project(db, payload, created_by=user)


@router.get("", response_model=list[ProjectResponse])
def list_projects(db=Depends(get_db), user: User = Depends(require_password_already_set)):
    """Admins see every project; everyone else sees only projects they're a team member on."""
    return project_service.list_visible_projects(db, user)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    members = [] if user.role == RoleEnum.CLIENT else project_member_service.list_members(db, project_id)
    return ProjectDetailResponse(**ProjectResponse.model_validate(project).model_dump(), members=members)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int, payload: ProjectUpdateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_manage_access(db, project, user)
    return project_service.update_project(db, project, payload)


# --- Team roster ---

@router.get("/{project_id}/members", response_model=list[ProjectMemberBrief])
def list_members(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        from fastapi import HTTPException, status
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Client accounts cannot access internal team roster data")
    return project_member_service.list_members(db, project_id)


@router.post("/{project_id}/members", response_model=ProjectMemberBrief, status_code=201)
def add_member(
    project_id: int, payload: AddProjectMemberRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_manage_access(db, project, user)
    member = project_member_service.add_member(db, project, payload)
    brief = [m for m in project_member_service.list_members(db, project_id) if m.id == member.id][0]
    return brief


@router.delete("/{project_id}/members/{member_id}", status_code=204)
def remove_member(
    project_id: int, member_id: int,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_manage_access(db, project, user)
    project_member_service.remove_member(db, project_id, member_id)


# --- Milestones ---

@router.get("/{project_id}/milestones", response_model=list[MilestoneResponse])
def list_milestones(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return milestone_service.list_milestones(db, project_id)


@router.post("/{project_id}/milestones", response_model=MilestoneResponse, status_code=201)
def create_milestone(
    project_id: int, payload: MilestoneCreateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_manage_access(db, project, user)
    return milestone_service.create_milestone(db, project_id, payload)


@router.patch("/{project_id}/milestones/{milestone_id}", response_model=MilestoneResponse)
def update_milestone(
    project_id: int, milestone_id: int, payload: MilestoneUpdateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_manage_access(db, project, user)
    milestone = milestone_service.get_milestone_or_404(db, project_id, milestone_id)
    return milestone_service.update_milestone(db, milestone, payload)


# --- Roadmap ---

@router.get("/{project_id}/roadmap", response_model=RoadmapResponse)
def get_roadmap(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return milestone_service.get_roadmap(db, project_id)


# --- Progress (stand-in for sprint charts until Module 3) ---

@router.get("/{project_id}/progress", response_model=ProjectProgressResponse)
def get_progress(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return milestone_service.get_progress(db, project_id)
