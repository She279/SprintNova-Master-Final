from typing import Literal

from pydantic import BaseModel, Field


class WhatIfSimulationRequest(BaseModel):
    scenario: Literal["leave", "delay"]
    days: int = Field(default=1, ge=1, le=30)
    user_id: int | None = None
    project_id: int | None = None
    task_id: int | None = None


class WorkloadEntry(BaseModel):
    user_id: int
    full_name: str
    role: str
    active_project_count: int
    unavailable_days_next_14: int
    available_capacity_hours: float
    assigned_effort_hours: float
    remaining_capacity_hours: float
    utilization_percent: float | None
    active_task_count: int
    overdue_task_count: int
    blocked_task_count: int
    workload_status: str


class WorkloadSummaryResponse(BaseModel):
    team: list[WorkloadEntry]
    recommendation: str
    ai_generated: bool


class TeamAllocationResponse(BaseModel):
    missing_roles: list[str]
    candidates_by_role: dict
    recommendation: str
    ai_generated: bool


class BacklogItemBrief(BaseModel):
    key: str
    title: str
    story_points: int | None
    priority: str


class SprintPlanningResponse(BaseModel):
    recommended_capacity: float
    capacity_is_default: bool
    recommended_stories: list[BacklogItemBrief]
    postponed_stories: list[BacklogItemBrief]
    needs_estimation: list[BacklogItemBrief]
    recommendation: str
    ai_generated: bool


class TaskBrief(BaseModel):
    key: str
    title: str
    status: str
    due_date: str | None
    estimated_hours: float | None
    actual_hours: float | None


class TaskRiskResponse(BaseModel):
    overdue_tasks: list[TaskBrief]
    at_risk_tasks: list[TaskBrief]
    over_estimate_tasks: list[TaskBrief]
    recommendation: str
    ai_generated: bool


class BugBrief(BaseModel):
    key: str
    title: str
    severity: str
    status: str


class DuplicateBugPair(BaseModel):
    bug_a: str
    bug_b: str
    title_similarity: float


class QualityRiskResponse(BaseModel):
    risk_level: str
    risk_score: int
    is_ml_prediction: bool
    open_bug_count: int
    critical_open_bugs: list[BugBrief]
    reopened_bugs: list[BugBrief]
    avg_resolution_days: float | None
    test_pass_rate: float | None
    tests_passed: int
    tests_failed: int
    tests_not_run: int
    possible_duplicates: list[DuplicateBugPair]
    recommendation: str
    ai_generated: bool


class CompletionPredictionResponse(BaseModel):
    predicted_completion_date: str
    confidence: str
    provider: str
    historical_velocity: float
    completed_story_points: int
    remaining_story_points: int
    completed_tasks: int
    remaining_tasks: int
    unestimated_stories: int
    overdue_tasks: int
    over_estimate_tasks: int
    signals: list[str]
    recommendation: str
