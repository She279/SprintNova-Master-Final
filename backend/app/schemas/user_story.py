from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.scrum_enums import StoryPriority, StoryStatus


class UserStoryCreateRequest(BaseModel):
    title: str
    description: str | None = None
    acceptance_criteria: str | None = None
    priority: StoryPriority = StoryPriority.MEDIUM
    story_points: int | None = None
    epic_id: int | None = None
    assignee_id: int | None = None
    labels: list[str] = []


class UserStoryUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    acceptance_criteria: str | None = None
    priority: StoryPriority | None = None
    story_points: int | None = None
    status: StoryStatus | None = None
    epic_id: int | None = None
    assignee_id: int | None = None
    labels: list[str] | None = None


class BacklogReorderRequest(BaseModel):
    """New top-to-bottom order for a set of backlog items (drag-and-drop)."""
    story_ids_in_order: list[int]


class AssignToSprintRequest(BaseModel):
    sprint_id: int | None  # null to pull a story back out of its sprint


class UserStoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    key: str
    epic_id: int | None
    sprint_id: int | None
    title: str
    description: str | None
    acceptance_criteria: str | None
    priority: StoryPriority
    story_points: int | None
    status: StoryStatus
    labels: list[str]
    backlog_rank: int
    assignee_id: int | None
    reporter_id: int
    created_at: datetime
    updated_at: datetime


class UserStoryBrief(BaseModel):
    """Lightweight shape used inside sprint responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    title: str
    priority: StoryPriority
    story_points: int | None
    status: StoryStatus
    assignee_id: int | None
