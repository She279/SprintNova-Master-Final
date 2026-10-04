"""
Import every model module here so `Base.metadata.create_all()` (used for
local/demo bootstrapping) and Alembic autogenerate (used in production)
both discover all tables. Future modules should add their model imports
to this file too, e.g.:

    from app.models.project import Project        # Module 2
    from app.models.sprint import Sprint           # Module 3
"""
from app.models.role import RoleEnum, ADMIN_ROLES  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.login_history import LoginHistory  # noqa: F401
from app.models.otp import OTP, OTPPurpose  # noqa: F401

# --- Module 2: Project & Team Management ---
from app.models.project_enums import ProjectStatus, ProjectRole, MilestoneStatus  # noqa: F401
from app.models.client import Client  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.project_member import ProjectMember  # noqa: F401
from app.models.milestone import Milestone  # noqa: F401
from app.models.project_template import ProjectTemplate  # noqa: F401
from app.models.notification import Notification, NotificationType  # noqa: F401
from app.models.availability import Availability, AvailabilityStatus  # noqa: F401
from app.models.leave import LeaveRequest, LeaveType, LeaveStatus  # noqa: F401

# --- Employee Workspace: Work Sessions, Weekly Availability, Daily Updates ---
from app.models.work_session import WorkSession, WorkSessionStatus  # noqa: F401
from app.models.weekly_availability import WeeklyAvailability, DayOfWeek  # noqa: F401
from app.models.daily_work_update import DailyWorkUpdate  # noqa: F401
from app.models.daily_work_update_analysis import DailyWorkUpdateAnalysis, RiskLevel, AIProvider  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401

# --- Module 3: Product Backlog & Sprint Management (Scrum) ---
from app.models.scrum_enums import StoryPriority, StoryStatus, SprintStatus  # noqa: F401
from app.models.epic import Epic  # noqa: F401
from app.models.sprint import Sprint  # noqa: F401
from app.models.user_story import UserStory  # noqa: F401

# --- Module 4: Task & Kanban Management ---
from app.models.task_enums import TaskStatus, TaskPriority  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.task_comment import TaskComment  # noqa: F401
from app.models.task_history import TaskHistory  # noqa: F401

# --- Module 5: Testing & Bug Tracking ---
from app.models.testing_enums import (  # noqa: F401
    TestCaseStatus, TestPriority, ExecutionResult,
    BugSeverity, BugPriority, BugStatus, CodeReviewStatus, BuildStatus,
)
from app.models.test_case import TestCase  # noqa: F401
from app.models.test_execution import TestExecution  # noqa: F401
from app.models.bug import Bug  # noqa: F401
from app.models.bug_comment import BugComment  # noqa: F401
from app.models.bug_history import BugHistory  # noqa: F401
from app.models.code_review import CodeReview  # noqa: F401
from app.models.build import Build  # noqa: F401

# --- Module 7: AI Assistant & Knowledge Retrieval (ChromaDB/RAG) ---
from app.models.project_document import ProjectDocument, DocumentType  # noqa: F401

from app.models.project_attachment import ProjectAttachment  # noqa: F401
