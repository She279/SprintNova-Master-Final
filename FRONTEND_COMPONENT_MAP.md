# Frontend Component Architecture Map

## Component Hierarchy

```
App.jsx
├── BrowserRouter
├── AuthProvider
└── WorkSessionProvider ✨ NEW
    ├── Routes
    ├── ProtectedRoute (login/auth routes)
    ├── ProtectedRoute + AdminLayout (existing /admin/* routes)
    ├── ProtectedRoute + RoleBasedLayout ✨ NEW
    │   ├── RoleBasedRedirect (for "/" route) ✨ NEW
    │   ├── DeveloperDashboard ✨ NEW
    │   ├── TesterDashboard ✨ NEW
    │   ├── ScrumMasterDashboard ✨ NEW
    │   ├── ProjectManagerDashboard ✨ NEW
    │   ├── ProductOwnerDashboard ✨ NEW
    │   ├── TeamLeadDashboard ✨ NEW
    │   └── ClientDashboard ✨ NEW
    │
    └── Routes
        ├── LoginPage (existing)
        ├── ForgotPasswordPage (existing)
        └── ChangePasswordPage (existing)

RoleBasedLayout ✨ NEW
├── Header
│   ├── Logo
│   ├── Role-Specific Navigation
│   ├── WorkSessionTimer ✨ NEW
│   ├── NotificationBell (existing)
│   └── User Menu
└── Main Content Area
    └── <Outlet /> (Dashboard pages)
```

## File Structure

### Context & State Management
```
src/context/
├── AuthContext.jsx (existing)
│   └── useAuth() hook
│       ├── session
│       ├── login()
│       ├── logout()
│       └── isAuthenticated
│
└── WorkSessionContext.jsx ✨ NEW (87 lines)
    ├── WorkSessionProvider
    └── useWorkSession() hook
        ├── workSession
        ├── elapsedSeconds
        ├── isLoading
        ├── startSession()
        ├── stopSession()
        └── isActive
```

### API Modules
```
src/api/
├── client.js (existing - handles auth headers)
├── auth.js (existing)
├── availability.js (existing)
│
├── work-sessions.js ✨ NEW (17 lines)
│   ├── start()
│   ├── getCurrent()
│   ├── stop(sessionId)
│   ├── getTodayTotal()
│   ├── getHistory(limit, skip)
│   └── getCurrentlyWorking()
│
├── weekly-availability.js ✨ NEW (19 lines)
│   ├── setup(schedule)
│   ├── getSchedule()
│   ├── isConfigured()
│   ├── getAvailableHours(days)
│   └── getTeamMemberSchedule(userId)
│
└── daily-work-updates.js ✨ NEW (33 lines)
    ├── create(updateData)
    ├── getTodayUpdate()
    ├── checkPending()
    ├── getHistory(startDate, endDate, limit, skip)
    ├── update(updateId, updateData)
    ├── getAnalysis(updateId)
    ├── triggerAnalysis(updateId)
    └── getTeamUpdates()
```

### Layout Components
```
src/components/layout/
├── AdminLayout.jsx (existing)
│   └── Used for /admin/* routes
│
└── RoleBasedLayout.jsx ✨ NEW (90 lines)
    ├── Header with WorkSessionTimer
    ├── Role-specific navigation menu
    ├── <Outlet /> for page content
    └── Works with 7 role dashboards
```

### UI Components
```
src/components/
├── ProtectedRoute.jsx (existing)
├── NotificationBell.jsx (existing)
│
├── WorkSessionTimer.jsx ✨ NEW (62 lines)
│   ├── Start/Stop buttons
│   ├── Live timer display (HH:MM:SS)
│   ├── Confirmation dialog
│   └── Uses useWorkSession() hook
│
├── AvailabilitySetupModal.jsx ✨ NEW (140 lines)
│   ├── 7-day schedule selector
│   ├── Timezone dropdown
│   ├── Toggle work/off for each day
│   ├── Time picker inputs
│   ├── Error handling
│   └── Submit calls weeklyAvailabilityApi.setup()
│
├── AvailabilityCheckRoute.jsx ✨ NEW (50 lines)
│   ├── Checks isConfigured on mount
│   ├── Shows AvailabilitySetupModal if needed
│   └── Blocks access until setup (unless client)
│
├── RoleBasedRedirect.jsx ✨ NEW (22 lines)
│   ├── Reads session.role
│   └── Navigates to appropriate dashboard
│
└── ui/
    ├── Button.jsx (existing)
    ├── Modal.jsx (existing)
    └── Field.jsx (existing)
```

### Page Components - Dashboards
```
src/pages/
├── admin/ (existing)
├── developer/
│   └── DeveloperDashboard.jsx ✨ NEW (130 lines)
│       ├── Work session timer display
│       ├── Today's work summary
│       ├── Daily update status
│       ├── AI analysis preview
│       ├── Work time stats
│       └── Quick action buttons
│
├── tester/
│   └── TesterDashboard.jsx ✨ NEW (65 lines)
│       ├── Test case status
│       ├── Bug assignments
│       ├── Quality metrics
│       └── Today's summary
│
├── scrum-master/
│   └── ScrumMasterDashboard.jsx ✨ NEW (67 lines)
│       ├── Sprint progress
│       ├── Team status
│       ├── Daily updates count
│       └── Sprint risks
│
├── pm/
│   └── ProjectManagerDashboard.jsx ✨ NEW (59 lines)
│       ├── Active projects
│       ├── Team capacity
│       ├── Milestones
│       └── Team health metrics
│
├── product-owner/
│   └── ProductOwnerDashboard.jsx ✨ NEW (59 lines)
│       ├── Product backlog
│       ├── Release progress
│       ├── Epics
│       └── Sprint planning
│
├── team-lead/
│   └── TeamLeadDashboard.jsx ✨ NEW (59 lines)
│       ├── Team members
│       ├── Workload distribution
│       ├── Task progress
│       └── Active blockers
│
├── client/
│   └── ClientDashboard.jsx ✨ NEW (62 lines)
│       ├── Projects (restricted)
│       ├── Milestones
│       ├── Progress only
│       └── No employee data
│
└── (existing admin pages preserved)
```

---

## Data Flow Diagram

### Initial Load (First Visit)
```
User Login
    ↓
AuthContext.login() → receives JWT + role
    ↓
App stores role in localStorage
    ↓
Navigate to "/"
    ↓
RoleBasedRedirect reads session.role
    ↓
Navigate to /[role]/dashboard
    ↓
AvailabilityCheckRoute checks isConfigured
    ↓
If not configured:
    ├── Show AvailabilitySetupModal
    ├── User sets schedule
    └── POST /api/v1/availability/weekly/setup
                      ↓
                  Success → Close modal
                      ↓
                  Load dashboard
                      ↓
If configured:
    └── Load dashboard immediately
            ↓
        WorkSessionProvider initializes
            ├── GET /api/v1/work-sessions/current
            └── If active session exists:
                    └── Set as active + recover timer

Dashboard Loads
    ├── Component useEffect fires
    ├── Fetches data from APIs:
    │   ├── GET /work-sessions/today-total
    │   ├── GET /daily-updates/me/today
    │   └── [other role-specific endpoints]
    ├── Sets state with response data
    └── Renders with real data
```

### Work Session Flow
```
User clicks "Start Work"
    ↓
WorkSessionTimer → startSession()
    ↓
POST /api/v1/work-sessions/start
    ↓
Backend creates session
    ↓
Response: { id, started_at, status: "active" }
    ↓
WorkSessionContext updates state
    ├── workSession = response
    ├── elapsedSeconds = 0
    └── Start setInterval for timer
            ↓
        Every 1 second:
        └── setElapsedSeconds(prev => prev + 1)
            ↓
        UI shows HH:MM:SS timer

User clicks "Stop"
    ↓
Confirmation dialog
    ↓
If confirmed:
    ├── stopSession()
    ├── POST /api/v1/work-sessions/{id}/stop
    ├── Backend updates session.status = "completed"
    └── WorkSessionContext:
        ├── workSession = null
        ├── elapsedSeconds = 0
        └── Clear setInterval
            ↓
        UI shows "Start Work" button again

Page Refresh During Active Session
    ↓
WorkSessionProvider useEffect on mount
    ├── GET /api/v1/work-sessions/current
    ├── Backend returns active session
    ├── Calculate elapsed: (now - started_at) / 1000
    └── Resume timer from backend elapsed time
            ↓
        User sees correct time, no loss of data
```

### Availability Setup Flow
```
First Login (non-client)
    ↓
AvailabilityCheckRoute mounts
    ├── GET /api/v1/availability/weekly/is-configured
    └── Response: { is_configured: false }
            ↓
        Show AvailabilitySetupModal
                ↓
User enters schedule:
├── Selects days as work/off
├── Sets start/end times per day
└── Selects timezone
        ↓
User clicks "Save Schedule"
    ├── Calls weeklyAvailabilityApi.setup()
    ├── POST /api/v1/availability/weekly/setup
    │   {
    │     timezone: "IST",
    │     schedule: {
    │       monday: { start_time: "09:00", end_time: "17:30" },
    │       ...
    │     }
    │   }
    └── Backend creates/updates weekly_availability records
            ↓
Success
    ├── Close modal
    ├── AvailabilityCheckRoute props onSuccess callback fires
    └── Load dashboard with data
```

---

## Component Dependencies

### WorkSessionTimer Dependencies
- `useWorkSession()` hook
- `workSessionApi.start()`, `.stop()`
- No external UI libraries (uses Tailwind only)

### AvailabilitySetupModal Dependencies
- `weeklyAvailabilityApi.setup()`
- No external validation library (built-in)
- No external date picker (HTML5 time input)

### Dashboard Components Dependencies
- `useAuth()` hook (session data)
- `useWorkSession()` hook (for developer dashboard)
- Various API modules for data fetching
- Tailwind CSS for styling

### RoleBasedLayout Dependencies
- `useAuth()` hook
- `useWorkSession()` hook
- `WorkSessionTimer` component
- `NotificationBell` component (existing)
- Tailwind CSS

---

## External Dependencies
- React 19
- React Router v6+
- Tailwind CSS (already in project)
- Existing AuthContext
- Existing API client (handles JWT)

No additional npm packages were added!

---

## File Creation Summary
✅ **18 new files created** (all in Phase 2)
✅ **1 file modified** (App.jsx - routing + providers)
✅ **0 files deleted**
✅ **No new npm dependencies**

Total new code: ~1,100 lines
Average component size: 60-90 lines (lean & focused)
