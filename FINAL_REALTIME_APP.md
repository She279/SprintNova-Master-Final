# SprintNova — Final Real-Time Agile Project Management App

SprintNova is a role-aware Agile project management platform built on the existing architecture.
It combines Scrum, Kanban, project/team management, work sessions, availability/leave, testing,
bugs, code reviews, builds, real-time events, notifications, AI project intelligence and RAG.

## Demo organisation

One default project team is seeded with the five supplied personal/contact emails:

| Contact email | Org role | Project role | SprintNova login |
|---|---|---|---|
| 24suca27@tcarts.in | Owner/Admin | Project Manager | sprintnova.admin@sprintnova.com |
| dharsini1229@gmail.com | Product Owner | Product Owner | dharsini.m@sprintnova.com |
| rajilakshimi75@gmail.com | Scrum Master | Scrum Master | rajilakshimi.team@sprintnova.com |
| 24suca45@tcarts.in | Developer | Team Lead | developer.user@sprintnova.com |
| 24suca38@tcarts.in | Tester | Tester | tester.user@sprintnova.com |

Demo password for all five accounts: `SprintNova1!`

The contact emails remain the supplied personal/contact identities. The application continues to
use the company-email login policy (`@sprintnova.com`).

## Demo project

**ECOM — E-Commerce Web Application**

Seeded data includes:

- 5-person project team
- milestones and roadmap
- 3 epics
- 10 prioritized user stories/backlog items
- completed Sprint 1
- active Sprint 2
- 7 Kanban tasks across Done / In Progress / Testing / To Do
- task comments
- 6 test cases and 5 executions
- 5 bugs across severity/status combinations
- 3 code reviews
- 4 build records
- weekly availability and daily availability
- pending and approved leave examples
- daily work updates and stored AI analyses
- completed work session
- 5 RAG project documents
- project file attachment
- AI project health/risk signals
- workload analysis
- sprint planning recommendation
- task-risk and quality-risk analysis
- completion-date forecast
- authenticated real-time WebSocket events

## Setup

From `backend`:

```cmd
alembic upgrade head
python seed_demo_data.py --force
python -m uvicorn app.main:app --reload
```

From `frontend`:

```cmd
npm install
npm run dev
```

The backend is normally at `http://127.0.0.1:8000` and the Vite frontend at
`http://127.0.0.1:5173`.

## Database rule

Alembic is the schema source of truth. The demo seed does **not** call
`Base.metadata.create_all()`.

## AI rule

Numeric project intelligence is calculated from real SprintNova database data first.
Gemini, when configured, is used for explanations/recommendations and gracefully falls back to
transparent rule-based analysis when unavailable.

## Real-time rule

WebSockets deliver invalidation/events only. REST/database APIs remain authoritative.
Project events are delivered to a project subscriber or to a global workspace subscriber only when
that user is authorized for the project.

## Main feature areas

1. Authentication and RBAC
2. Project and team management
3. Scrum backlog, epics, stories and sprints
4. Kanban/task execution
5. Testing, bugs, code reviews and builds
6. Role-specific dashboards
7. Work sessions and availability/leave
8. Daily work reporting and AI analysis
9. Project health and completion forecasting
10. Workload and sprint-planning intelligence
11. ChromaDB/RAG project knowledge
12. Natural-language project assistant
13. Notifications and real-time events
14. Authenticated project file attachments
15. Audit logging and access control
