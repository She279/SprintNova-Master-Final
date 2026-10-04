# SprintNova Frontend — Modules 1 & 2

React 19 + Vite + Tailwind frontend covering Module 1 (Authentication,
Company Email & User Account flow) and Module 2 (Project & Team
Management). Talks to the FastAPI backend.

## Design direction

Built as an engineering console, not a marketing site — dark ink + cobalt
accent, Space Grotesk for display type, Inter for body, IBM Plex Mono for
anything identity-shaped (emails, employee IDs, OTP codes). The signature
moment is the **email assembly line** on the Create Employee screen: as the
admin types a name, the generated `first.last@sprintnova.com` address
builds itself character by character, making the product's core mechanic
(automatic company-email generation) visible rather than an invisible
backend detail.

## Quick start

```bash
cd frontend
cp .env.example .env      # point VITE_API_BASE_URL at your backend
npm install
npm run dev
```

Make sure the backend is running first (see `backend/README.md`) and
that you've bootstrapped an Owner/Admin with `python create_first_admin.py`.

## What's implemented

**Module 1**
- `/login` — sign in with company email + password
- `/change-password` — forced first-login password change (temp → permanent)
- `/forgot-password` — 3-step guided flow: request OTP → verify OTP → set new password
- `/admin/employees` — employee list, activate/deactivate
- `/admin/employees/new` — create employee with live company-email preview
- `/admin/employees/:id` — employee detail + login history

**Module 2**
- `/admin/projects` — project cards (only the ones you're a team member on;
  Admins see every project)
- `/admin/projects/new` — create a project, optionally linking a client and
  a Product Owner (auto-added to the team)
- `/admin/projects/:id` — tabbed detail view: Overview (status + progress
  chart), Team (add/remove members with a per-project role), Backlog,
  Sprints, Milestones (add + update status), Roadmap (milestones grouped
  by phase as a timeline), AI Suggestions (team-allocation + sprint-planning
  recommendations)
- `/admin/templates` — create reusable project templates (default
  milestones + suggested roles) and apply one to spin up a new project
  with milestones pre-populated
- `/admin/leave` — submit a Leave or Permission request; Owner/Admin and
  Scrum Master get a "Team requests" tab to approve/reject
- `/admin/availability` — set your own day-by-day availability; Owner/Admin,
  Product Owner, and Scrum Master also see a team availability view
- `/admin/workload` — AI-assisted workload summary across the whole team,
  labeled as Gemini-generated or rule-based depending on whether
  `GEMINI_API_KEY` is configured on the backend
- A notification bell in the header (in `AdminLayout`) shows in-app
  notifications fired by project/team/milestone/leave events, with
  mark-read / mark-all-read

**Module 3**
- **Backlog tab** — create user stories ("As a ... I want ... so that
  ..."), set priority/points/acceptance criteria/epic/assignee, drag to
  reorder (native HTML5 drag-and-drop, no extra library), move a story
  into a planned/active sprint. Only the Product Owner (or Admin) sees the
  management controls; everyone else can still update a story's status
  (the backend enforces the assignee-or-PO rule regardless of what the
  UI shows)
- **Sprints tab** — velocity chart (hand-rolled SVG bar chart, real
  completed-points-per-sprint data) plus the sprint list with
  start/close/cancel actions, visible to Owner/Admin and Scrum Master
- **Sprint detail page** (`/admin/projects/:id/sprints/:sprintId`) — real
  burndown chart (hand-rolled SVG, ideal vs. actual remaining points from
  real story-completion timestamps) and the sprint's story list with
  inline status updates
- **AI Suggestions tab** now also shows a sprint-planning recommendation:
  which backlog items fit the project's real average velocity (or a
  labeled default capacity if no sprint has completed yet), which are
  postponed, and which still need story points before they can be planned

**Module 4**
- **Kanban tab** — a real four-column board (To Do / In Progress / Testing
  / Done) with native HTML5 drag-and-drop (no extra library), priority
  badges, overdue highlighting on the due date, and an assignee avatar
  (initials) per card
- Clicking a card opens a **task detail modal** (built on a new reusable
  `Modal` component) with inline editing for status/priority/assignee/
  actual-hours, a comment thread, and the field-level activity history —
  all backed by real endpoints, not local-only state
- **AI Suggestions tab** gained a "Task risk" section: real overdue and
  due-within-2-days detection, plus tasks that have run over their time
  estimate, using the same real-data-first + optional-Gemini pattern as
  every other AI section

**Module 5**
- **Testing tab** — create test cases, then record pass/fail/blocked
  executions inline (each row expands to an execution form + history);
  the test case's status badge always reflects its most recent execution,
  never hand-set
- **Bugs tab** — a filterable bug table with an inline status dropdown per
  row for quick lifecycle moves, severity and priority shown as separate
  badges (they mean different things: how bad vs. how soon), and a bug
  detail modal (comments + activity history) reusing the same `Modal`
  pattern as the Kanban task modal
- **Quality tab** — code reviews (request → approve/reject) and build
  status (trigger → pass/fail) side by side, the XP-practice half of this
  module
- **AI Suggestions tab** gained a "Quality risk" section: a 0-100 score
  labeled explicitly as rule-based (never mislabeled as an ML prediction),
  critical open bugs, reopened bugs, test pass rate, average resolution
  time, and possible-duplicate-bug pairs flagged by title similarity

**Module 6**
- `/admin/dashboard` — the app's landing page (`/` redirects here). Fetches
  one endpoint (`/api/v1/dashboard`) that returns whichever shape matches
  the signed-in user's actual role, and renders a genuinely different
  layout per role rather than one generic page with sections hidden by role
- **Chart.js** (via `react-chartjs-2`) makes its first appearance here: a
  doughnut chart for project status distribution and a bar chart for
  employee workload on the Admin dashboard, both driven entirely by the
  real numbers the backend returns — `components/charts/chartSetup.js`
  registers the Chart.js building blocks once and exports the app's chart
  color palette so every future chart stays visually consistent
- The **Client dashboard** renders only project-level cards (progress bar,
  current sprint, milestones) — no employee names, no assignees, matching
  the backend's deliberate exclusion of internal detail for that role
- Every list/chart has a real empty state (`EmptyChart`, plain "no data
  yet" text) rather than rendering broken or misleading placeholders when
  a brand-new org has no data yet

**Module 7**
- **Documents tab** — add/expand/delete project knowledge (requirements,
  sprint notes, guidelines, testing docs); any project member can
  contribute, matching the backend's shared-knowledge-base design
- **Assistant tab** — a lightweight chat UI with one-tap suggested
  questions (the exact examples from the spec: "which tasks are
  overdue", "is the project at risk", etc.). Each answer bubble is
  labeled Gemini vs. rule-based and shows which retrieval method was
  used (vector / keyword / none) — and only shows source documents when
  they actually informed that specific answer, never leftover retrieved
  docs the answer didn't use

All routes are guarded client-side by `ProtectedRoute` (redirects to
`/login` if unauthenticated, or to `/change-password` if the forced
password change hasn't happened yet) — but remember the backend enforces
the same rules independently via RBAC, since frontend guards alone are
never sufficient.

## Project layout & how future modules attach

```
src/
  api/
    client.js        # shared fetch wrapper (auth header, base URL, errors)
    auth.js, employees.js       # Module 1
    clients.js, projects.js, projectTemplates.js, notifications.js,
    availability.js, leave.js, ai.js                              # Module 2
    epics.js, backlog.js, sprints.js                              # Module 3
    tasks.js                                                       # Module 4
    testCases.js, bugs.js, quality.js                              # Module 5
    dashboard.js                                                   # Module 6
    documents.js, assistant.js                                     # Module 7
                        # <- future modules add reports.js here
  context/
    AuthContext.jsx    # session state used by every module
  components/
    ui/                # Button, Field/Input/Select, Badge/Alert, Tabs, Modal — reuse these everywhere
    layout/
      AuthShell.jsx      # split-panel shell for auth screens
      AdminLayout.jsx    # top bar + nav — add a NavLink here per new module
    NotificationBell.jsx, ProjectProgressChart.jsx, EmailAssemblyLine.jsx
    BurndownChart.jsx, VelocityChart.jsx                          # Module 3
    charts/chartSetup.js                                          # Module 6 -- Chart.js registration + shared color palette
    ProtectedRoute.jsx
  pages/
    LoginPage.jsx, ChangePasswordPage.jsx, ForgotPasswordPage.jsx
    admin/
      dashboard/DashboardPage.jsx                                              # Module 6
      EmployeesListPage.jsx, CreateEmployeePage.jsx, EmployeeDetailPage.jsx   # Module 1
      projects/
        ProjectsListPage.jsx, CreateProjectPage.jsx, ProjectDetailPage.jsx     # Module 2
        BacklogTab.jsx, SprintsTab.jsx, SprintDetailPage.jsx                   # Module 3
        KanbanBoard.jsx                                                        # Module 4
        TestingTab.jsx, BugsTab.jsx, QualityTab.jsx                            # Module 5
        DocumentsTab.jsx, AssistantTab.jsx                                     # Module 7
      templates/ProjectTemplatesPage.jsx
      leave/LeaveRequestsPage.jsx
      availability/AvailabilityPage.jsx
      workload/WorkloadPage.jsx
                        # <- future modules add pages/admin/reports/, etc.
  App.jsx               # <- single route tree; add new <Route> entries here
```

To attach a new module (e.g. Sprints):

1. Add `src/api/sprints.js` following the pattern in `projects.js`.
2. Add page components under `src/pages/admin/sprints/`.
3. Add a `NavLink` to `AdminLayout.jsx`.
4. Add `<Route>` entries inside the existing `<Route element={<ProtectedRoute />}>`
   block in `App.jsx` — no other file needs to change.

Module 2 was built entirely following these four steps, page by page and
feature by feature, and required zero changes to any Module 1 component.
`ProjectProgressChart` (a small hand-rolled SVG chart) and `NotificationBell`
are the only genuinely new pieces of UI machinery it introduced — both are
reusable by future modules too.

## Environment variables

- `VITE_API_BASE_URL` — URL of the FastAPI backend (default `http://127.0.0.1:8000`)

## Realtime UI

The frontend connects to the SprintNova authenticated WebSocket stream after login, refreshes affected views when Agile events arrive, and automatically reconnects after temporary network loss. Set `VITE_API_BASE_URL` to the backend origin.
