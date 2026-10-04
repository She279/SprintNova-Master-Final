from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.testing_enums import BugSeverity, BugPriority, BugStatus


class BugCreateRequest(BaseModel):
    title: str
    description: str | None = None
    environment: str | None = None
    steps_to_reproduce: str | None = None
    expected_result: str | None = None
    actual_result: str | None = None
    severity: BugSeverity = BugSeverity.MINOR
    priority: BugPriority = BugPriority.MEDIUM
    test_case_id: int | None = None
    assignee_id: int | None = None


class BugUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    environment: str | None = None
    steps_to_reproduce: str | None = None
    expected_result: str | None = None
    actual_result: str | None = None
    severity: BugSeverity | None = None
    priority: BugPriority | None = None
    status: BugStatus | None = None
    assignee_id: int | None = None


class BugResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    key: str
    test_case_id: int | None
    title: str
    description: str | None
    environment: str | None
    steps_to_reproduce: str | None
    expected_result: str | None
    actual_result: str | None
    severity: BugSeverity
    priority: BugPriority
    status: BugStatus
    reporter_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class BugCommentCreateRequest(BaseModel):
    body: str


class BugCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bug_id: int
    author_id: int
    body: str
    created_at: datetime


class BugHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bug_id: int
    user_id: int
    field_changed: str
    old_value: str | None
    new_value: str | None
    created_at: datetime
