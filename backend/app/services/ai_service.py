"""
AI-based suggestions for project planning, team allocation, and workload
balancing (spec: "provides AI-based suggestions to support project
planning, team allocation, workload balancing, and overall project
management").

Design: every function here computes its numbers from REAL SprintNova data
first (active project counts, roster gaps, availability/leave records) --
never fabricated. Gemini, if configured, is used ONLY to turn those real
numbers into a short written recommendation. If GEMINI_API_KEY is not set,
or the call fails for any reason, the endpoint still returns the real
computed data plus a rule-based (non-LLM) recommendation string instead of
an error -- there is no scenario where this returns fake/hardcoded output.
"""
from datetime import date, timedelta

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.role import RoleEnum
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_enums import ProjectStatus, ProjectRole
from app.models.availability import Availability, AvailabilityStatus
from app.models.task import Task
from app.models.task_enums import TaskStatus
from app.services.weekly_availability_service import calculate_available_hours


def _call_gemini(prompt: str) -> str | None:
    if not settings.GEMINI_API_KEY:
        return None
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    )
    try:
        resp = requests.post(
            url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        # Network unavailable, bad key, quota exceeded, unexpected response
        # shape, etc. -- degrade gracefully to the rule-based text rather
        # than failing the request.
        return None


def workload_summary(db: Session) -> list[dict]:
    """Active-project count + near-term unavailability per active employee
    -- the real numbers behind any workload-balancing suggestion."""
    employees = db.query(User).filter(User.is_active == True).all()  # noqa: E712
    today = date.today()
    window_end = today + timedelta(days=14)

    summary = []
    for emp in employees:
        active_count = (
            db.query(ProjectMember)
            .join(Project, ProjectMember.project_id == Project.id)
            .filter(ProjectMember.user_id == emp.id, Project.status == ProjectStatus.ACTIVE)
            .count()
        )
        unavailable_days = (
            db.query(Availability)
            .filter(
                Availability.user_id == emp.id,
                Availability.date >= today,
                Availability.date <= window_end,
                Availability.status == AvailabilityStatus.UNAVAILABLE,
            )
            .count()
        )
        tasks = db.query(Task).filter(Task.assignee_id == emp.id, Task.status != TaskStatus.DONE).all()
        capacity = calculate_available_hours(db, user_id=emp.id, from_days=14)["total_available_hours"]
        assigned_effort = round(sum(task.estimated_hours or 0 for task in tasks), 2)
        utilization = round((assigned_effort / capacity) * 100, 1) if capacity else None
        overdue_tasks = sum(1 for task in tasks if task.due_date and task.due_date < today)
        blocked_tasks = sum(1 for task in tasks if task.status == TaskStatus.TESTING)
        if capacity == 0:
            workload_status = "unavailable"
        elif utilization is not None and utilization > 100:
            workload_status = "overloaded"
        elif utilization is not None and utilization >= 85:
            workload_status = "high_load"
        elif utilization is not None and utilization < 40:
            workload_status = "underutilized"
        else:
            workload_status = "healthy"
        summary.append({
            "user_id": emp.id,
            "full_name": f"{emp.first_name} {emp.last_name}",
            "role": emp.role.value,
            "active_project_count": active_count,
            "unavailable_days_next_14": unavailable_days,
            "available_capacity_hours": round(capacity, 2),
            "assigned_effort_hours": assigned_effort,
            "remaining_capacity_hours": round(capacity - assigned_effort, 2),
            "utilization_percent": utilization,
            "active_task_count": len(tasks),
            "overdue_task_count": overdue_tasks,
            "blocked_task_count": blocked_tasks,
            "workload_status": workload_status,
        })
    return sorted(summary, key=lambda s: s["active_project_count"], reverse=True)


def workload_recommendation(summary: list[dict], *, use_ai: bool = True) -> tuple[str, bool]:
    if not summary:
        return "No active employees to evaluate yet.", False

    counts = [s["active_project_count"] for s in summary]
    max_load, min_load = max(counts), min(counts)

    prompt = (
        "You are an assistant for an Agile project management tool. Given this real "
        "team workload data (active project counts and upcoming unavailable days per "
        f"person), write a 2-3 sentence, plain-language workload-balancing recommendation:\n{summary}"
    )
    ai_text = _call_gemini(prompt) if use_ai else None
    if ai_text:
        return ai_text, True

    if max_load - min_load <= 1:
        return "Workload looks evenly distributed across the team — no rebalancing needed right now.", False

    overloaded = [s["full_name"] for s in summary if s["active_project_count"] == max_load]
    underloaded = [s["full_name"] for s in summary if s["active_project_count"] == min_load]
    return (
        f"{', '.join(overloaded)} {'are' if len(overloaded) > 1 else 'is'} carrying the most active "
        f"projects ({max_load}), while {', '.join(underloaded)} {'have' if len(underloaded) > 1 else 'has'} "
        f"the most headroom ({min_load}). Consider shifting new work toward the latter."
    ), False


def team_allocation_suggestion(db: Session, project: Project) -> dict:
    """Real role gaps on this project's roster, cross-referenced with
    org-wide workload, to suggest who to add and for which role."""
    roster = db.query(ProjectMember).filter(ProjectMember.project_id == project.id).all()
    filled_roles = {m.project_role for m in roster}
    member_ids = {m.user_id for m in roster}
    missing_roles = [r for r in ProjectRole if r not in filled_roles]

    summary = workload_summary(db)
    candidates_by_role = {}
    for role in missing_roles:
        # Employees whose org role matches the missing project role and
        # aren't already on this project, ranked by current workload (ascending).
        eligible = [
            s for s in summary
            if s["user_id"] not in member_ids and s["role"] == role.value
        ]
        eligible.sort(key=lambda s: (s["active_project_count"], s["unavailable_days_next_14"]))
        candidates_by_role[role.value] = eligible[:3]

    prompt = (
        f"Project '{project.name}' ({project.code}) is missing these project roles: "
        f"{[r.value for r in missing_roles]}. Here are real candidate employees ranked by "
        f"current workload for each missing role: {candidates_by_role}. In 2-3 sentences, "
        "recommend who to add and why, in plain language."
    )
    ai_text = _call_gemini(prompt) if missing_roles else None
    ai_generated = bool(ai_text)

    if not ai_text:
        if not missing_roles:
            ai_text = "This project's core roles are all staffed."
        else:
            parts = []
            for role, candidates in candidates_by_role.items():
                if candidates:
                    parts.append(f"for {role.replace('_', ' ')}, {candidates[0]['full_name']} has the lightest current load")
                else:
                    parts.append(f"no available employee currently holds the {role.replace('_', ' ')} org role")
            ai_text = "; ".join(parts) + "."

    return {
        "missing_roles": [r.value for r in missing_roles],
        "candidates_by_role": candidates_by_role,
        "recommendation": ai_text,
        "ai_generated": ai_generated,
    }


def sprint_planning_recommendation(db: Session, project) -> dict:
    """
    AI-assisted sprint planning (spec: analyze previous velocity, team
    capacity, story points, historical completion rate to recommend which
    backlog items should enter the next sprint).

    Every number here is real: velocity from actually-completed sprints,
    backlog items with their actual story points and manual rank. Gemini,
    if configured, only turns those real numbers into a written rationale
    -- the recommended/postponed story lists themselves are always
    computed deterministically, never suggested by the LLM, so the person
    can trust the actual selection regardless of whether Gemini is available.
    """
    from app.models.user_story import UserStory
    from app.models.scrum_enums import StoryStatus
    from app.services import sprint_service

    velocity = sprint_service.get_velocity(db, project.id)
    # No completed sprints yet -> fall back to a conservative default so a
    # first sprint can still be planned, clearly labeled as a default.
    capacity = velocity.average_velocity if velocity.sprints else 20.0
    capacity_is_default = not velocity.sprints

    backlog = (
        db.query(UserStory)
        .filter(UserStory.project_id == project.id, UserStory.sprint_id.is_(None))
        .order_by(UserStory.backlog_rank)
        .all()
    )

    recommended, postponed, needs_estimation = [], [], []
    running_total = 0
    for story in backlog:
        if story.story_points is None:
            needs_estimation.append(story)
            continue
        if running_total + story.story_points <= capacity:
            recommended.append(story)
            running_total += story.story_points
        else:
            postponed.append(story)

    def brief(s):
        return {"key": s.key, "title": s.title, "story_points": s.story_points, "priority": s.priority.value}

    prompt = (
        f"You are an assistant for an Agile project management tool planning the next sprint for "
        f"'{project.name}'. Team velocity is {capacity} story points"
        f"{' (default estimate, no completed sprints yet)' if capacity_is_default else ' (average of past sprints)'}. "
        f"Recommended stories for the next sprint: {[brief(s) for s in recommended]}. "
        f"Postponed due to capacity: {[brief(s) for s in postponed]}. "
        "Write a 2-3 sentence plain-language summary of this sprint plan and any risk worth flagging."
    )
    ai_text = _call_gemini(prompt)
    ai_generated = bool(ai_text)

    if not ai_text:
        ai_text = (
            f"Recommended capacity is {capacity} story points"
            f"{' (default — no completed sprints yet to base this on)' if capacity_is_default else ''}. "
            f"{len(recommended)} item(s) totaling {running_total} points fit within that capacity; "
            f"{len(postponed)} item(s) are recommended to wait for a future sprint."
        )
        if needs_estimation:
            ai_text += f" {len(needs_estimation)} backlog item(s) have no story points yet and were skipped — estimate them before planning."

    return {
        "recommended_capacity": capacity,
        "capacity_is_default": capacity_is_default,
        "recommended_stories": [brief(s) for s in recommended],
        "postponed_stories": [brief(s) for s in postponed],
        "needs_estimation": [brief(s) for s in needs_estimation],
        "recommendation": ai_text,
        "ai_generated": ai_generated,
    }


def task_risk_analysis(db, project) -> dict:
    """
    AI-based task analysis (spec: overdue detection, tasks likely to
    become overdue, excessive workload, priority conflicts).

    Every list here is computed from real task data -- due dates, status,
    estimated vs. actual hours already logged -- never inferred or
    fabricated. Gemini, if configured, only adds a written summary.
    """
    from datetime import date, timedelta
    from app.models.task import Task
    from app.models.task_enums import TaskStatus

    today = date.today()
    soon = today + timedelta(days=2)

    tasks = (
        db.query(Task)
        .filter(Task.project_id == project.id, Task.status != TaskStatus.DONE)
        .all()
    )

    overdue = [t for t in tasks if t.due_date and t.due_date < today]
    at_risk = [
        t for t in tasks
        if t.due_date and today <= t.due_date <= soon and t.status != TaskStatus.DONE
    ]
    over_estimate = [
        t for t in tasks
        if t.estimated_hours and t.actual_hours and t.actual_hours > t.estimated_hours
    ]

    def brief(t):
        return {
            "key": t.key, "title": t.title, "status": t.status.value,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "estimated_hours": t.estimated_hours, "actual_hours": t.actual_hours,
        }

    prompt = (
        f"You are an assistant for an Agile project management tool reviewing task health for "
        f"'{project.name}'. Overdue tasks: {[brief(t) for t in overdue]}. Tasks due within 2 days: "
        f"{[brief(t) for t in at_risk]}. Tasks that have exceeded their time estimate: "
        f"{[brief(t) for t in over_estimate]}. Write a 2-3 sentence plain-language summary of the "
        "biggest risk here and what to do about it."
    )
    ai_text = _call_gemini(prompt)
    ai_generated = bool(ai_text)

    if not ai_text:
        if not overdue and not at_risk and not over_estimate:
            ai_text = "No overdue, at-risk, or over-estimate tasks right now."
        else:
            parts = []
            if overdue:
                parts.append(f"{len(overdue)} task(s) are already overdue")
            if at_risk:
                parts.append(f"{len(at_risk)} task(s) are due within 2 days")
            if over_estimate:
                parts.append(f"{len(over_estimate)} task(s) have exceeded their time estimate")
            ai_text = "; ".join(parts).capitalize() + ". Consider reassigning or extending deadlines where needed."

    return {
        "overdue_tasks": [brief(t) for t in overdue],
        "at_risk_tasks": [brief(t) for t in at_risk],
        "over_estimate_tasks": [brief(t) for t in over_estimate],
        "recommendation": ai_text,
        "ai_generated": ai_generated,
    }


def _title_words(title: str) -> set:
    import re
    return set(re.sub(r"[^a-z0-9\s]", "", title.lower()).split())


def _find_possible_duplicates(bugs) -> list[dict]:
    """Simple, transparent duplicate detection: flags open-bug pairs whose
    titles share a high proportion of words (Jaccard similarity). This is
    a rule-based heuristic, not a trained model -- kept simple and
    explainable on purpose (spec: "clearly separate [fallback] from ML
    predictions")."""
    pairs = []
    for i, a in enumerate(bugs):
        words_a = _title_words(a.title)
        if not words_a:
            continue
        for b in bugs[i + 1:]:
            words_b = _title_words(b.title)
            if not words_b:
                continue
            overlap = len(words_a & words_b) / len(words_a | words_b)
            if overlap >= 0.5:
                pairs.append({"bug_a": a.key, "bug_b": b.key, "title_similarity": round(overlap, 2)})
    return pairs


def quality_risk_analysis(db, project) -> dict:
    """
    AI-based testing & bug-quality insights (spec: bug classification
    support, duplicate detection, testing recommendations, quality risk
    identification). Every figure is computed from real bugs/test cases in
    the database; the risk LEVEL is a transparent, rule-based score
    (explicitly not presented as a trained ML prediction, per the "clearly
    separate fallback from ML" rule) since there isn't yet enough
    historical closed-bug data in a fresh install to train a real model.
    """
    from datetime import datetime
    from app.models.bug import Bug
    from app.models.test_case import TestCase
    from app.models.testing_enums import BugStatus, BugSeverity, TestCaseStatus

    bugs = db.query(Bug).filter(Bug.project_id == project.id).all()
    open_bugs = [b for b in bugs if b.status not in (BugStatus.CLOSED, BugStatus.VERIFIED)]
    critical_open = [b for b in open_bugs if b.severity == BugSeverity.CRITICAL]
    reopened = [b for b in bugs if b.status == BugStatus.REOPENED]

    resolved = [b for b in bugs if b.resolved_at]
    avg_resolution_days = (
        round(sum((b.resolved_at - b.created_at).total_seconds() for b in resolved) / len(resolved) / 86400, 1)
        if resolved else None
    )

    test_cases = db.query(TestCase).filter(TestCase.project_id == project.id).all()
    passed = len([t for t in test_cases if t.status == TestCaseStatus.PASSED])
    failed = len([t for t in test_cases if t.status == TestCaseStatus.FAILED])
    not_run = len([t for t in test_cases if t.status in (TestCaseStatus.DRAFT, TestCaseStatus.READY)])
    pass_rate = round(passed / len(test_cases) * 100, 1) if test_cases else None

    duplicates = _find_possible_duplicates(open_bugs)

    # Transparent fallback risk score (0-100): weighted from real signals.
    # NOT a trained ML model -- see docstring.
    score = 0
    score += min(len(critical_open) * 20, 60)
    score += min(len(reopened) * 10, 20)
    if pass_rate is not None:
        score += max(0, (100 - pass_rate) * 0.2)
    score = min(round(score), 100)
    risk_level = "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW"

    def brief(b):
        return {"key": b.key, "title": b.title, "severity": b.severity.value, "status": b.status.value}

    prompt = (
        f"You are an assistant for an Agile project management tool assessing quality risk for "
        f"'{project.name}'. Open bugs: {len(open_bugs)} ({len(critical_open)} critical). Reopened bugs: "
        f"{len(reopened)}. Test pass rate: {pass_rate}%. Possible duplicate bug pairs: {len(duplicates)}. "
        f"Fallback risk score: {score}/100 ({risk_level}). Write a 2-3 sentence plain-language quality "
        "risk summary and the single biggest thing to address."
    )
    ai_text = _call_gemini(prompt)
    ai_generated = bool(ai_text)

    if not ai_text:
        parts = [f"Quality risk is {risk_level} ({score}/100, rule-based, not an ML prediction)."]
        if critical_open:
            parts.append(f"{len(critical_open)} critical bug(s) are still open.")
        if reopened:
            parts.append(f"{len(reopened)} bug(s) have been reopened.")
        if pass_rate is not None and pass_rate < 80:
            parts.append(f"Test pass rate is {pass_rate}%.")
        if duplicates:
            parts.append(f"{len(duplicates)} pair(s) of open bugs look like possible duplicates.")
        ai_text = " ".join(parts)

    return {
        "risk_level": risk_level,
        "risk_score": score,
        "is_ml_prediction": False,  # always a transparent rule-based score in this build
        "open_bug_count": len(open_bugs),
        "critical_open_bugs": [brief(b) for b in critical_open],
        "reopened_bugs": [brief(b) for b in reopened],
        "avg_resolution_days": avg_resolution_days,
        "test_pass_rate": pass_rate,
        "tests_passed": passed,
        "tests_failed": failed,
        "tests_not_run": not_run,
        "possible_duplicates": duplicates,
        "recommendation": ai_text,
        "ai_generated": ai_generated,
    }



def completion_prediction(db: Session, project) -> dict:
    """Forecast project completion from actual delivery history.

    This is deliberately transparent: the date is calculated from remaining
    story points/tasks and observed completed-sprint velocity. Gemini, when
    available, only explains the forecast; it never chooses the numeric date.
    """
    from datetime import date, timedelta
    from app.models.user_story import UserStory
    from app.models.scrum_enums import StoryStatus, SprintStatus
    from app.models.task import Task
    from app.models.task_enums import TaskStatus
    from app.services import sprint_service

    stories = db.query(UserStory).filter(UserStory.project_id == project.id).all()
    tasks = db.query(Task).filter(Task.project_id == project.id).all()
    completed_points = sum((s.story_points or 0) for s in stories if s.status == StoryStatus.DONE)
    remaining_points = sum((s.story_points or 0) for s in stories if s.status != StoryStatus.DONE and s.story_points is not None)
    unestimated_stories = sum(1 for s in stories if s.status != StoryStatus.DONE and s.story_points is None)

    completed_tasks = sum(1 for t in tasks if t.status == TaskStatus.DONE)
    remaining_tasks = sum(1 for t in tasks if t.status != TaskStatus.DONE)

    velocity = sprint_service.get_velocity(db, project.id)
    historical_velocity = float(velocity.average_velocity or 0) if velocity.sprints else 0.0
    if historical_velocity <= 0:
        # No completed sprint history: use actual remaining task hours when
        # available instead of inventing a story-point velocity.
        remaining_hours = sum((t.estimated_hours or 0) for t in tasks if t.status != TaskStatus.DONE)
        working_days = max(1, round(remaining_hours / 8)) if remaining_hours else max(1, remaining_tasks)
        basis = "task_hours_fallback"
    else:
        working_days = max(1, round((remaining_points or remaining_tasks) / historical_velocity * 10))
        basis = "historical_sprint_velocity"

    # Delivery friction is derived from live signals.
    overdue = [t for t in tasks if t.status != TaskStatus.DONE and t.due_date and t.due_date < date.today()]
    blocked_text = 0
    for t in tasks:
        if t.status != TaskStatus.DONE and (t.actual_hours or 0) > (t.estimated_hours or 0) > 0:
            blocked_text += 1
    risk_factor = min(1.5, 1 + 0.15 * len(overdue) + 0.10 * blocked_text)
    adjusted_days = max(1, round(working_days * risk_factor))
    predicted_date = date.today() + timedelta(days=adjusted_days)

    confidence = "high" if velocity.sprints and len(velocity.sprints) >= 3 else "medium" if velocity.sprints else "low"
    signals = []
    if overdue:
        signals.append(f"{len(overdue)} overdue task(s)")
    if blocked_text:
        signals.append(f"{blocked_text} task(s) above estimate")
    if unestimated_stories:
        signals.append(f"{unestimated_stories} unestimated story(s)")

    prompt = (
        f"Project {project.name} has {remaining_points} remaining story points, "
        f"{remaining_tasks} remaining tasks, historical velocity {historical_velocity}, "
        f"and a transparent forecast date of {predicted_date.isoformat()}. "
        f"Risk signals: {signals or ['none']}. Explain the forecast in 2 short sentences."
    )
    ai_text = _call_gemini(prompt)
    recommendation = ai_text or (
        f"Forecast is {predicted_date.isoformat()} based on {basis.replace('_', ' ')}. "
        + ("Review overdue/over-estimate work before committing to the date." if signals else "Current delivery signals do not require an additional schedule adjustment.")
    )
    return {
        "predicted_completion_date": predicted_date.isoformat(),
        "confidence": confidence,
        "provider": "gemini_explanation" if ai_text else "rule_based_forecast",
        "historical_velocity": round(historical_velocity, 2),
        "completed_story_points": completed_points,
        "remaining_story_points": remaining_points,
        "completed_tasks": completed_tasks,
        "remaining_tasks": remaining_tasks,
        "unestimated_stories": unestimated_stories,
        "overdue_tasks": len(overdue),
        "over_estimate_tasks": blocked_text,
        "signals": signals,
        "recommendation": recommendation,
    }
