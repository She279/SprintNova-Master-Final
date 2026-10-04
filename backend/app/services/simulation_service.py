"""Read-only, database-backed what-if simulations."""
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.task_enums import TaskStatus
from app.models.user import User
from app.models.project_member import ProjectMember
from app.models.role import RoleEnum
from app.services import project_service
from app.services.weekly_availability_service import calculate_available_hours


def _risk(utilization: float | None) -> str:
    if utilization is None:
        return "unknown"
    if utilization > 100:
        return "high"
    if utilization >= 85:
        return "medium"
    return "low"


def simulate(db: Session, payload, requester: User) -> dict:
    if payload.scenario == "leave":
        if not payload.user_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Select an employee for the leave simulation")
        employee = db.get(User, payload.user_id)
        if not employee or not employee.is_active:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
        task_query = db.query(Task).filter(Task.assignee_id == employee.id, Task.status != TaskStatus.DONE)
        if payload.project_id:
            project = project_service.get_project_or_404(db, payload.project_id)
            project_service.require_view_access(db, project, requester)
            membership = db.query(ProjectMember).filter(
                ProjectMember.project_id == project.id, ProjectMember.user_id == employee.id,
            ).first()
            if not membership:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Employee is not on the selected project team")
            task_query = task_query.filter(Task.project_id == project.id)
        elif requester.role != RoleEnum.OWNER_ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Select an accessible project for this simulation")
        tasks = task_query.all()
        current = calculate_available_hours(db, user_id=employee.id, from_days=14)["total_available_hours"]
        daily_capacity = current / 14 if current else 0
        predicted = round(max(0, current - min(current, daily_capacity * payload.days)), 2)
        assigned = round(sum(task.estimated_hours or 0 for task in tasks), 2)
        current_utilization = round((assigned / current) * 100, 1) if current else None
        predicted_utilization = round((assigned / predicted) * 100, 1) if predicted else None
        affected = [
            {"id": task.id, "key": task.key, "title": task.title, "due_date": task.due_date}
            for task in tasks
            if not task.due_date or task.due_date <= date.today() + timedelta(days=payload.days + 14)
        ]
        return {
            "scenario": "leave",
            "label": f"{employee.first_name} {employee.last_name} takes {payload.days} day(s) leave",
            "simulation_only": True,
            "current": {"capacity_hours": round(current, 2), "utilization_percent": current_utilization, "risk": _risk(current_utilization)},
            "predicted": {"capacity_hours": predicted, "utilization_percent": predicted_utilization, "risk": _risk(predicted_utilization)},
            "affected_tasks": affected,
            "recommendation": f"Review the {len(affected)} affected task(s) before approving leave. No assignments were changed.",
        }

    if not payload.task_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Select a task for the delay simulation")
    task = db.get(Task, payload.task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    project = project_service.get_project_or_404(db, task.project_id)
    project_service.require_view_access(db, project, requester)
    predicted_due = task.due_date + timedelta(days=payload.days) if task.due_date else None
    return {
        "scenario": "delay",
        "label": f"{task.key} is delayed by {payload.days} day(s)",
        "simulation_only": True,
        "current": {"due_date": task.due_date, "risk": "current"},
        "predicted": {"due_date": predicted_due, "risk": "higher" if task.due_date else "unknown"},
        "affected_tasks": [{"id": task.id, "key": task.key, "title": task.title, "due_date": predicted_due}],
        "recommendation": "Review the task and its project timeline before applying any schedule change. No data was changed.",
    }