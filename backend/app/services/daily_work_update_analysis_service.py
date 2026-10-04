"""
AI analysis service for daily work updates.

Analyzes work updates using:
1. Gemini API (if GEMINI_API_KEY is configured)
2. Rule-based analysis (fallback)

Identifies: completed items, pending items, blockers, risk levels, suggestions
"""
import json
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.daily_work_update import DailyWorkUpdate
from app.models.daily_work_update_analysis import DailyWorkUpdateAnalysis, RiskLevel, AIProvider
from app.models.task import Task
from app.models.user import User
from app.services.audit_service import audit_log


def analyze_daily_update(
    db: Session,
    *,
    user_id: int,
    daily_update: DailyWorkUpdate,
) -> DailyWorkUpdateAnalysis:
    """
    Analyze a daily work update using available AI provider.
    
    Tries Gemini first if API key is configured, falls back to rule-based.
    """
    # Try Gemini if available
    if settings.GEMINI_API_KEY:
        try:
            analysis = _analyze_with_gemini(db, user_id=user_id, daily_update=daily_update)
            return analysis
        except Exception as e:
            # Log error but continue with rule-based fallback
            print(f"Gemini analysis failed: {e}, falling back to rule-based")

    # Fall back to rule-based analysis
    return _analyze_with_rules(db, user_id=user_id, daily_update=daily_update)


def _analyze_with_gemini(
    db: Session,
    *,
    user_id: int,
    daily_update: DailyWorkUpdate,
) -> DailyWorkUpdateAnalysis:
    """Analyze using Google Gemini API."""
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-pro")

    # Prepare context from project/task data
    task_context = _get_task_context(db, daily_update=daily_update)

    prompt = f"""Analyze this employee's daily work update and provide structured JSON analysis.

Employee: User ID {user_id}
Date: {daily_update.date}

Work Update:
- Work Done: {daily_update.work_done or 'N/A'}
- Completed: {daily_update.completed_work or 'N/A'}
- Pending: {daily_update.pending_work or 'N/A'}
- Blockers: {daily_update.blockers or 'N/A'}
- Progress: {daily_update.progress_percentage or 0}%
- Additional Notes: {daily_update.additional_notes or 'N/A'}

Project Context:
{task_context}

Provide analysis as JSON with these fields:
{{
    "summary": "Brief overall summary",
    "completed_items": "Parsed completed items list",
    "pending_items": "Parsed pending items list",
    "detected_blockers": "Any blockers identified",
    "risk_level": "low|medium|high|critical",
    "risk_reason": "Why this risk level?",
    "suggested_progress": 0-100,
    "suggested_actions": "Recommended next steps",
    "task_suggestions": []
}}

Be concise and practical. If blocker is mentioned, risk is at least medium."""

    response = model.generate_content(prompt)
    response_text = response.text

    # Parse JSON from response
    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if not json_match:
        raise ValueError("Could not parse JSON from Gemini response")

    analysis_data = json.loads(json_match.group())

    # Compare the update with the employee's real assigned tasks.
    tasks = db.query(Task).filter(Task.assignee_id == user_id).all()
    work_done = (daily_update.work_done or "").lower()
    completed = (daily_update.completed_work or "").lower()
    pending = (daily_update.pending_work or "").lower()
    blockers_text = (daily_update.blockers or "").lower()
    combined_text = " ".join([work_done, completed, pending, blockers_text])
    task_suggestions = []
    for task in tasks:
        title_tokens = [t for t in re.findall(r"[a-z0-9]+", task.title.lower()) if len(t) > 3]
        if not (task.key.lower() in combined_text or any(tok in combined_text for tok in title_tokens[:4])):
            continue
        suggested = None
        if task.key.lower() in completed or task.title.lower() in completed:
            suggested = "done"
        elif task.key.lower() in pending or task.title.lower() in pending:
            suggested = "in_progress"
        if suggested and suggested != task.status.value:
            task_suggestions.append({
                "task_id": task.id, "task_key": task.key,
                "current_status": task.status.value, "suggested_status": suggested,
            })

    overdue = [t for t in tasks if t.due_date and t.due_date < daily_update.date and t.status.value != "done"]
    risk_value = str(analysis_data.get("risk_level", "low")).lower()
    if overdue and risk_value == "low":
        risk_value = "medium"
    if overdue:
        analysis_data["risk_reason"] = (analysis_data.get("risk_reason") or "") + f" {len(overdue)} assigned task(s) are overdue."
        analysis_data["suggested_actions"] = (analysis_data.get("suggested_actions") or "") + " Review overdue estimates, dependencies, and remaining capacity."
    analysis_data["task_suggestions"] = task_suggestions
    analysis_data["risk_level"] = risk_value

    # Create analysis record
    analysis = DailyWorkUpdateAnalysis(
        daily_update_id=daily_update.id,
        summary=analysis_data.get("summary"),
        completed_items=analysis_data.get("completed_items"),
        pending_items=analysis_data.get("pending_items"),
        detected_blockers=analysis_data.get("detected_blockers"),
        risk_level=analysis_data.get("risk_level", "low"),
        risk_reason=analysis_data.get("risk_reason"),
        suggested_progress=analysis_data.get("suggested_progress"),
        suggested_actions=analysis_data.get("suggested_actions"),
        task_suggestions=json.dumps(analysis_data.get("task_suggestions", [])),
        ai_provider=AIProvider.GEMINI,
        model_version="gemini-1.5-pro",
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # High-risk daily updates become actionable project notifications for
    # project managers/leads, while the existing audit trail remains the
    # source of truth. Avoid duplicate risk alerts for the same update.
    if daily_update.project_id and getattr(analysis.risk_level, "value", str(analysis.risk_level)).lower() in {"high", "critical"}:
        from app.models.project_member import ProjectMember
        from app.models.project_enums import ProjectRole
        from app.models.notification import Notification, NotificationType
        from app.services.notification_service import notify
        recipients = db.query(User).join(ProjectMember, ProjectMember.user_id == User.id).filter(
            ProjectMember.project_id == daily_update.project_id,
            ProjectMember.project_role.in_([
                ProjectRole.PROJECT_MANAGER, ProjectRole.SCRUM_MASTER,
                ProjectRole.TEAM_LEAD,
            ]),
            User.is_active == True,
        ).all()
        for recipient in recipients:
            exists = db.query(Notification).filter(
                Notification.user_id == recipient.id,
                Notification.related_project_id == daily_update.project_id,
                Notification.type == NotificationType.AI_RISK_DETECTED,
                Notification.title == "High-risk daily update detected",
            ).first()
            if not exists:
                notify(
                    db, user=recipient, type=NotificationType.AI_RISK_DETECTED,
                    title="High-risk daily update detected",
                    body=analysis.risk_reason or "Review the employee's daily work update and project context.",
                    related_project_id=daily_update.project_id, also_email=False,
                )

    audit_log(
        db,
        user_id=user_id,
        action="daily_update_analysis_generated",
        entity_type="daily_work_update_analysis",
        entity_id=analysis.id,
        changes={"ai_provider": "gemini"},
    )

    return analysis


def _analyze_with_rules(
    db: Session,
    *,
    user_id: int,
    daily_update: DailyWorkUpdate,
) -> DailyWorkUpdateAnalysis:
    """
    Analyze using rule-based heuristics.
    
    Does not require API key. Simpler but functional analysis.
    """
    # Analyze text content
    work_done = (daily_update.work_done or "").lower()
    completed = (daily_update.completed_work or "").lower()
    pending = (daily_update.pending_work or "").lower()
    blockers_text = (daily_update.blockers or "").lower()

    # Detect completed items
    completed_items = _parse_items(daily_update.completed_work or "")
    pending_items = _parse_items(daily_update.pending_work or "")
    detected_blockers = daily_update.blockers or "No blockers reported"

    # Determine risk level
    risk_level = RiskLevel.LOW
    risk_reason = "No major issues detected"

    if blockers_text:
        risk_level = RiskLevel.MEDIUM
        risk_reason = "Blockers reported"

    if "blocked" in blockers_text or "stuck" in blockers_text or "unable" in blockers_text:
        risk_level = RiskLevel.HIGH
        risk_reason = "Significant blockers preventing progress"

    # Check if progress is low for amount of work
    if daily_update.progress_percentage and daily_update.progress_percentage < 25:
        if risk_level == RiskLevel.LOW:
            risk_level = RiskLevel.MEDIUM
            risk_reason = "Low progress percentage"

    # Prepare summary
    summary = f"Employee completed {len(completed_items)} tasks, {len(pending_items)} pending"
    if blockers_text:
        summary += f", with {risk_level.value} risk due to blockers"

    # Suggested progress: use their reported value or estimate
    suggested_progress = daily_update.progress_percentage or 50

    # Suggested actions
    suggested_actions = []
    if blockers_text:
        suggested_actions.append("Resolve reported blockers before proceeding")
    if len(pending_items) > 5:
        suggested_actions.append("Consider breaking down pending work into smaller tasks")
    if suggested_progress < 30:
        suggested_actions.append("Review task estimates and adjust scope if needed")

    # Compare the update with the employee's real assigned tasks.
    tasks = db.query(Task).filter(Task.assignee_id == user_id).all()
    combined_text = " ".join([work_done, completed, pending, blockers_text])
    task_suggestions = []
    for task in tasks:
        title_tokens = [t for t in re.findall(r"[a-z0-9]+", task.title.lower()) if len(t) > 3]
        matched = task.key.lower() in combined_text or any(tok in combined_text for tok in title_tokens[:4])
        if not matched:
            continue
        suggested = None
        if task.key.lower() in completed or task.title.lower() in completed:
            suggested = "done"
        elif task.key.lower() in pending or task.title.lower() in pending:
            suggested = "in_progress"
        if suggested and suggested != task.status.value:
            task_suggestions.append({"task_id": task.id, "task_key": task.key, "current_status": task.status.value, "suggested_status": suggested})

    # Real project risk signals: overdue tasks + blockers + low progress.
    overdue = [t for t in tasks if t.due_date and t.due_date < daily_update.date and t.status.value != "done"]
    if overdue and risk_level == RiskLevel.LOW:
        risk_level = RiskLevel.MEDIUM
        risk_reason = f"{len(overdue)} assigned task(s) are overdue"
    if overdue:
        suggested_actions.append("Review overdue task estimates, dependencies, and remaining capacity")

    # Compare the update with the employee's real assigned tasks.
    tasks = db.query(Task).filter(Task.assignee_id == user_id).all()
    combined_text = " ".join([work_done, completed, pending, blockers_text])
    task_suggestions = []
    for task in tasks:
        title_tokens = [t for t in re.findall(r"[a-z0-9]+", task.title.lower()) if len(t) > 3]
        matched = task.key.lower() in combined_text or any(tok in combined_text for tok in title_tokens[:4])
        if not matched:
            continue
        suggested = None
        if task.key.lower() in completed or task.title.lower() in completed:
            suggested = "done"
        elif task.key.lower() in pending or task.title.lower() in pending:
            suggested = "in_progress"
        if suggested and suggested != task.status.value:
            task_suggestions.append({"task_id": task.id, "task_key": task.key, "current_status": task.status.value, "suggested_status": suggested})

    # Real project risk signals: overdue tasks + blockers + low progress.
    overdue = [t for t in tasks if t.due_date and t.due_date < daily_update.date and t.status.value != "done"]
    if overdue and risk_level == RiskLevel.LOW:
        risk_level = RiskLevel.MEDIUM
        risk_reason = f"{len(overdue)} assigned task(s) are overdue"
    if overdue:
        suggested_actions.append("Review overdue task estimates, dependencies, and remaining capacity")

    # Create analysis record
    analysis = DailyWorkUpdateAnalysis(
        daily_update_id=daily_update.id,
        summary=summary,
        completed_items=", ".join(completed_items) if completed_items else "None reported",
        pending_items=", ".join(pending_items) if pending_items else "None reported",
        detected_blockers=detected_blockers,
        risk_level=risk_level,
        risk_reason=risk_reason,
        suggested_progress=suggested_progress,
        suggested_actions="; ".join(suggested_actions) if suggested_actions else "Continue current work",
        task_suggestions=json.dumps(task_suggestions),
        ai_provider=AIProvider.RULE_BASED,
        model_version=None,
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    audit_log(
        db,
        user_id=user_id,
        action="daily_update_analysis_generated",
        entity_type="daily_work_update_analysis",
        entity_id=analysis.id,
        changes={"ai_provider": "rule_based"},
    )

    return analysis


def _parse_items(text: str) -> list[str]:
    """Extract items from bullet-point or comma-separated text."""
    if not text:
        return []

    # Try bullet points first
    items = re.findall(r"^[\s\-\*•]+(.+)$", text, re.MULTILINE)
    if items:
        return [item.strip() for item in items if item.strip()]

    # Try comma-separated
    items = [item.strip() for item in text.split(",") if item.strip()]
    if len(items) > 1:
        return items

    # Return as single item
    return [text.strip()] if text.strip() else []


def _get_task_context(db: Session, *, daily_update: DailyWorkUpdate) -> str:
    """Get relevant task/project context for analysis."""
    if not daily_update.project_id:
        return "No project specified"

    from app.models.project import Project

    project = db.query(Project).filter(Project.id == daily_update.project_id).first()
    if not project:
        return "Project not found"

    # Get user's tasks in this project
    tasks = (
        db.query(Task)
        .filter(
            Task.project_id == daily_update.project_id,
            Task.assignee_id == daily_update.user_id,
        )
        .limit(5)
        .all()
    )

    context = f"Project: {project.name}\n"
    if tasks:
        context += "Assigned tasks:\n"
        for task in tasks:
            context += f"  - {task.key}: {task.title} | status={task.status.value} | due={task.due_date} | estimate={task.estimated_hours or 0}h\n"

    return context


def get_analysis_or_create(
    db: Session,
    *,
    user_id: int,
    daily_update: DailyWorkUpdate,
) -> DailyWorkUpdateAnalysis:
    """
    Get existing analysis or create new one if it doesn't exist.
    """
    existing = db.query(DailyWorkUpdateAnalysis).filter(
        DailyWorkUpdateAnalysis.daily_update_id == daily_update.id
    ).first()

    if existing:
        return existing

    return analyze_daily_update(db, user_id=user_id, daily_update=daily_update)
