from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.task_enums import TaskStatus, TaskPriority


class TaskCreateRequest(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    sprint_id: int | None = None
    user_story_id: int | None = None
    assignee_id: int | None = None
    due_date: date | None = None
    estimated_hours: float | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    sprint_id: int | None = None
    user_story_id: int | None = None
    assignee_id: int | None = None
    due_date: date | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    key: str
    sprint_id: int | None
    user_story_id: int | None
    title: str
    description: str | None
    priority: TaskPriority
    status: TaskStatus
    due_date: date | None
    estimated_hours: float | None
    actual_hours: float | None
    assignee_id: int | None
    reporter_id: int
    created_at: datetime
    updated_at: datetime


class TaskCommentCreateRequest(BaseModel):
    body: str


class TaskCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    author_id: int
    body: str
    created_at: datetime


class TaskHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_id: int
    field_changed: str
    old_value: str | None
    new_value: str | None
    created_at: datetime
