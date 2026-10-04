"""
Enums scoped to Module 2 (Projects & Teams). Kept separate from
app.models.role.RoleEnum, which is the org-wide employee role — a person's
org role (e.g. Developer) is independent of their role on a specific
project team (e.g. they could be a Tester on Project A's team even if
their employee role is Developer, in smaller orgs that double people up).
"""
import enum


class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProjectMethodology(str, enum.Enum):
    SCRUM = "scrum"
    KANBAN = "kanban"
    XP = "xp"
    LEAN = "lean"
    HYBRID = "hybrid"


class ProjectRole(str, enum.Enum):
    PRODUCT_OWNER = "product_owner"
    SCRUM_MASTER = "scrum_master"
    DEVELOPER = "developer"
    TESTER = "tester"
    CLIENT_VIEWER = "client_viewer"
    PROJECT_MANAGER = "project_manager"
    TEAM_LEAD = "team_lead"


class MilestoneStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"
