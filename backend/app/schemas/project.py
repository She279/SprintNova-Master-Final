from datetime import datetime, date

from pydantic import BaseModel, ConfigDict

from app.models.project_enums import ProjectStatus, ProjectPriority, ProjectMethodology, ProjectRole, MilestoneStatus


class ProjectCreateRequest(BaseModel):
    code: str
    name: str
    description: str | None = None
    client_id: int | None = None
    product_owner_id: int | None = None
    priority: ProjectPriority = ProjectPriority.MEDIUM
    methodology: ProjectMethodology = ProjectMethodology.SCRUM
    start_date: date | None = None
    end_date: date | None = None


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    priority: ProjectPriority | None = None
    methodology: ProjectMethodology | None = None
    client_id: int | None = None
    product_owner_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectMemberBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    project_role: ProjectRole
    full_name: str
    company_email: str


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    status: ProjectStatus
    priority: ProjectPriority
    methodology: ProjectMethodology
    client_id: int | None
    product_owner_id: int | None
    start_date: date | None
    end_date: date | None
    created_at: datetime


class ProjectDetailResponse(ProjectResponse):
    members: list[ProjectMemberBrief] = []


class AddProjectMemberRequest(BaseModel):
    user_id: int
    project_role: ProjectRole


class MilestoneCreateRequest(BaseModel):
    title: str
    description: str | None = None
    due_date: date | None = None
    phase: str | None = None
    sort_order: int = 0


class MilestoneUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: date | None = None
    status: MilestoneStatus | None = None
    phase: str | None = None
    sort_order: int | None = None


class MilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None
    due_date: date | None
    status: MilestoneStatus
    phase: str | None
    sort_order: int
    created_at: datetime


class RoadmapPhase(BaseModel):
    phase: str
    milestones: list[MilestoneResponse]


class RoadmapResponse(BaseModel):
    project_id: int
    phases: list[RoadmapPhase]


class ProgressPoint(BaseModel):
    date: date
    cumulative_completed: int


class ProjectProgressResponse(BaseModel):
    """
    Milestone-completion-based progress for a project. This is a stand-in
    for real sprint burndown/velocity charts, which need actual sprint
    data (Module 3, not yet built) -- until then, this is the most honest
    "team progress" signal available: how many of the project's planned
    milestones are actually done, and when they were completed.
    """
    project_id: int
    total_milestones: int
    completed_milestones: int
    missed_milestones: int
    percent_complete: float
    timeline: list[ProgressPoint]
