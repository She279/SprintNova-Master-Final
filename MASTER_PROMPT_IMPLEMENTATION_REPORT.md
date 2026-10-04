# SprintNova — Master Prompt Implementation Report

## Base
This release extends the existing SprintNova architecture. It does not introduce a second authentication, RBAC, notification, audit, project-access, AI, RAG, or database system.

## Implemented capabilities
- JWT authentication, password/OTP flows, login history and audit logging
- Role-aware dashboards for Owner/Admin, Project Manager, Product Owner, Scrum Master, Team Lead, Developer, Tester and Client
- Projects, clients, project members, milestones, roadmaps and templates
- Epics, backlog, user stories, sprint planning, sprint lifecycle, burndown/velocity
- Kanban tasks, comments, history, due dates and risk signals
- Test cases, executions, bugs, severity/priority, regression/retest, code reviews and builds
- Backend work sessions with active-session recovery and duplicate prevention
- Weekly/daily availability and leave-aware capacity
- Daily work updates and structured AI analysis
- AI task suggestions with review/accept/reject workflow and audit trail
- Project risk, workload, quality risk, completion forecasting and sprint planning
- Gemini with rule-based fallback and truthful provider labels
- ChromaDB/RAG with keyword fallback
- Project AI assistant using structured project data + RAG for authorized internal users
- Real-time WebSocket invalidation/events with backend authorization
- Project attachments with size validation and access checks
- Smart notifications and AI-risk notifications
- Real API-driven dashboards and analytics

## Security hardening in this release
- Client accounts cannot access internal project attachments.
- Client accounts cannot access internal project knowledge/RAG documents.
- Client AI assistant responses are restricted to client-visible project status/progress information.
- Client WebSocket connections receive only an allowlisted set of project-progress events; internal task, bug, test, work-session and engineering events are filtered server-side.
- Organization-wide AI workload summary is restricted to Owner/Admin; project-level AI planning remains project-access scoped.
- Project AI planning roles include Project Manager and Team Lead in addition to the existing planning roles.

## Demo seed
The existing `backend/seed_demo_data.py` remains the demo entry point and requires Alembic schema creation first. It creates a realistic E-Commerce Agile scenario with projects, team membership, milestones, epics, stories, sprints, tasks, tests, bugs, code reviews, builds, availability, leave, daily updates, AI analysis and project documents.

The requested five demo contacts are retained in the seed's default team. The project-level roles demonstrate Project Manager and Team Lead through existing project-role mappings without creating a second RBAC system.

## Database rule
Schema creation is owned by Alembic. The seed script explicitly requires migrations and does not call `Base.metadata.create_all()`.

## Verification performed in this environment
- `python -m compileall -q backend/app tests` — passed after the final hardening changes.
- Migration files were parsed/compiled as part of the backend compilation.
- Frontend package structure was inspected.

## Verification limitations
The execution environment used for this packaging pass does not have the project's Python dependencies installed and cannot reach the package index, so a full pytest runtime collection could not be completed here. The failure was environmental (`ModuleNotFoundError: jose`), not a reported application assertion failure. The frontend `node_modules` directory is also absent, so `npm run build` could not be executed here.

On Windows, install the project's locked dependencies from `backend/requirements.txt`, run Alembic, seed the demo database, then run pytest and the frontend production build before the final college demonstration.
