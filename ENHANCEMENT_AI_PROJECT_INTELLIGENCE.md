# SprintNova – AI Project Intelligence Enhancement

This enhancement extends the existing SprintNova application. It does not replace the existing authentication, RBAC, project, Scrum, Kanban, testing, availability, leave, daily-update, notification, RAG, or realtime systems.

## Added / strengthened

- Unified project health now considers:
  - overdue active tasks
  - active sprint progress
  - late milestones
  - open and critical bugs
  - test pass rate
  - upcoming approved leave
  - reduced weekly availability
  - tasks exceeding their estimated hours
  - today's team daily-update coverage
  - active work sessions
- Project Manager and Team Lead dashboards now receive:
  - project health summaries
  - team workload/capacity data
  - advisory workload recommendation
- Admin dashboard now shows organization-wide project health and capacity guidance.
- Existing task-risk, quality-risk, sprint-planning and workload AI services remain the source of AI intelligence; no duplicate AI engine was introduced.
- Dashboard loads use deterministic workload guidance and do not call Gemini repeatedly. Gemini remains available through the dedicated AI endpoint where explicitly requested.
- High/critical daily-update analysis can create a project-scoped `AI_RISK_DETECTED` notification for project managers, Scrum Masters and Team Leads. The existing notification service publishes the notification through the existing realtime channel.
- AI recommendations remain advisory. No task is automatically reassigned or changed by project-health calculations.

## Database

A small Alembic migration adds the `AI_RISK_DETECTED` notification enum value for PostgreSQL. SQLite development remains compatible with the existing schema approach.

## Verification

- Backend `compileall`: passed.
- Migration Python parsing: passed.
- Frontend build: not executed in this environment because `frontend/node_modules` is not installed. Run `npm install` followed by `npm run build` on Windows.
