"""Unified, database-backed project health intelligence.

This service deliberately uses deterministic project signals first. It does not
invent percentages or require Gemini. The result gives managers one place to
see schedule, sprint, quality, capacity and delivery risks and the concrete
records behind each risk.
"""
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.task_enums import TaskStatus
from app.models.sprint import Sprint
from app.models.scrum_enums import SprintStatus
from app.models.milestone import Milestone
from app.models.project_enums import MilestoneStatus
from app.models.bug import Bug
from app.models.testing_enums import BugSeverity, BugStatus, TestCaseStatus
from app.models.test_case import TestCase
from app.models.leave import LeaveRequest, LeaveStatus
from app.models.weekly_availability import WeeklyAvailability
from app.models.daily_work_update import DailyWorkUpdate
from app.models.work_session import WorkSession, WorkSessionStatus


def build_project_health(db: Session, project: Project) -> dict:
    """Return a transparent project-health snapshot from current DB records."""
    today = date.today()
    tasks = db.query(Task).filter(Task.project_id == project.id).all()
    active_tasks = [t for t in tasks if t.status != TaskStatus.DONE]
    over_estimate_tasks = [t for t in active_tasks if t.estimated_hours and t.actual_hours and t.actual_hours > t.estimated_hours]
    overdue_tasks = [t for t in active_tasks if t.due_date and t.due_date < today]
    blocked_tasks = [t for t in active_tasks if t.status == TaskStatus.TESTING]

    active_sprint = (
        db.query(Sprint)
        .filter(Sprint.project_id == project.id, Sprint.status == SprintStatus.ACTIVE)
        .first()
    )
    sprint_total = 0
    sprint_done = 0
    if active_sprint:
        sprint_tasks = [t for t in tasks if t.sprint_id == active_sprint.id]
        sprint_total = len(sprint_tasks)
        sprint_done = sum(1 for t in sprint_tasks if t.status == TaskStatus.DONE)

    milestones = db.query(Milestone).filter(Milestone.project_id == project.id).all()
    late_milestones = [
        m for m in milestones
        if m.due_date and m.due_date < today and m.status != MilestoneStatus.COMPLETED
    ]

    bugs = db.query(Bug).filter(Bug.project_id == project.id).all()
    open_bugs = [b for b in bugs if b.status not in (BugStatus.CLOSED, BugStatus.VERIFIED)]
    critical_bugs = [b for b in open_bugs if b.severity == BugSeverity.CRITICAL]

    test_cases = db.query(TestCase).filter(TestCase.project_id == project.id).all()
    executed = [t for t in test_cases if t.status in (TestCaseStatus.PASSED, TestCaseStatus.FAILED)]
    passed = sum(1 for t in executed if t.status == TestCaseStatus.PASSED)
    pass_rate = round((passed / len(executed)) * 100, 1) if executed else None

    member_ids = [m.user_id for m in db.query(ProjectMember).filter(ProjectMember.project_id == project.id).all()]
    upcoming_leave = 0
    if member_ids:
        upcoming_leave = db.query(LeaveRequest).filter(
            LeaveRequest.user_id.in_(member_ids),
            LeaveRequest.status == LeaveStatus.APPROVED,
            LeaveRequest.start_date <= today + timedelta(days=14),
            LeaveRequest.end_date >= today,
        ).count()

    # Weekly availability records are optional; absence means no extra risk is inferred.
    # Sum the configured daily working windows rather than relying on a non-existent
    # precomputed hours field.
    active_work_sessions = 0
    if member_ids:
        active_work_sessions = db.query(WorkSession).filter(
            WorkSession.user_id.in_(member_ids),
            WorkSession.status == WorkSessionStatus.ACTIVE,
            WorkSession.ended_at.is_(None),
        ).count()

    updates_today = 0
    if member_ids:
        updates_today = db.query(DailyWorkUpdate).filter(
            DailyWorkUpdate.user_id.in_(member_ids),
            DailyWorkUpdate.date == today,
        ).count()

    reduced_availability = 0
    if member_ids:
        availability_rows = db.query(WeeklyAvailability).filter(
            WeeklyAvailability.user_id.in_(member_ids),
            WeeklyAvailability.effective_to.is_(None),
        ).all()
        hours_by_user = {uid: 0.0 for uid in member_ids}
        for row in availability_rows:
            if row.start_time and row.end_time:
                seconds = (
                    row.end_time.hour * 3600 + row.end_time.minute * 60 + row.end_time.second
                    - row.start_time.hour * 3600 - row.start_time.minute * 60 - row.start_time.second
                )
                if seconds > 0:
                    hours_by_user[row.user_id] = hours_by_user.get(row.user_id, 0.0) + seconds / 3600
        reduced_availability = sum(1 for hours in hours_by_user.values() if 0 < hours < 40)

    # Transparent component scores: 0-100, higher is healthier.
    schedule_score = 100
    if tasks:
        schedule_score -= min(60, round((len(overdue_tasks) / len(tasks)) * 100))
    if late_milestones:
        schedule_score -= min(30, len(late_milestones) * 10)
    schedule_score = max(0, schedule_score)

    sprint_score = 100
    if active_sprint and sprint_total:
        sprint_score = round((sprint_done / sprint_total) * 100)
        if active_sprint.end_date and active_sprint.end_date < today and sprint_done < sprint_total:
            sprint_score = max(0, sprint_score - 25)
    elif active_sprint:
        sprint_score = 75

    quality_score = 100
    if critical_bugs:
        quality_score -= min(60, len(critical_bugs) * 20)
    quality_score -= min(30, len(open_bugs) * 3)
    if pass_rate is not None and pass_rate < 80:
        quality_score -= 15
    quality_score = max(0, quality_score)

    capacity_score = 100
    capacity_score -= min(40, upcoming_leave * 8)
    capacity_score -= min(30, reduced_availability * 5)
    capacity_score = max(0, capacity_score)

    overall = round((schedule_score + sprint_score + quality_score + capacity_score) / 4)

    risks = []
    if overdue_tasks:
        risks.append({"severity": "high" if len(overdue_tasks) >= 3 else "medium", "type": "schedule", "title": f"{len(overdue_tasks)} overdue task(s)", "detail": "Active tasks have passed their due date."})
    if late_milestones:
        risks.append({"severity": "high", "type": "milestone", "title": f"{len(late_milestones)} milestone(s) are late", "detail": "Uncompleted milestones are past their due dates."})
    if critical_bugs:
        risks.append({"severity": "critical", "type": "quality", "title": f"{len(critical_bugs)} critical bug(s) open", "detail": "Critical defects remain unresolved or unverified."})
    if pass_rate is not None and pass_rate < 80:
        risks.append({"severity": "high", "type": "quality", "title": f"Test pass rate is {pass_rate}%", "detail": "Review failed tests and regression coverage before release."})
    if upcoming_leave:
        risks.append({"severity": "medium", "type": "capacity", "title": f"{upcoming_leave} approved leave record(s) affect the next 14 days", "detail": "Recheck sprint capacity and milestone ownership."})
    if reduced_availability:
        risks.append({"severity": "medium", "type": "capacity", "title": f"{reduced_availability} member(s) have reduced weekly availability", "detail": "Consider available capacity before assigning new work."})
    if over_estimate_tasks:
        risks.append({"severity": "medium", "type": "effort", "title": f"{len(over_estimate_tasks)} task(s) exceeded their estimate", "detail": "Review remaining effort before committing additional scope."})
    if member_ids and updates_today < len(member_ids):
        risks.append({"severity": "low", "type": "reporting", "title": f"{len(member_ids) - updates_today} team member(s) have not submitted today's update", "detail": "Follow up before using today's progress picture for planning."})

    recommendations = []
    if overdue_tasks:
        recommendations.append("Review overdue tasks, dependencies and remaining estimates.")
    if late_milestones:
        recommendations.append("Recheck milestone dates and move blocked work to the active plan.")
    if critical_bugs or (pass_rate is not None and pass_rate < 80):
        recommendations.append("Prioritize quality work before committing additional release scope.")
    if upcoming_leave or reduced_availability:
        recommendations.append("Rebalance upcoming work using actual available capacity.")
    if over_estimate_tasks:
        recommendations.append("Review tasks that exceeded their estimates and update remaining effort before replanning.")
    if member_ids and updates_today < len(member_ids):
        recommendations.append("Collect missing daily updates before finalizing today's project status.")
    if not recommendations:
        recommendations.append("No major rule-based risk signal is currently detected. Continue monitoring delivery and quality trends.")

    return {
        "project_id": project.id,
        "project_code": project.code,
        "project_name": project.name,
        "overall_health": overall,
        "health_label": "healthy" if overall >= 80 else "watch" if overall >= 60 else "at_risk",
        "components": {
            "schedule": schedule_score,
            "sprint": sprint_score,
            "quality": quality_score,
            "capacity": capacity_score,
        },
        "signals": {
            "active_tasks": len(active_tasks),
            "overdue_tasks": len(overdue_tasks),
            "blocked_or_testing_tasks": len(blocked_tasks),
            "active_sprint": active_sprint.name if active_sprint else None,
            "sprint_progress_percent": round((sprint_done / sprint_total) * 100, 1) if sprint_total else None,
            "late_milestones": len(late_milestones),
            "open_bugs": len(open_bugs),
            "critical_bugs": len(critical_bugs),
            "test_pass_rate": pass_rate,
            "upcoming_leave_records": upcoming_leave,
            "reduced_availability_members": reduced_availability,
            "over_estimate_tasks": len(over_estimate_tasks),
            "active_work_sessions": active_work_sessions,
            "daily_updates_submitted": updates_today,
            "daily_updates_expected": len(member_ids),
        },
        "risks": risks,
        "recommendations": recommendations,
        "generated_at": datetime.utcnow(),
    }
