"""
Single attachment point for every SprintNova module's API routes.

MODULE 1 (this build) registers `auth` and `employees` below.

Every future module follows the exact same pattern -- create its router in
`app/api/v1/endpoints/<module>.py`, protect its routes with
`app.api.deps.require_role` / `get_current_user`, then add ONE line here:

    from app.api.v1.endpoints import projects
    api_router.include_router(projects.router)

    from app.api.v1.endpoints import sprints
    api_router.include_router(sprints.router)

    from app.api.v1.endpoints import kanban
    api_router.include_router(kanban.router)

    from app.api.v1.endpoints import bugs
    api_router.include_router(bugs.router)

    from app.api.v1.endpoints import reports
    api_router.include_router(reports.router)

    from app.api.v1.endpoints import ai_assistant
    api_router.include_router(ai_assistant.router)

No other file needs to change to attach a new module -- main.py only ever
imports `api_router` from this file.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, employees, clients, projects, project_templates, notifications, availability, leave, ai_assistant,
    epics, backlog, sprints, tasks, test_cases, bugs, code_reviews, builds, dashboard,
    documents, assistant, attachments, work_sessions, weekly_availability, daily_work_updates, realtime,
)

api_router = APIRouter(prefix="/api/v1")

# --- Module 1: Authentication, Company Email & User Account Flow ---
api_router.include_router(auth.router)
api_router.include_router(employees.router)

# --- Module 2: Project & Team Management ---
api_router.include_router(clients.router)
api_router.include_router(projects.router)
api_router.include_router(project_templates.router)
api_router.include_router(notifications.router)
api_router.include_router(availability.router)
api_router.include_router(leave.router)
api_router.include_router(ai_assistant.router)

# --- Employee Workspace: Work Sessions, Weekly Availability, Daily Updates ---
api_router.include_router(work_sessions.router)
api_router.include_router(weekly_availability.router)
api_router.include_router(daily_work_updates.router)
api_router.include_router(realtime.router)

# --- Module 3: Product Backlog & Sprint Management (Scrum) ---
api_router.include_router(epics.router)
api_router.include_router(backlog.router)
api_router.include_router(sprints.router)

# --- Module 4: Task & Kanban Management ---
api_router.include_router(tasks.router)

# --- Module 5: Testing & Bug Tracking ---
api_router.include_router(test_cases.router)
api_router.include_router(bugs.router)
api_router.include_router(code_reviews.router)
api_router.include_router(builds.router)

# --- Module 6: Reports & Dashboards ---
api_router.include_router(dashboard.router)

# --- Module 7: AI Assistant & Knowledge Retrieval (ChromaDB/RAG) ---
api_router.include_router(documents.router)
api_router.include_router(attachments.router)
api_router.include_router(assistant.router)

# --- Future modules attach here -- see docstring above for the exact pattern. ---
