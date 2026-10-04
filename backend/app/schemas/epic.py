from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EpicCreateRequest(BaseModel):
    title: str
    description: str | None = None


class EpicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None
    created_at: datetime
