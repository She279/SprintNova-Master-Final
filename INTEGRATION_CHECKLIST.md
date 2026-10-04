# 🚀 Employee Workspace Feature - Integration Checklist

Use this checklist to track your integration progress.

---

## STEP 1: Extract Files
```bash
cd /path/to/your/sprintnova
tar -xzf source-files.tar.gz --strip-components=1
```
- [ ] Archive extracted
- [ ] No conflicts reported
- [ ] Files merged into project

---

## STEP 2: Backend Models (5 files)

### ✓ Models Created
- [ ] `backend/app/models/work_session.py`
- [ ] `backend/app/models/weekly_availability.py`
- [ ] `backend/app/models/daily_work_update.py`
- [ ] `backend/app/models/daily_work_update_analysis.py`
- [ ] `backend/app/models/audit_log.py`

### ✓ Models Imported
Edit `backend/app/models/__init__.py`:
```python
from .work_session import WorkSession
from .weekly_availability import WeeklyAvailability
from .daily_work_update import DailyWorkUpdate
from .daily_work_update_analysis import DailyWorkUpdateAnalysis
from .audit_log import AuditLog
```

- [ ] Imports added to `__init__.py`
- [ ] All models in `__all__` list

---

## STEP 3: Backend Services (5 files)

### ✓ Services Created
- [ ] `backend/app/services/work_session_service.py`
- [ ] `backend/app/services/weekly_availability_service.py`
- [ ] `backend/app/services/daily_work_update_service.py`
- [ ] `backend/app/services/daily_work_update_analysis_service.py`
- [ ] `backend/app/services/audit_service.py`

### ✓ No Changes Needed to `__init__.py`
- [ ] Services created (imported where used, not in __init__)

---

## STEP 4: Backend Schemas (4 files)

### ✓ Schemas Created
- [ ] `backend/app/schemas/work_session.py`
- [ ] `backend/app/schemas/weekly_availability.py`
- [ ] `backend/app/schemas/daily_work_update.py`
- [ ] `backend/app/schemas/daily_work_update_analysis.py`

### ✓ Schemas Imported
Edit `backend/app/schemas/__init__.py`:
```python
from .work_session import WorkSessionResponse, WorkSessionDetailResponse
from .weekly_availability import WeeklyScheduleSetup, FullWeeklyScheduleResponse
from .daily_work_update import DailyWorkUpdateCreate, DailyWorkUpdateUpdate, DailyWorkUpdateDetailResponse
from .daily_work_update_analysis import DailyWorkUpdateAnalysisResponse
```

- [ ] Imports added to `__init__.py`
- [ ] Following existing pattern

---

## STEP 5: Backend Endpoints (3 files)

### ✓ Endpoints Created
- [ ] `backend/app/api/v1/endpoints/work_sessions.py`
- [ ] `backend/app/api/v1/endpoints/weekly_availability.py`
- [ ] `backend/app/api/v1/endpoints/daily_work_updates.py`

### ✓ Routers Registered
Edit `backend/app/api/v1/router.py`:
```python
from .endpoints.work_sessions import router as work_sessions_router
from .endpoints.weekly_availability import router as weekly_availability_router
from .endpoints.daily_work_updates import router as daily_work_updates_router

# Include routers
router.include_router(work_sessions_router, prefix="/work-sessions", tags=["work-sessions"])
router.include_router(weekly_availability_router, prefix="/availability/weekly", tags=["availability"])
router.include_router(daily_work_updates_router, prefix="/daily-updates", tags=["daily-updates"])
```

- [ ] Imports added
- [ ] Routers included with correct prefixes
- [ ] Tags added for API docs

---

## STEP 6: Database Migration

### ✓ Migration File Created
- [ ] `backend/migrations/versions/add_employee_workspace_tables.py`

### ✓ Migration Applied
```bash
cd backend
alembic upgrade head
```

- [ ] Migration ran successfully
- [ ] All 5 tables created:
  - [ ] work_sessions
  - [ ] weekly_availability
  - [ ] daily_work_updates
  - [ ] daily_work_update_analysis
  - [ ] audit_logs

Verify with:
```bash
psql your_db -c "\dt"
```

---

## STEP 7: Frontend Components

### ✓ New Components Created
- [ ] `frontend/src/components/DailyUpdateForm.jsx`
- [ ] `frontend/src/components/AnalysisDisplay.jsx`

### ✓ Existing Components (Already in place)
- [ ] `frontend/src/components/RoleBasedRedirect.jsx`
- [ ] `frontend/src/components/AvailabilityCheckRoute.jsx`
- [ ] `frontend/src/components/WorkSessionTimer.jsx`
- [ ] `frontend/src/components/AvailabilitySetupModal.jsx`
- [ ] `frontend/src/components/layout/RoleBasedLayout.jsx`

### ✓ Context Updated/Created
- [ ] `frontend/src/context/WorkSessionContext.jsx`

---

## STEP 8: Frontend API Modules

### ✓ API Modules Created
- [ ] `frontend/src/api/work-sessions.js`
- [ ] `frontend/src/api/weekly-availability.js`
- [ ] `frontend/src/api/daily-work-updates.js`

---

## STEP 9: Frontend Dashboards (7 files)

### ✓ Dashboards Updated/Enhanced
- [ ] `frontend/src/pages/developer/DeveloperDashboard.jsx` (added daily update form + timer)
- [ ] `frontend/src/pages/tester/TesterDashboard.jsx` (added daily update form)
- [ ] `frontend/src/pages/scrum-master/ScrumMasterDashboard.jsx` (team updates + risk view)
- [ ] `frontend/src/pages/pm/ProjectManagerDashboard.jsx` (enhanced metrics)
- [ ] `frontend/src/pages/product-owner/ProductOwnerDashboard.jsx` (enhanced dashboard)
- [ ] `frontend/src/pages/team-lead/TeamLeadDashboard.jsx` (team workload)
- [ ] `frontend/src/pages/client/ClientDashboard.jsx` (strict isolation ⚠️)

---

## STEP 10: Frontend App.jsx Update

Edit `frontend/src/App.jsx`:

### ✓ Import New Components
```jsx
import RoleBasedRedirect from "./components/RoleBasedRedirect";
import AvailabilityCheckRoute from "./components/AvailabilityCheckRoute";
import DeveloperDashboard from "./pages/developer/DeveloperDashboard";
import TesterDashboard from "./pages/tester/TesterDashboard";
import ScrumMasterDashboard from "./pages/scrum-master/ScrumMasterDashboard";
import ProjectManagerDashboard from "./pages/pm/ProjectManagerDashboard";
import ProductOwnerDashboard from "./pages/product-owner/ProductOwnerDashboard";
import TeamLeadDashboard from "./pages/team-lead/TeamLeadDashboard";
import ClientDashboard from "./pages/client/ClientDashboard";
```

- [ ] All imports added

### ✓ Add Routes Structure
```jsx
<Routes>
  {/* Public */}
  <Route path="/login" element={<LoginPage />} />
  <Route path="/forgot-password" element={<ForgotPasswordPage />} />

  {/* Password Change */}
  <Route element={<RequirePasswordChangeRoute />}>
    <Route path="/change-password" element={<ChangePasswordPage />} />
  </Route>

  {/* Admin Routes */}
  <Route element={<ProtectedRoute />}>
    <Route element={<AdminLayout />}>
      <Route path="/admin/dashboard" element={<DashboardPage />} />
      {/* ... existing admin routes ... */}
    </Route>
  </Route>

  {/* NEW: Root Redirect */}
  <Route element={<ProtectedRoute />}>
    <Route path="/" element={<RoleBasedRedirect />} />
  </Route>

  {/* NEW: Role Dashboards */}
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

- [ ] Routes added in correct structure
- [ ] Role-based layout wraps role dashboards
- [ ] Catch-all redirects to login

### ✓ Wrap with Providers
```jsx
<BrowserRouter>
  <AuthProvider>
    <WorkSessionProvider>
      <Routes>{/* ... */}</Routes>
    </WorkSessionProvider>
  </AuthProvider>
</BrowserRouter>
```

- [ ] `WorkSessionProvider` wraps `<Routes>`
- [ ] Import `WorkSessionProvider` from context

---

## STEP 11: Test Integration

### ✓ Backend Tests
```bash
cd backend
python -m uvicorn app.main:app --reload
```

Check in browser: `http://localhost:8000/docs`

- [ ] Server starts without errors
- [ ] API docs show new endpoints:
  - [ ] `/work-sessions/*`
  - [ ] `/availability/weekly/*`
  - [ ] `/daily-updates/*`

### ✓ Frontend Tests
```bash
cd frontend
npm run dev
```

Visit: `http://localhost:5173`

- [ ] App loads without console errors
- [ ] Login works
- [ ] Redirects to correct dashboard per role

### ✓ Feature Tests

#### Work Session
- [ ] Start session button works
- [ ] Timer increments
- [ ] Stop session button saves duration

#### Daily Update
- [ ] Form displays
- [ ] Can submit update
- [ ] Analysis shows (risk badge, suggestions)

#### Availability (first login)
- [ ] Modal appears for new users
- [ ] Can set 7-day schedule
- [ ] System remembers configuration

#### Team Views (Scrum Master)
- [ ] See team daily updates
- [ ] See risk badges
- [ ] See blockers for team

#### Client Isolation
- [ ] Client sees projects only
- [ ] No availability visible
- [ ] No team members visible
- [ ] No internal updates visible

---

## ✅ INTEGRATION COMPLETE!

When all checkboxes are done:

```bash
# Backend
cd backend && alembic upgrade head && python -m uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend && npm run dev
```

Visit `http://localhost:5173` and test the complete flow! 🎉

---

## 🚨 COMMON ISSUES

| Problem | Checklist |
|---------|-----------|
| Import errors | ✓ Check models/__init__.py, schemas/__init__.py |
| Routes 404 | ✓ Verify router.include_router() in router.py |
| DB errors | ✓ Run `alembic upgrade head` |
| Timer not showing | ✓ Verify WorkSessionProvider in App.jsx |
| Dashboard blank | ✓ Check all dashboard imports in App.jsx |
| 403 Forbidden on endpoints | ✓ Verify role permissions in endpoint decorators |

---

## 📞 NEED HELP?

Refer to:
1. **INTEGRATION_GUIDE.md** - Detailed step-by-step
2. **README.md** - Overview & troubleshooting
3. **API_ENDPOINTS_REFERENCE.md** - Endpoint details (in source archive)

All files are production-ready! ✨
