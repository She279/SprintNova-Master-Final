"""
Module 6: Reports & Dashboards.

This module deliberately does NOT introduce new source-of-truth data --
every number here is computed by querying Modules 1-5's own tables (or
calling their existing service functions) at request time. That's the
"do not hardcode dashboard metrics" rule from the spec: there is no
dashboard-specific table that could drift out of sync with reality.
"""
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import RoleEnum
from app.models.work_session import WorkSession, WorkSessionStatus
from app.models.daily_work_update import DailyWorkUpdate
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_enums import ProjectStatus, ProjectRole
from app.models.user_story import UserStory
from app.models.scrum_enums import StoryStatus
from app.models.sprint import Sprint
from app.models.scrum_enums import SprintStatus
from app.models.task import Task
from app.models.task_enums import TaskStatus
from app.models.bug import Bug
from app.models.testing_enums import BugStatus as BugStatusEnum
from app.models.test_case import TestCase
from app.models.testing_enums import TestCaseStatus
from app.models.leave import LeaveRequest, LeaveStatus
from app.models.milestone import Milestone
from app.services import project_service, milestone_service, sprint_service, ai_service, notification_service, project_health_service


def _project_summary(db: Session, project: Project) -> dict:
    progress = milestone_service.get_progress(db, project.id)
    return {
        "id": project.id, "code": project.code, "name": project.name,
        "status": project.status.value, "priority": project.priority.value,
        "percent_complete": progress.percent_complete,
    }


def _sprint_summary(db: Session, sprint: Sprint, project: Project) -> dict:
    stories = db.query(UserStory).filter(UserStory.sprint_id == sprint.id).all()
    total_points = sum(s.story_points or 0 for s in stories)
    completed_points = sum(s.story_points or 0 for s in stories if s.status == StoryStatus.DONE)
    return {
        "id": sprint.id, "project_id": project.id, "project_code": project.code,
        "name": sprint.name, "status": sprint.status.value,
        "total_points": total_points, "completed_points": completed_points,
    }


# --- Admin ---

def get_admin_dashboard(db: Session) -> dict:
    total_employees = db.query(User).count()
    projects = db.query(Project).all()
    status_counts: dict[str, int] = {}
    for p in projects:
        status_counts[p.status.value] = status_counts.get(p.status.value, 0) + 1

    workload = ai_service.workload_summary(db)
    employee_workload = [
        {"user_id": w["user_id"], "full_name": w["full_name"], "role": w["role"],
         "active_project_count": w["active_project_count"]}
        for w in workload
    ]

    leave_counts = {"pending": 0, "approved": 0, "rejected": 0}
    for status_val, count in (
        db.query(LeaveRequest.status, func.count(LeaveRequest.id)).group_by(LeaveRequest.status).all()
    ):
        if status_val.value in leave_counts:
            leave_counts[status_val.value] = count

    return {
        "total_employees": total_employees,
        "total_projects": len(projects),
        "active_projects": status_counts.get(ProjectStatus.ACTIVE.value, 0),
        "completed_projects": status_counts.get(ProjectStatus.COMPLETED.value, 0),
        "project_status_distribution": status_counts,
        "employee_workload": employee_workload,
        "leave_stats": leave_counts,
    }


# --- Product Owner ---

def get_product_owner_dashboard(db: Session, user: User) -> dict:
    projects = [
        p for p in project_service.list_visible_projects(db, user)
        if project_service.is_product_owner_on_project(db, p, user) or user.role == RoleEnum.OWNER_ADMIN
    ]
    project_ids = [p.id for p in projects]

    priority_counts: dict[str, int] = {}
    if project_ids:
        for priority, count in (
            db.query(UserStory.priority, func.count(UserStory.id))
            .filter(UserStory.project_id.in_(project_ids), UserStory.status != StoryStatus.DONE)
            .group_by(UserStory.priority)
            .all()
        ):
            priority_counts[priority.value] = count

    active_sprints = []
    velocity_by_project = {}
    for p in projects:
        for sprint in db.query(Sprint).filter(Sprint.project_id == p.id, Sprint.status == SprintStatus.ACTIVE).all():
            active_sprints.append(_sprint_summary(db, sprint, p))
        velocity = sprint_service.get_velocity(db, p.id)
        if velocity.sprints:
            velocity_by_project[p.code] = velocity.average_velocity

    return {
        "projects": [_project_summary(db, p) for p in projects],
        "backlog_priority_counts": [{"priority": k, "count": v} for k, v in priority_counts.items()],
        "active_sprints": active_sprints,
        "latest_velocity_by_project": velocity_by_project,
    }


# --- Scrum Master ---

def get_scrum_master_dashboard(db: Session, user: User) -> dict:
    projects = [
        p for p in project_service.list_visible_projects(db, user)
        if project_service.is_scrum_master_on_project(db, p, user) or user.role == RoleEnum.OWNER_ADMIN
    ]
    project_ids = [p.id for p in projects]

    active_sprints = []
    for p in projects:
        for sprint in db.query(Sprint).filter(Sprint.project_id == p.id, Sprint.status == SprintStatus.ACTIVE).all():
            active_sprints.append(_sprint_summary(db, sprint, p))

    member_ids = set()
    for pid in project_ids:
        for m in db.query(ProjectMember).filter(ProjectMember.project_id == pid).all():
            member_ids.add(m.user_id)
    full_workload = ai_service.workload_summary(db)
    team_workload = [
        {"user_id": w["user_id"], "full_name": w["full_name"], "role": w["role"],
         "active_project_count": w["active_project_count"]}
        for w in full_workload if w["user_id"] in member_ids
    ]

    # "Blocked or stale" is a real, transparent heuristic: a task sitting in
    # Testing or In Progress for more than 5 days without moving to Done.
    stale_cutoff = datetime.utcnow() - timedelta(days=5)
    stale_tasks = []
    if project_ids:
        for t in (
            db.query(Task)
            .filter(Task.project_id.in_(project_ids), Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.TESTING]))
            .filter(Task.updated_at < stale_cutoff)
            .all()
        ):
            stale_tasks.append({"key": t.key, "title": t.title, "status": t.status.value,
                                 "days_stale": (datetime.utcnow() - t.updated_at).days})

    return {
        "active_sprints": active_sprints,
        "team_workload": team_workload,
        "blocked_or_stale_tasks": stale_tasks,
    }


# --- Developer ---

def get_developer_dashboard(db: Session, user: User) -> dict:
    today = date.today()

    my_tasks = db.query(Task).filter(Task.assignee_id == user.id).all()
    project_codes = {p.id: p.code for p in db.query(Project).all()}

    def task_brief(t: Task) -> dict:
        return {
            "key": t.key, "project_code": project_codes.get(t.project_id, "?"), "title": t.title,
            "status": t.status.value, "priority": t.priority.value, "due_date": t.due_date,
        }

    tasks_due_today = [t for t in my_tasks if t.due_date == today and t.status != TaskStatus.DONE]
    tasks_overdue = [t for t in my_tasks if t.due_date and t.due_date < today and t.status != TaskStatus.DONE]

    projects = project_service.list_visible_projects(db, user)
    current_sprints = []
    for p in projects:
        for sprint in db.query(Sprint).filter(Sprint.project_id == p.id, Sprint.status == SprintStatus.ACTIVE).all():
            current_sprints.append(_sprint_summary(db, sprint, p))

    bugs_assigned = db.query(Bug).filter(Bug.assignee_id == user.id).all()

    def bug_brief(b: Bug) -> dict:
        return {"key": b.key, "project_code": project_codes.get(b.project_id, "?"), "title": b.title,
                "severity": b.severity.value, "status": b.status.value}

    notifications = notification_service.list_for_user(db, user.id)[:5]

    return {
        "my_tasks": [task_brief(t) for t in my_tasks],
        "tasks_due_today": [task_brief(t) for t in tasks_due_today],
        "tasks_overdue": [task_brief(t) for t in tasks_overdue],
        "current_sprints": current_sprints,
        "bugs_assigned": [bug_brief(b) for b in bugs_assigned],
        "recent_notifications": [
            {"title": n.title, "created_at": n.created_at, "is_read": n.is_read} for n in notifications
        ],
    }


# --- Tester ---

def get_tester_dashboard(db: Session, user: User) -> dict:
    projects = [
        p for p in project_service.list_visible_projects(db, user)
        if project_service.is_tester_on_project(db, p, user) or user.role == RoleEnum.OWNER_ADMIN
    ]
    project_ids = [p.id for p in projects]
    project_codes = {p.id: p.code for p in projects}

    test_cases = db.query(TestCase).filter(TestCase.project_id.in_(project_ids)).all() if project_ids else []
    passed = sum(1 for tc in test_cases if tc.status == TestCaseStatus.PASSED)
    failed = sum(1 for tc in test_cases if tc.status == TestCaseStatus.FAILED)
    executed = passed + failed

    bugs = db.query(Bug).filter(Bug.project_id.in_(project_ids)).all() if project_ids else []
    open_bugs = [b for b in bugs if b.status not in (BugStatusEnum.CLOSED, BugStatusEnum.VERIFIED)]
    awaiting_retest = [b for b in bugs if b.status == BugStatusEnum.RETESTING]

    def bug_brief(b: Bug) -> dict:
        return {"key": b.key, "project_code": project_codes.get(b.project_id, "?"), "title": b.title,
                "severity": b.severity.value, "status": b.status.value}

    return {
        "test_cases_total": len(test_cases),
        "tests_passed": passed,
        "tests_failed": failed,
        "open_bugs": [bug_brief(b) for b in open_bugs],
        "bugs_awaiting_retest": [bug_brief(b) for b in awaiting_retest],
        "testing_progress_percent": round((passed / executed) * 100, 1) if executed else 0.0,
    }


# --- Project Manager / Team Lead ---

def _management_dashboard(db: Session, user: User, *, team_lead: bool = False) -> dict:
    projects = project_service.list_visible_projects(db, user)
    project_ids = [p.id for p in projects]
    member_ids = {m.user_id for m in db.query(ProjectMember).filter(ProjectMember.project_id.in_(project_ids)).all()} if project_ids else set()
    members = db.query(User).filter(User.id.in_(member_ids)).all() if member_ids else []
    active_tasks = db.query(Task).filter(Task.project_id.in_(project_ids), Task.status != TaskStatus.DONE).all() if project_ids else []
    overdue = [t for t in active_tasks if t.due_date and t.due_date < date.today()]
    submitted = db.query(DailyWorkUpdate).filter(DailyWorkUpdate.user_id.in_(member_ids), DailyWorkUpdate.date == date.today()).count() if member_ids else 0
    working = db.query(WorkSession).filter(WorkSession.user_id.in_(member_ids), WorkSession.status == WorkSessionStatus.ACTIVE, WorkSession.ended_at == None).count() if member_ids else 0
    leave = db.query(LeaveRequest).filter(LeaveRequest.user_id.in_(member_ids), LeaveRequest.status == LeaveStatus.APPROVED, LeaveRequest.start_date <= date.today(), LeaveRequest.end_date >= date.today()).count() if member_ids else 0
    workload = ai_service.workload_summary(db)
    team_workload = [w for w in workload if w["user_id"] in member_ids]
    workload_recommendation, workload_ai_generated = ai_service.workload_recommendation(team_workload, use_ai=False)
    health = [project_health_service.build_project_health(db, p) for p in projects]
    return {
        "projects": [_project_summary(db,p) for p in projects], "team_members": len(members),
        "active_team_members": working, "on_leave_today": leave, "active_tasks": len(active_tasks),
        "overdue_tasks": len(overdue), "daily_updates_submitted": submitted,
        "daily_updates_pending": max(0,len(member_ids)-submitted),
        "risks": [{"key":t.key,"title":t.title,"reason":f"Overdue since {t.due_date}"} for t in overdue[:10]],
        "project_health": [{"project_id": h["project_id"], "project_code": h["project_code"], "project_name": h["project_name"], "overall_health": h["overall_health"], "health_label": h["health_label"], "risk_count": len(h["risks"])} for h in health],
        "team_workload": team_workload, "workload_recommendation": workload_recommendation,
        "workload_ai_generated": workload_ai_generated,
    }

def get_project_manager_dashboard(db: Session, user: User) -> dict:
    return _management_dashboard(db,user)

def get_team_lead_dashboard(db: Session, user: User) -> dict:
    return _management_dashboard(db,user,team_lead=True)


# --- Client ---

def get_client_dashboard(db: Session, user: User) -> dict:
    """Only ever includes project-level, client-safe fields -- never team
    member names, employee emails, bug detail, or internal task data."""
    memberships = (
        db.query(ProjectMember)
        .filter(ProjectMember.user_id == user.id, ProjectMember.project_role == ProjectRole.CLIENT_VIEWER)
        .all()
    )
    projects_out = []
    for m in memberships:
        project = db.get(Project, m.project_id)
        if not project:
            continue
        progress = milestone_service.get_progress(db, project.id)
        milestones = milestone_service.list_milestones(db, project.id)
        active_sprint = db.query(Sprint).filter(Sprint.project_id == project.id, Sprint.status == SprintStatus.ACTIVE).first()

        projects_out.append({
            "id": project.id, "code": project.code, "name": project.name, "status": project.status.value,
            "percent_complete": progress.percent_complete,
            "milestones": [{"title": ms.title, "due_date": ms.due_date, "status": ms.status.value} for ms in milestones],
            "current_sprint_name": active_sprint.name if active_sprint else None,
            "current_sprint_status": active_sprint.status.value if active_sprint else None,
        })

    return {"projects": projects_out}


# --- Standalone chart-data reports (project-scoped) ---

def get_bug_stats(db: Session, project_id: int) -> dict:
    by_status: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for bug in db.query(Bug).filter(Bug.project_id == project_id).all():
        by_status[bug.status.value] = by_status.get(bug.status.value, 0) + 1
        by_severity[bug.severity.value] = by_severity.get(bug.severity.value, 0) + 1
    return {
        "by_status": [{"status": k, "count": v} for k, v in by_status.items()],
        "by_severity": [{"severity": k, "count": v} for k, v in by_severity.items()],
    }


def get_task_completion(db: Session, project_id: int) -> dict:
    counts = {s.value: 0 for s in TaskStatus}
    for status_val, count in (
        db.query(Task.status, func.count(Task.id)).filter(Task.project_id == project_id).group_by(Task.status).all()
    ):
        counts[status_val.value] = count
    return counts


def get_testing_progress(db: Session, project_id: int) -> dict:
    test_cases = db.query(TestCase).filter(TestCase.project_id == project_id).all()
    passed = sum(1 for tc in test_cases if tc.status == TestCaseStatus.PASSED)
    failed = sum(1 for tc in test_cases if tc.status == TestCaseStatus.FAILED)
    not_run = len(test_cases) - passed - failed
    executed = passed + failed
    return {
        "total_test_cases": len(test_cases), "passed": passed, "failed": failed, "not_run": not_run,
        "pass_rate": round((passed / executed) * 100, 1) if executed else 0.0,
    }
