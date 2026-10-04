"""Organization-level AI command center data assembled from existing services."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.services import ai_service, project_health_service


def _summary(health: list[dict], workload: list[dict]) -> tuple[str, str]:
    risk_count = sum(len(item["risks"]) for item in health)
    affected_projects = sum(1 for item in health if item["risks"])
    unavailable_days = sum(item["unavailable_days_next_14"] for item in workload)
    prompt = (
        "You are an AI operating assistant for an Agile organization. Summarize this real data in 2-3 concise "
        "sentences for an owner/admin. Mention only the supplied facts, name the most important attention areas, "
        "and do not recommend automatic changes.\n"
        f"Project health: {health}\nTeam workload: {workload}\n"
    )
    ai_text = ai_service._call_gemini(prompt)
    if ai_text:
        return ai_text, "gemini"

    if not health and not workload:
        return "No project or team signals are available yet. Create projects and add employees to begin monitoring organization health.", "rule-based"
    if risk_count:
        return (
            f"{affected_projects} project(s) currently show {risk_count} active risk signal(s). "
            f"The next-14-day workload view contains {unavailable_days} unavailable day(s). Review the signals below before changing plans."
        ), "rule-based"
    return (
        f"No active project risk signals are currently detected across {len(health)} project(s). "
        f"The next-14-day workload view contains {unavailable_days} unavailable day(s); continue monitoring delivery and capacity."
    ), "rule-based"


def get_command_center(db: Session) -> dict:
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    employees = db.query(User).filter(User.is_active == True).count()  # noqa: E712
    health = [project_health_service.build_project_health(db, project) for project in projects]
    workload = ai_service.workload_summary(db)
    summary, provider = _summary(health, workload)

    attention_items = []
    for project in health:
        for risk in project["risks"][:3]:
            attention_items.append({
                "project_id": project["project_id"],
                "project_name": project["project_name"],
                "severity": risk["severity"],
                "title": risk["title"],
                "detail": risk["detail"],
            })
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    attention_items.sort(key=lambda item: severity_order.get(item["severity"], 4))

    health_scores = [item["overall_health"] for item in health]
    return {
        "organization_health": round(sum(health_scores) / len(health_scores)) if health_scores else None,
        "active_employee_count": employees,
        "project_count": len(projects),
        "projects_with_risks": sum(1 for item in health if item["risks"]),
        "attention_items": attention_items[:10],
        "project_health": health,
        "team_workload": workload,
        "summary": summary,
        "provider": provider,
        "generated_at": datetime.utcnow(),
    }