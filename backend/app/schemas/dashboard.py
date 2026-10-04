"""
Schemas for Module 6 (Reports & Dashboards). Each role's dashboard shape is
genuinely different (spec: "each dashboard must contain role-specific
features"), so these are separate models rather than one bloated shared
shape with mostly-null fields.
"""
from datetime import date, datetime

from pydantic import BaseModel


class ProjectSummary(BaseModel):
    id: int
    code: str
    name: str
    status: str
    priority: str
    percent_complete: float


class WorkloadEntrySummary(BaseModel):
    user_id: int
    full_name: str
    role: str
    active_project_count: int


class LeaveStats(BaseModel):
    pending: int
    approved: int
    rejected: int


class AdminDashboardResponse(BaseModel):
    total_employees: int
    total_projects: int
    active_projects: int
    completed_projects: int
    project_status_distribution: dict[str, int]
    employee_workload: list[WorkloadEntrySummary]
    leave_stats: LeaveStats


class BacklogPriorityCount(BaseModel):
    priority: str
    count: int


class SprintSummary(BaseModel):
    id: int
    project_id: int
    project_code: str
    name: str
    status: str
    total_points: int
    completed_points: int


class ProductOwnerDashboardResponse(BaseModel):
    projects: list[ProjectSummary]
    backlog_priority_counts: list[BacklogPriorityCount]
    active_sprints: list[SprintSummary]
    latest_velocity_by_project: dict[str, float]


class ScrumMasterDashboardResponse(BaseModel):
    active_sprints: list[SprintSummary]
    team_workload: list[WorkloadEntrySummary]
    blocked_or_stale_tasks: list[dict]


class TaskBrief(BaseModel):
    key: str
    project_code: str
    title: str
    status: str
    priority: str
    due_date: date | None


class BugBrief(BaseModel):
    key: str
    project_code: str
    title: str
    severity: str
    status: str


class NotificationBrief(BaseModel):
    title: str
    created_at: datetime
    is_read: bool


class DeveloperDashboardResponse(BaseModel):
    my_tasks: list[TaskBrief]
    tasks_due_today: list[TaskBrief]
    tasks_overdue: list[TaskBrief]
    current_sprints: list[SprintSummary]
    bugs_assigned: list[BugBrief]
    recent_notifications: list[NotificationBrief]


class TesterDashboardResponse(BaseModel):
    test_cases_total: int
    tests_passed: int
    tests_failed: int
    open_bugs: list[BugBrief]
    bugs_awaiting_retest: list[BugBrief]
    testing_progress_percent: float


class ClientMilestone(BaseModel):
    title: str
    due_date: date | None
    status: str


class ClientProjectView(BaseModel):
    """Deliberately excludes internal employee/team detail -- spec: 'Do
    not expose internal employee information to clients.'"""
    id: int
    code: str
    name: str
    status: str
    percent_complete: float
    milestones: list[ClientMilestone]
    current_sprint_name: str | None
    current_sprint_status: str | None


class ClientDashboardResponse(BaseModel):
    projects: list[ClientProjectView]


class BugStatusCount(BaseModel):
    status: str
    count: int


class BugSeverityCount(BaseModel):
    severity: str
    count: int


class BugStatsResponse(BaseModel):
    by_status: list[BugStatusCount]
    by_severity: list[BugSeverityCount]


class TaskCompletionResponse(BaseModel):
    todo: int
    in_progress: int
    testing: int
    done: int


class TestingProgressResponse(BaseModel):
    total_test_cases: int
    passed: int
    failed: int
    not_run: int
    pass_rate: float
