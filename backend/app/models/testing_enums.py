import enum


class TestCaseStatus(str, enum.Enum):
    DRAFT = "draft"        # written, not yet executed
    READY = "ready"        # reviewed, ready to execute
    PASSED = "passed"      # last execution passed
    FAILED = "failed"      # last execution failed
    BLOCKED = "blocked"    # can't execute (e.g. dependency broken)


class TestPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExecutionResult(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"


class BugSeverity(str, enum.Enum):
    """Impact on the system if left unfixed -- independent of BugPriority
    (how soon it should be worked on). A cosmetic typo can be Critical
    priority right before a demo; a rare crash can be Critical severity
    but Low priority if no one hits it in practice."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"


class BugPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BugStatus(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    RETESTING = "retesting"
    VERIFIED = "verified"
    REOPENED = "reopened"
    CLOSED = "closed"


class CodeReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


class BuildStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESSFUL = "successful"
    FAILED = "failed"
