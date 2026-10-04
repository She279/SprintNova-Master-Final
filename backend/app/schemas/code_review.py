from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.testing_enums import CodeReviewStatus


class CodeReviewCreateRequest(BaseModel):
    title: str
    description: str | None = None
    task_id: int | None = None
    reviewer_id: int | None = None


class CodeReviewUpdateRequest(BaseModel):
    status: CodeReviewStatus | None = None
    reviewer_id: int | None = None
    description: str | None = None


class CodeReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    task_id: int | None
    title: str
    description: str | None
    status: CodeReviewStatus
    author_id: int
    reviewer_id: int | None
    created_at: datetime
    updated_at: datetime
