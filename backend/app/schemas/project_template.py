from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.project_enums import ProjectRole


class TemplateMilestoneSpec(BaseModel):
    title: str
    phase: str | None = None
    offset_days: int = Field(0, description="Days after the project start date this milestone is due")


class ProjectTemplateCreateRequest(BaseModel):
    name: str
    description: str | None = None
    default_milestones: list[TemplateMilestoneSpec] = []
    default_project_roles: list[ProjectRole] = []


class ProjectTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    default_milestones: list[TemplateMilestoneSpec]
    default_project_roles: list[ProjectRole]
    created_at: datetime


class ApplyTemplateRequest(BaseModel):
    """Create a new project by applying a template's default milestones."""
    code: str
    name: str
    description: str | None = None
    client_id: int | None = None
    product_owner_id: int | None = None
    start_date: str  # ISO date; required so milestone offsets can be resolved
