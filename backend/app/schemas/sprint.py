from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.scrum_enums import SprintStatus
from app.schemas.user_story import UserStoryBrief


class SprintCreateRequest(BaseModel):
    name: str
    goal: str | None = None
    start_date: date
    end_date: date


class SprintUpdateRequest(BaseModel):
    name: str | None = None
    goal: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class SprintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    goal: str | None
    start_date: date
    end_date: date
    status: SprintStatus
    created_by_id: int
    created_at: datetime


class SprintDetailResponse(SprintResponse):
    stories: list[UserStoryBrief]
    total_points: int
    completed_points: int


class BurndownPoint(BaseModel):
    date: date
    ideal_remaining: float
    actual_remaining: float | None  # null for days in the future of an active sprint


class BurndownResponse(BaseModel):
    sprint_id: int
    total_points: int
    points: list[BurndownPoint]


class VelocityEntry(BaseModel):
    sprint_id: int
    sprint_name: str
    completed_points: int


class VelocityResponse(BaseModel):
    project_id: int
    sprints: list[VelocityEntry]
    average_velocity: float
