from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.testing_enums import BuildStatus


class BuildCreateRequest(BaseModel):
    label: str


class BuildUpdateRequest(BaseModel):
    status: BuildStatus
    log_summary: str | None = None


class BuildResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    label: str
    status: BuildStatus
    log_summary: str | None
    triggered_by_id: int
    created_at: datetime
    finished_at: datetime | None
