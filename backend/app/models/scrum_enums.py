import enum


class StoryPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StoryStatus(str, enum.Enum):
    BACKLOG = "backlog"          # not yet selected for any sprint
    READY = "ready"               # refined, has points + acceptance criteria, ready to pull into a sprint
    IN_SPRINT = "in_sprint"       # selected into a sprint, not started
    IN_PROGRESS = "in_progress"
    DONE = "done"


class SprintStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
