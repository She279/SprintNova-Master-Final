# SprintNova Backend — Module 1: Authentication, Company Email & User Account Flow

This is the foundation module of SprintNova. It is fully functional and
tested (see `tests/test_module1_smoke.py`), and is structured so every
future module (Projects, Sprints, Kanban, Bugs, Reports, AI Assistant)
plugs in without modifying this module's code.

## What's implemented

### Module 1 — Authentication, Company Email & User Account Flow
- Admin-only employee creation (RBAC-enforced on the backend, not just hidden UI)
- Automatic, unique company email generation: `first.last@<COMPANY_EMAIL_DOMAIN>`,
  with numeric-suffix collision handling (`arun.kumar@...`, `arun.kumar1@...`, ...)
- Separate `personal_email` (any valid provider) vs `company_email` (login identity)
- Secure temporary password generation, bcrypt hashing, `must_change_password` flag
- Dedicated, provider-agnostic email service (console for dev, SMTP for prod —
  works with Gmail SMTP, SendGrid, Resend, Amazon SES, or any SMTP endpoint)
- JWT login, forced first-login password change
- Forgot-password flow via OTP sent to the *personal* email (hashed, expiring,
  single-use, attempt-limited)
- Login history (success/failure, IP, user agent, timestamp)
- Admin employee management: list, view, activate/deactivate, view login history

### Module 2 — Project & Team Management
- Clients (Owner/Admin + Product Owner can manage)
- Projects with a unique short `code` (e.g. `SN-001`), status, **priority**
  (critical/high/medium/low), **methodology** (scrum/kanban/xp/lean/hybrid),
  dates, and an optional Product Owner (auto-added to the team on creation)
- Team rosters (`ProjectMember`) with a **per-project role** distinct from the
  employee's org-wide role — e.g. someone can be a Tester on one project's
  team even if their employee role is Developer. This is a deliberate
  simplification of a separate `teams`/`team_members` table set: a
  project's roster *is* its team, so there's one place team membership
  lives rather than two tables to keep in sync
- Membership-aware visibility: Owner/Admin sees every project; everyone else
  sees only projects they're a team member on (`list_visible_projects`)
- Management vs. view RBAC: only Owner/Admin, the assigned Product Owner, or
  a Scrum Master on the project's roster can edit it, add/remove team
  members, or manage milestones — enforced with
  `project_service.require_view_access` / `require_manage_access`, not just
  hidden frontend buttons
- Milestones per project (title, due date, status, `phase`, `sort_order`)
- **Project templates** — reusable blueprints with default milestones
  (each with a `phase` and `offset_days`) and suggested project roles;
  applying one creates a project with milestones pre-populated at the
  right dates relative to the project's start date
- **Roadmap** — `/projects/{id}/roadmap` groups milestones by `phase` into
  ordered timeline stages, the same underlying data as the milestone list
- **Project notifications** — an in-app `Notification` table plus email,
  fired automatically on project creation, status changes, team
  members added/removed, milestone status changes, and leave/permission
  decisions (`notification_service.py` is the single trigger point every
  future module should route through)
- **Employee availability** — per-day records (available/partial/
  unavailable + hours), settable by the employee, viewable as a team
  calendar by Owner/Admin, Product Owner, or Scrum Master
- **Leave & Permission tracking** — Leave (full day+) vs. Permission
  (same-day short window) request types, pending → approved/rejected
  workflow; an approved Leave automatically marks the employee
  unavailable for those dates, keeping availability consistent
- **AI-based suggestions** (`ai_service.py`) — workload summary and
  team-allocation suggestions, both computed from real data (actual
  active-project counts, actual roster gaps, actual availability).
  Optionally enriched by Gemini (`GEMINI_API_KEY`) for a written
  recommendation; if no key is set, or the call fails, falls back to a
  rule-based recommendation over the same real numbers — never a
  fabricated prediction
- **Project progress** — `/projects/{id}/progress` reports real
  milestone-completion stats and a completion timeline. This was a
  stand-in for sprint burndown/velocity charts before Module 3 existed;
  now that Sprints are real, prefer `/projects/{id}/sprints/{id}/burndown`
  for anything sprint-scoped and keep this endpoint for overall project
  (not sprint) milestone tracking

### Module 3 — Product Backlog & Sprint Management (Scrum)
- **Epics** and a **backlog** of user stories (`"As a ... I want ... so
  that ..."`), each auto-assigned a Jira-style key (`SN-001-7` = project
  code + sequence)
- Story fields: priority, story points, acceptance criteria, labels,
  status (`backlog → ready → in_sprint → in_progress → done`), a manual
  `backlog_rank` for drag-and-drop reordering independent of priority
- RBAC split matching real Scrum roles: only the **Product Owner** (or
  Admin) can create/edit/reorder/delete backlog items; the **assignee**
  may move their own story's `status` but nothing else; assigning a story
  into/out of a sprint requires PO **or** Scrum Master (sprint planning is
  collaborative); sprint lifecycle (create/start/close/cancel) is the
  **Scrum Master's** (or Admin's) call alone
- **Sprints**: `planned → active → completed/cancelled`. Starting a sprint
  is blocked if the project already has one active. Closing a sprint
  automatically returns any not-Done stories to the backlog (real Scrum
  practice) and notifies the team
- **Real burndown**: `/sprints/{id}/burndown` computes ideal vs. actual
  remaining story points per day from actual story completion timestamps
  — never hardcoded chart values
- **Real velocity**: `/sprints/velocity` averages completed story points
  across a project's actually-completed sprints
- **AI sprint planning** (`ai_service.sprint_planning_recommendation`) —
  greedily fits backlog items (ordered by `backlog_rank`) into the
  project's real average velocity (or a labeled default if no sprints
  have completed yet), producing a deterministic recommended/postponed
  split. Gemini, if configured, only adds a written rationale on top —
  the selection itself is never left to the LLM

### Module 4 — Task & Kanban Management
- **Tasks** with a Jira-style key (`SN-800-T1` = project code + `T` +
  sequence, separate namespace from user story keys), the four Kanban
  columns (`todo → in_progress → testing → done`), priority, due date,
  estimated/actual hours, and optional links to a sprint and/or a user
  story (a story can break down into several tasks, or a task can stand
  alone on a Lean/Kanban board with no Scrum ceremony around it)
- RBAC tuned for how a Kanban board actually gets used: **any** project
  member can create a card and drag it between columns (status is the one
  field open to everyone); editing other fields (title, description,
  priority, due date, estimate, assignee) or deleting a card requires
  being the task's reporter, the Product Owner, the Scrum Master, or an Admin
- **Comments** and a **field-level activity history** (`TaskHistory`) —
  every status/assignee/priority change is logged automatically by
  `task_service.py`, never written by the route handler directly, so it
  can't be bypassed or missed
- Notifications on task assignment, status change, and new comments
- **AI task risk analysis** (`ai_service.task_risk_analysis`) — real
  overdue-task and due-within-2-days detection from actual due dates,
  plus over-time-estimate detection from actual vs. estimated hours
  already logged on the task. Open to any project member, not just
  planning roles, since developers and testers benefit from this as much
  as the Product Owner does

### Module 5 — Testing & Bug Tracking
- **Test cases**: title, steps, expected result, priority, plus a `status`
  (`draft/ready/passed/failed/blocked`) that's *derived* from the most
  recent execution, never hand-set — recording an execution is the only
  way a test case's status changes
- **Test executions**: pass/fail/blocked results with actual-result notes,
  a full history per test case
- **Bugs** with the real Bug/Kanban distinction spelled out in the spec:
  **severity** (critical/major/minor/trivial, how bad the impact is) is
  modeled separately from **priority** (critical/high/medium/low, how
  soon to fix it) — a trivial-severity bug can still be high priority
- Full bug lifecycle (`open → assigned → in_progress → fixed → retesting
  → verified`, with `reopened`/`closed` as well), `resolved_at` set
  automatically when a bug reaches a resolved status and cleared if it's
  reopened
- Bug comments and a field-level activity history, same pattern as Module 4
- **Code reviews** (`pending/approved/changes_requested/rejected`) and
  **builds** (`running/successful/failed`, `finished_at` set automatically
  on completion) — the XP-practice half of this module
- **AI quality risk analysis** (`ai_service.quality_risk_analysis`) — a
  transparent 0-100 rule-based score built from real inputs (open critical
  bugs, reopened-bug count, average resolution time, test pass rate), with
  `is_ml_prediction: false` always returned alongside it so the frontend
  (and anyone reading the API response) can never confuse a rule-based
  score for a trained model's prediction. Also includes **possible
  duplicate bug detection** via title-similarity matching among open bugs
  (difflib-based, not ML) — flagged for a human to confirm, never
  auto-merged

### Module 6 — Reports & Dashboards
- `GET /dashboard` returns a genuinely different shape per role (Admin,
  Product Owner, Scrum Master, Developer, Tester, Client) rather than one
  bloated shared model with mostly-null fields — the role comes from the
  authenticated user's own DB record, never from the request, so nobody
  can request another role's dashboard
- Every number is computed at request time by querying Modules 1-5's own
  tables (or calling their existing service functions, e.g. reusing
  `sprint_service.get_velocity` and `milestone_service.get_progress`
  rather than recomputing that logic) — there is no dashboard-specific
  table that could drift out of sync with reality
- The **Client dashboard** deliberately excludes internal detail: no
  employee names, no assignees, no bug data — only project status,
  percent complete, milestones, and current sprint name/status, per the
  spec's "do not expose internal employee information to clients" rule
- The Scrum Master dashboard's "blocked or stale" task detection is a
  transparent, named heuristic (a task sitting in In Progress or Testing
  for 5+ days without moving) rather than an opaque ML call — simple
  enough to trust, and easy to tune later
- Project-scoped chart-data reports (`/reports/projects/{id}/bug-stats`,
  `/task-completion`, `/testing-progress`) return strictly-typed,
  Chart.js-ready aggregates for any project the caller can view

### Module 7 — AI Assistant & Knowledge Retrieval (ChromaDB/RAG)
- **Project documents** (`ProjectDocument`): requirements, sprint notes,
  guidelines, testing docs — freeform team knowledge, editable by any
  project member, automatically indexed/re-indexed/removed from the
  ChromaDB collection on create/update/delete
- **Real ChromaDB**, not a stub — but with a twist: Chroma's default
  embedding function downloads a ~90MB pretrained model from Hugging
  Face on first use, which silently fails in any offline or locked-down
  environment. `app/services/embeddings.py`'s `HashingEmbeddingFunction`
  is a from-scratch, dependency-free, fully offline embedding: light
  stemming + hashed bag-of-words + L2 normalization, giving ChromaDB's
  real cosine-similarity search a genuine (if not state-of-the-art)
  notion of document similarity with zero network calls. Verified live:
  asking about "refunds for payments" correctly retrieves a doc titled
  "payment module... refunds" over an unrelated sprint note. Swap in a
  real embedding model in production for stronger semantic matching —
  this is a one-line change in `rag_service.py`
- **Graceful degradation**: if Chroma is unavailable for any reason, `rag_service.search`
  falls back to a real (not fake) keyword-overlap search directly over
  the `project_documents` table, and always reports which method was
  used (`retrieval_method: "vector" | "keyword" | "none"`) rather than
  silently misrepresenting keyword search as semantic search
- **AI assistant** (`assistant_service.answer_question`) answers natural-
  language questions (the exact examples from the spec: "which tasks are
  overdue", "is the project at risk", "what should we prioritize",
  "who's available") by gathering real structured context from Modules
  2-6's own functions first, retrieving relevant documents second, then
  either using Gemini (if configured) or a keyword-intent-matched
  deterministic fallback — never a fabricated answer. Document sources
  are only ever attached to the response when they actually informed the
  answer (verified live: an intent-matched real-data answer returns
  `sources: []`, not leftover retrieved docs that were never used)

## Quick start (local, SQLite, zero setup)

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt --break-system-packages
alembic upgrade head                # applies the migration history
python create_first_admin.py        # interactive: creates the first Owner/Admin
uvicorn app.main:app --reload
```

## Demo data (recommended for a first look)

Instead of starting from an empty workspace, seed the full
"E-Commerce Web Application" scenario from the spec:

```bash
python seed_demo_data.py            # refuses to run if data already exists
python seed_demo_data.py --force    # wipe and reseed
```

This creates 9 people across all six roles, a client, two projects, epics,
a prioritised backlog, one completed and one active sprint, Kanban tasks
across all four columns, test cases with executions, bugs at every
lifecycle stage, code reviews, builds, a milestone roadmap, availability
and leave records, and five project documents indexed into ChromaDB for
the AI assistant. Every login is printed at the end (all share the
password `SprintNova1!`).

Seeding goes through the real service layer wherever one exists, so the
result is indistinguishable from data entered through the UI — generated
company emails, hashed passwords, notification fan-out and vector
indexing all happen exactly as they would in normal use.

API docs: http://127.0.0.1:8000/docs

## Database migrations (Alembic)

Schema changes go through Alembic, not `Base.metadata.create_all()` — the
`create_all()` call in `main.py`'s startup hook is a local/demo convenience
only (safe to leave in since it's a no-op once tables already exist via
migrations), never the production migration strategy.

```bash
alembic upgrade head                          # apply all pending migrations
alembic revision --autogenerate -m "message"  # generate a new migration after changing models
alembic downgrade -1                          # roll back one migration
```

`migrations/env.py` reads `DATABASE_URL` from the same `app.core.config.settings`
every other part of the app uses, so there's one source of truth — switching
`DATABASE_URL` from SQLite to PostgreSQL in `.env` is all that's needed to
target either database.

## Quick start (Docker + PostgreSQL 17)

```bash
cd backend
docker compose up --build
# then, in another shell, exec into the backend container:
docker compose exec backend alembic upgrade head
docker compose exec backend python create_first_admin.py
```

## Running tests

```bash
pip install pytest httpx --break-system-packages
pytest -q
```

## Configuration

Everything sensitive or environment-specific is read from `.env`
(see `.env.example`) — nothing is hardcoded:

- `DATABASE_URL` — PostgreSQL in prod, SQLite for local/demo
- `COMPANY_EMAIL_DOMAIN` — the domain used for generated company emails
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `EMAIL_PROVIDER` (`console` | `smtp`) + `SMTP_*` credentials
- `OTP_LENGTH`, `OTP_EXPIRE_MINUTES`, `OTP_MAX_ATTEMPTS`
- `TEMP_PASSWORD_LENGTH`
- `GEMINI_API_KEY`, `GEMINI_MODEL` — optional; AI suggestion endpoints work
  with real computed data and a rule-based recommendation even if unset
- `CHROMA_PERSIST_DIR` — where the ChromaDB collections live on disk
  (default `./chroma_data`); delete this directory and call the reindex
  path (`rag_service.reindex_project`) to rebuild from `project_documents`

## Project layout

```
app/
  core/
    config.py       # Settings loaded from env — import `settings` everywhere
    database.py      # SQLAlchemy engine/session, Base, get_db()
    security.py       # password hashing + JWT issue/verify
  models/
    role.py           # RoleEnum (RBAC roles) — import in every module
    user.py           # users table — the identity every module references
    login_history.py, otp.py                                    # Module 1
    client.py, project.py, project_member.py, milestone.py,     # Module 2
    project_template.py, notification.py, availability.py, leave.py
    scrum_enums.py, epic.py, sprint.py, user_story.py            # Module 3
    task_enums.py, task.py, task_comment.py, task_history.py     # Module 4
    testing_enums.py, test_case.py, test_execution.py,            # Module 5
    bug.py, bug_comment.py, bug_history.py, code_review.py, build.py
    project_document.py                                           # Module 7
    __init__.py        # <- add new module model imports here
  schemas/
    user.py, auth.py                                            # Module 1
    client.py, project.py, project_template.py, notification.py,  # Module 2
    availability.py, leave.py, ai.py
    epic.py, user_story.py, sprint.py                            # Module 3
    task.py                                                      # Module 4
    test_case.py, bug.py, code_review.py, build.py                # Module 5
    dashboard.py                                                  # Module 6 (no new models -- read-only over Modules 1-5)
    document.py, assistant.py                                     # Module 7
  services/
    email_service.py    # ALL outbound email goes through this — reuse it
    notification_service.py   # single trigger point for in-app + email notifications
    employee_service.py, auth_service.py                        # Module 1
    client_service.py, project_service.py, project_member_service.py,
    milestone_service.py, project_template_service.py,          # Module 2
    availability_service.py, leave_service.py, ai_service.py
    epic_service.py, backlog_service.py, sprint_service.py       # Module 3
    task_service.py                                              # Module 4
    testcase_service.py, bug_service.py,                          # Module 5
    code_review_service.py, build_service.py
    dashboard_service.py                                          # Module 6
    embeddings.py, rag_service.py, document_service.py,           # Module 7
    assistant_service.py
  api/
    deps.py             # get_current_user, require_role() — reuse in every module
    v1/
      router.py         # <- single attachment point for every module's routes
      endpoints/
        auth.py, employees.py           # Module 1
        clients.py, projects.py, project_templates.py, notifications.py,
        availability.py, leave.py, ai_assistant.py                # Module 2
        epics.py, backlog.py, sprints.py                          # Module 3
        tasks.py                                                  # Module 4
        test_cases.py, bugs.py, code_reviews.py, builds.py        # Module 5
        dashboard.py                                               # Module 6
        documents.py, assistant.py                                 # Module 7
  main.py
create_first_admin.py
tests/
  test_module1_smoke.py   # covers Modules 1-7 end-to-end flows
```

## How to attach the next module (e.g. Projects)

1. Add your model(s) in `app/models/project.py`, then register them in
   `app/models/__init__.py`:
   ```python
   from app.models.project import Project  # noqa: F401
   ```
2. Add your Pydantic schemas in `app/schemas/project.py`.
3. Add your business logic in `app/services/project_service.py`.
4. Add your routes in `app/api/v1/endpoints/projects.py`, protecting them
   with the shared RBAC dependency:
   ```python
   from app.api.deps import require_role
   from app.models.role import RoleEnum

   @router.post("/projects")
   def create_project(
       payload: ProjectCreateRequest,
       user: User = Depends(require_role(RoleEnum.PRODUCT_OWNER, RoleEnum.OWNER_ADMIN)),
   ):
       ...
   ```
5. Register the router in `app/api/v1/router.py` (one line):
   ```python
   from app.api.v1.endpoints import projects
   api_router.include_router(projects.router)
   ```

No other file needs to change. `main.py` never imports individual module
routers directly — only `api_router` from `router.py`.

Module 2 (`clients.py`, `projects.py`) was built following exactly these
five steps, and required zero changes to any Module 1 file — proof the
attachment pattern holds in practice, not just in theory.

## Security notes already baked in

- Passwords are never stored or returned in plain text — only bcrypt hashes.
- OTPs are hashed at rest, expire, are single-use, and are attempt-limited.
- RBAC is enforced with a FastAPI dependency on every protected route, not
  just hidden frontend buttons.
- The forgot-password endpoint returns an identical response whether or not
  the account exists, to prevent account enumeration.
- CORS in `main.py` is wide open (`*`) for local development — tighten
  `allow_origins` to the real frontend URL before deploying.
- `Base.metadata.create_all()` in `main.py` is for local/demo use only;
  use Alembic migrations in production.

## Realtime API

Authenticated clients can connect to:

`ws://127.0.0.1:8000/api/v1/realtime/ws?token=<JWT>`

For project collaboration, include `project_id=<PROJECT_ID>`. The backend validates the JWT and project membership before accepting a project-scoped stream. Realtime messages are event notifications only; REST/database state remains authoritative.
