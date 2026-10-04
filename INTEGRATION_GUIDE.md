# Integration Guide: Adding Employee Workspace Features to SprintNova

This guide explains how to merge the new Employee Workspace feature into your existing SprintNova project.

---

## OVERVIEW

Your existing project has:
- ✅ Modules 1-7 (auth, projects, sprints, tasks, testing, dashboards, AI assistant)
- ✅ 50+ existing endpoints
- ✅ Complete database schema
- ✅ Frontend with React 19, Vite, Tailwind

**New feature adds:**
- 5 new database models (work_sessions, weekly_availability, daily_work_updates, analysis, audit_logs)
- 5 new services with business logic
- 20 new API endpoints (organized in 3 routers)
- 8 role-based dashboards
- 7 new/enhanced React components
- 1 Alembic migration

---

## INTEGRATION STEPS

### STEP 1: BACKEND - Add New Models

**Location:** `/backend/app/models/`

Copy these 5 new files:
```
✓ work_session.py
✓ weekly_availability.py
✓ daily_work_update.py
✓ daily_work_update_analysis.py
✓ audit_log.py
```

**Then update:** `/backend/app/models/__init__.py`

Add these imports:
```python
from .work_session import WorkSession
from .weekly_availability import WeeklyAvailability
from .daily_work_update import DailyWorkUpdate
from .daily_work_update_analysis import DailyWorkUpdateAnalysis
from .audit_log import AuditLog
```

Add to `__all__` list:
```python
"WorkSession",
"WeeklyAvailability",
"DailyWorkUpdate",
"DailyWorkUpdateAnalysis",
"AuditLog",
```

---

### STEP 2: BACKEND - Add New Services

**Location:** `/backend/app/services/`

Copy these 5 new files:
```
✓ work_session_service.py
✓ weekly_availability_service.py
✓ daily_work_update_service.py
✓ daily_work_update_analysis_service.py
✓ audit_service.py
```

No changes needed to `__init__.py` (these are imported directly where needed).

---

### STEP 3: BACKEND - Add Pydantic Schemas

**Location:** `/backend/app/schemas/`

Copy these 4 new files:
```
✓ work_session.py
✓ weekly_availability.py
✓ daily_work_update.py
✓ daily_work_update_analysis.py
```

**Then update:** `/backend/app/schemas/__init__.py`

Add these imports (follow existing pattern):
```python
from .work_session import (
    WorkSessionResponse,
    WorkSessionDetailResponse,
)
from .weekly_availability import (
    WeeklyScheduleSetup,
    FullWeeklyScheduleResponse,
)
from .daily_work_update import (
    DailyWorkUpdateCreate,
    DailyWorkUpdateUpdate,
    DailyWorkUpdateDetailResponse,
)
from .daily_work_update_analysis import DailyWorkUpdateAnalysisResponse
```

---

### STEP 4: BACKEND - Add API Endpoints

**Location:** `/backend/app/api/v1/endpoints/`

Copy these 3 new files:
```
✓ work_sessions.py
✓ weekly_availability.py
✓ daily_work_updates.py
```

**Then update:** `/backend/app/api/v1/router.py`

Add these import statements:
```python
from .endpoints.work_sessions import router as work_sessions_router
from .endpoints.weekly_availability import router as weekly_availability_router
from .endpoints.daily_work_updates import router as daily_work_updates_router
```

Add these includes (follow existing pattern):
```python
router.include_router(work_sessions_router, prefix="/work-sessions", tags=["work-sessions"])
router.include_router(weekly_availability_router, prefix="/availability/weekly", tags=["availability"])
router.include_router(daily_work_updates_router, prefix="/daily-updates", tags=["daily-updates"])
```

---

### STEP 5: DATABASE - Add Migration

**Location:** `/backend/migrations/versions/`

Copy this file:
```
✓ add_employee_workspace_tables.py
```

**Run migration:**
```bash
cd /backend
alembic upgrade head
```

This will create all 5 new tables with proper indexes and foreign keys.

---

### STEP 6: FRONTEND - Add Core Components

**Location:** `/frontend/src/components/`

Copy these 2 NEW files:
```
✓ DailyUpdateForm.jsx
✓ AnalysisDisplay.jsx
```

The following already exist in your project (no changes needed):
- ✓ RoleBasedRedirect.jsx
- ✓ AvailabilityCheckRoute.jsx
- ✓ WorkSessionTimer.jsx
- ✓ AvailabilitySetupModal.jsx
- ✓ RoleBasedLayout.jsx

---

### STEP 7: FRONTEND - Add API Modules

**Location:** `/frontend/src/api/`

Copy these 3 new files:
```
✓ work-sessions.js
✓ weekly-availability.js
✓ daily-work-updates.js
```

---

### STEP 8: FRONTEND - Update Dashboards

**Location:** `/frontend/src/pages/`

Replace these files with enhanced versions:
```
✓ developer/DeveloperDashboard.jsx (enhanced with daily update form)
✓ tester/TesterDashboard.jsx (enhanced with daily update form)
✓ scrum-master/ScrumMasterDashboard.jsx (enhanced with team updates)
✓ pm/ProjectManagerDashboard.jsx (enhanced)
✓ product-owner/ProductOwnerDashboard.jsx (enhanced)
✓ team-lead/TeamLeadDashboard.jsx (enhanced)
✓ client/ClientDashboard.jsx (enhanced with strict data isolation)
```

If you have custom dashboard modifications, preserve them and integrate the new features.

---

### STEP 9: FRONTEND - Update App.jsx

**File:** `/frontend/src/App.jsx`

Update the App routing structure. The routing should look like this:

```jsx
<Routes>
  {/* Public Routes */}
  <Route path="/login" element={<LoginPage />} />
  <Route path="/forgot-password" element={<ForgotPasswordPage />} />

  {/* Password Change */}
  <Route element={<RequirePasswordChangeRoute />}>
    <Route path="/change-password" element={<ChangePasswordPage />} />
  </Route>

  {/* Protected Admin Routes (existing) */}
  <Route element={<ProtectedRoute />}>
    <Route element={<AdminLayout />}>
      <Route path="/admin/dashboard" element={<DashboardPage />} />
      {/* ... all existing admin routes ... */}
    </Route>
  </Route>

  {/* NEW: Root redirect based on role */}
  <Route element={<ProtectedRoute />}>
    <Route path="/" element={<RoleBasedRedirect />} />
  </Route>

  {/* NEW: Role-based dashboards */}
  <Route element={<ProtectedRoute />}>
    <Route element={<RoleBasedLayout />}>
      <Route path="/developer/dashboard" element={<DeveloperDashboard />} />
      <Route path="/tester/dashboard" element={<TesterDashboard />} />
      <Route path="/scrum-master/dashboard" element={<ScrumMasterDashboard />} />
      <Route path="/pm/dashboard" element={<ProjectManagerDashboard />} />
      <Route path="/product-owner/dashboard" element={<ProductOwnerDashboard />} />
      <Route path="/team-lead/dashboard" element={<TeamLeadDashboard />} />
      <Route path="/client/dashboard" element={<ClientDashboard />} />
    </Route>
  </Route>

  {/* Catch-all */}
  <Route path="*" element={<Navigate to="/login" replace />} />
</Routes>
```

---

### STEP 10: FRONTEND - Update Context Providers

**File:** `/frontend/src/App.jsx` (in the root JSX)

Ensure the `WorkSessionProvider` wraps everything:

```jsx
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <WorkSessionProvider>
          <Routes>
            {/* ... all routes ... */}
          </Routes>
        </WorkSessionProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
```

---

### STEP 11: FRONTEND - Check Imports

Make sure all dashboard imports are added to your App.jsx:

```jsx
import DeveloperDashboard from "./pages/developer/DeveloperDashboard";
import TesterDashboard from "./pages/tester/TesterDashboard";
import ScrumMasterDashboard from "./pages/scrum-master/ScrumMasterDashboard";
import ProjectManagerDashboard from "./pages/pm/ProjectManagerDashboard";
import ProductOwnerDashboard from "./pages/product-owner/ProductOwnerDashboard";
import TeamLeadDashboard from "./pages/team-lead/TeamLeadDashboard";
import ClientDashboard from "./pages/client/ClientDashboard";
```

---

## VERIFICATION CHECKLIST

After integration, verify everything is in place:

### Backend
- [ ] All 5 new models in `/app/models/`
- [ ] Models imported in `/app/models/__init__.py`
- [ ] All 5 new services in `/app/services/`
- [ ] All 4 new schemas in `/app/schemas/`
- [ ] Schemas imported in `/app/schemas/__init__.py`
- [ ] 3 new endpoint files in `/app/api/v1/endpoints/`
- [ ] Routers registered in `/app/api/v1/router.py`
- [ ] Migration file in `/migrations/versions/`

### Frontend
- [ ] 2 new components (DailyUpdateForm.jsx, AnalysisDisplay.jsx)
- [ ] 3 new API modules (work-sessions.js, weekly-availability.js, daily-work-updates.js)
- [ ] 7 dashboard files updated/created
- [ ] App.jsx updated with new routes
- [ ] WorkSessionProvider wraps routes
- [ ] All imports added to App.jsx

---

## DATABASE MIGRATION

Run the migration to create new tables:

```bash
cd /backend
alembic upgrade head
```

**Tables created:**
1. `work_sessions` - User work tracking
2. `weekly_availability` - Employee schedules
3. `daily_work_updates` - Daily summaries
4. `daily_work_update_analysis` - AI analysis results
5. `audit_logs` - Audit trail

---

## TESTING THE INTEGRATION

### 1. Start Backend
```bash
cd /backend
python -m uvicorn app.main:app --reload
```

### 2. Start Frontend
```bash
cd /frontend
npm run dev
```

### 3. Test Login Flow
- Log in as different roles
- Verify redirect to correct dashboard
- Check availability modal on first login (if not configured)

### 4. Test Features
- Start work session
- Submit daily update
- View AI analysis
- Verify team sees updates (Scrum Master)
- Confirm client sees only projects (not internal data)

---

## COMMON ISSUES & SOLUTIONS

### Issue: Import errors for new models
**Solution:** Make sure all new models are imported in `/app/models/__init__.py`

### Issue: Routes not working
**Solution:** Verify routers are registered in `/app/api/v1/router.py` with correct prefixes

### Issue: Dashboard not loading
**Solution:** Check that all imports are added to App.jsx and dashboard files are in correct locations

### Issue: Database table doesn't exist
**Solution:** Run `alembic upgrade head` to apply the migration

### Issue: WorkSession timer not showing
**Solution:** Verify `WorkSessionProvider` wraps the `<Routes>` in App.jsx

---

## AFTER INTEGRATION

Your project will have:

✅ All 8 role-specific dashboards  
✅ Work session tracking (backend + frontend)  
✅ Availability management (7-day schedule)  
✅ Daily work updates with AI analysis  
✅ Team visibility (Scrum Master, PM, Team Lead)  
✅ Client data isolation (strict)  
✅ Audit logging  
✅ Role-based routing  

**Plus all existing Modules 1-7 continue to work unchanged.**

---

## FILE COUNT

**Files to add/modify:**
- Backend: 16 new files (5 models, 5 services, 4 schemas, 3 endpoints)
- Backend: 1 migration, 2 files modified (router.py, models/__init__.py, schemas/__init__.py)
- Frontend: 2 new components, 3 new API modules
- Frontend: 7 dashboard updates, 1 App.jsx update

**Total: ~30 file operations**

---

## SUPPORT

If you need help with any step:
1. Check the detailed implementation files (all provided)
2. Refer to existing patterns in your project (auth, projects, etc.)
3. All new files follow your project's conventions

All code is production-ready and tested.

---

**You're ready to integrate!** 🚀
