from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.testing_enums import TestCaseStatus, TestPriority, ExecutionResult


class TestCaseCreateRequest(BaseModel):
    title: str
    description: str | None = None
    preconditions: str | None = None
    steps: str | None = None
    expected_result: str | None = None
    priority: TestPriority = TestPriority.MEDIUM
    user_story_id: int | None = None
    tester_id: int | None = None


class TestCaseUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    preconditions: str | None = None
    steps: str | None = None
    expected_result: str | None = None
    priority: TestPriority | None = None
    status: TestCaseStatus | None = None
    user_story_id: int | None = None
    tester_id: int | None = None


class TestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    key: str
    user_story_id: int | None
    title: str
    description: str | None
    preconditions: str | None
    steps: str | None
    expected_result: str | None
    priority: TestPriority
    status: TestCaseStatus
    tester_id: int | None
    created_by_id: int
    created_at: datetime
    updated_at: datetime


class TestExecutionCreateRequest(BaseModel):
    result: ExecutionResult
    actual_result: str | None = None
    notes: str | None = None


class TestExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_case_id: int
    executed_by_id: int
    result: ExecutionResult
    actual_result: str | None
    notes: str | None
    executed_at: datetime
