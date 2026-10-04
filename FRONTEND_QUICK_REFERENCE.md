# Frontend Phase 2 - Quick Reference Guide

## File Locations & Imports

### Work Session Timer
```jsx
// Import in dashboard
import { useWorkSession } from "../context/WorkSessionContext";
import { WorkSessionTimer } from "../components/WorkSessionTimer";

// Use in layout header (already done in RoleBasedLayout)
<WorkSessionTimer />

// Access state in component
const { isActive, elapsedSeconds, startSession, stopSession } = useWorkSession();
```

### Availability Setup
```jsx
import { AvailabilitySetupModal } from "../components/AvailabilitySetupModal";
import { weeklyAvailabilityApi } from "../api/weekly-availability";

// Check if configured
const result = await weeklyAvailabilityApi.isConfigured();
if (!result.is_configured) {
  // Show modal
}

// Save schedule
await weeklyAvailabilityApi.setup({
  timezone: "IST",
  schedule: {
    monday: { start_time: "09:00", end_time: "17:30" },
    // ... etc for all 7 days
  }
});
```

### Daily Work Updates
```jsx
import { dailyWorkUpdatesApi } from "../api/daily-work-updates";

// Check if pending
const pending = await dailyWorkUpdatesApi.checkPending();

// Get today's update
const update = await dailyWorkUpdatesApi.getTodayUpdate();

// Create new update
await dailyWorkUpdatesApi.create({
  project_id: "project-123",
  work_done: "Completed feature X",
  completed_work: "Feature X, Bug fix Y",
  pending_work: "Feature Z, Testing",
  blockers: "Waiting on design approval",
  additional_notes: "Pair programmed with John",
  progress_percentage: 75
});

// Update existing
await dailyWorkUpdatesApi.update(updateId, {
  work_done: "Updated work description",
  // ... other fields
});

// Get analysis
const analysis = await dailyWorkUpdatesApi.getAnalysis(updateId);
// Returns: summary, completed_items, pending_items, detected_blockers, 
//          risk_level, suggested_actions, task_suggestions
```

### Work Sessions
```jsx
import { workSessionApi } from "../api/work-sessions";

// Start session (auto-recovers if exists)
const session = await workSessionApi.start();
// Returns: { id, user_id, started_at, status: "active" }

// Get current session
const current = await workSessionApi.getCurrent();

// Stop session
const stopped = await workSessionApi.stop(sessionId);
// Returns: { status: "completed", total_work_minutes: 480 }

// Get today's total
const total = await workSessionApi.getTodayTotal();
// Returns: { total_minutes: 480 }

// Get history
const history = await workSessionApi.getHistory(limit=50, skip=0);

// Get currently working users (admin/sm only)
const working = await workSessionApi.getCurrentlyWorking();
```

---

## Adding New Components

### Template: Dashboard Page
```jsx
import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";

export default function RoleDashboard() {
  const { session } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        // Fetch data from APIs
        setData(result);
      } catch (error) {
        console.error("Failed to load:", error);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-[color]-600 to-[color]-700 text-white rounded-lg p-6">
        <h1 className="text-3xl font-bold">{session?.fullName}'s Dashboard</h1>
      </div>
      
      {/* Dashboard content */}
    </div>
  );
}
```

### Template: Form Component
```jsx
import { useState } from "react";

export function MyForm({ onSuccess }) {
  const [data, setData] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const result = await apiCall(data);
      onSuccess?.(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <div className="p-4 bg-red-50 text-red-800">{error}</div>}
      
      {/* Form fields */}
      
      <button
        type="submit"
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {loading ? "Loading..." : "Submit"}
      </button>
    </form>
  );
}
```

---

## Common Tasks

### Add New Dashboard Route
1. Create page component in `/pages/{role}/{RoleDashboard}.jsx`
2. Import in `App.jsx`
3. Add route under `<RoleBasedLayout>`:
   ```jsx
   <Route path="/role/dashboard" element={<RoleDashboard />} />
   ```

### Add New Role-Specific Navigation Link
1. Edit `RoleBasedLayout.jsx`
2. Add to `ROLE_NAV_LINKS` object:
   ```jsx
   role_name: [
     { to: "/role/page1", label: "Page 1" },
     { to: "/role/page2", label: "Page 2" },
   ]
   ```

### Display Work Session Timer
- Already in `RoleBasedLayout` header (no action needed)
- Or use `<WorkSessionTimer />` component directly

### Check Availability Configuration
- Use `AvailabilityCheckRoute` wrapper (optional)
- Or call API directly: `weeklyAvailabilityApi.isConfigured()`

### Handle API Errors
```jsx
try {
  const result = await api.call();
} catch (error) {
  if (error.status === 409) {
    // Conflict - e.g., duplicate daily update
  } else if (error.status === 403) {
    // Forbidden - role not allowed
  } else if (error.status === 401) {
    // Unauthorized - need to login
  }
}
```

---

## Styling Classes (Tailwind)

### Common Patterns
```jsx
// Header cards
<div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg p-6">

// Content cards
<div className="bg-white rounded-lg border border-gray-200 p-6">

// Button variations
// Primary: bg-blue-600 hover:bg-blue-700
// Secondary: bg-gray-100 hover:bg-gray-200
// Danger: bg-red-600 hover:bg-red-700
// Success: bg-green-600 hover:bg-green-700

// Grid layouts
// 2 columns: grid grid-cols-2 gap-6
// 3 columns: grid grid-cols-3 gap-4
// 4 columns: grid grid-cols-4 gap-3

// Status badges
<span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">Active</span>
```

---

## Testing Checklist

- [ ] Login with different roles → correct dashboard loads
- [ ] First login → availability modal appears (if not client)
- [ ] Complete availability setup → modal closes, dashboard loads
- [ ] Work session timer starts → elapsed time increases
- [ ] Refresh page → timer recovers elapsed time from backend
- [ ] Stop work session → confirmation dialog, session stops
- [ ] Client login → sees restricted dashboard (no employee data)
- [ ] Navigation menu shows only role-appropriate links
- [ ] Logout → redirects to login page
- [ ] Each dashboard pulls real data (check network tab)

---

## Backend Endpoints Used

All endpoints are on the same domain/port as the frontend. Adjust in `api/client.js` if needed.

### Work Sessions
- `POST /api/v1/work-sessions/start`
- `GET /api/v1/work-sessions/current`
- `POST /api/v1/work-sessions/{id}/stop`
- `GET /api/v1/work-sessions/today-total`

### Availability
- `POST /api/v1/availability/weekly/setup`
- `GET /api/v1/availability/weekly/is-configured`
- `GET /api/v1/availability/weekly/schedule`

### Daily Updates
- `POST /api/v1/daily-updates`
- `GET /api/v1/daily-updates/me/today`
- `GET /api/v1/daily-updates/me/pending`
- `GET /api/v1/daily-updates/{id}/analysis`
- `GET /api/v1/daily-updates/team/today`

All require JWT token in `Authorization: Bearer <token>` header (handled by `api/client.js`)

---

## Common Issues

### "WorkSessionProvider is not a provider"
- Make sure it wraps the entire app (check App.jsx line 51)
- Component must be inside `<WorkSessionProvider>`

### Timer doesn't persist on refresh
- Check `WorkSessionContext` useEffect on mount (should call `getCurrent()`)
- Check network tab - is API call returning active session?

### Availability modal doesn't show
- Ensure backend is running and `is-configured` endpoint works
- Check browser console for API errors
- Verify user role is not "client" (they don't need availability)

### Role navigation links don't appear
- Check `ROLE_NAV_LINKS` in `RoleBasedLayout.jsx` for correct role name
- Role string must match backend role exactly (e.g., "owner_admin" not "ownerAdmin")

### Button clicks do nothing
- Check browser console for errors
- Verify API endpoint exists and is not 403/401
- Check network tab to see actual API response

---

## Next Phases

### Phase 3A: Forms & Submissions
- DailyWorkUpdateForm component
- Real-time validation
- Auto-save drafts
- 409 duplicate handling

### Phase 3B: Analysis Display
- AnalysisDisplay component
- Risk level indicators
- Suggested actions UI
- Task suggestions list

### Phase 3C: Team Views
- Team updates list (SM/PM only)
- Filter & search
- Bulk actions
- Update history

See `PHASE2_FRONTEND_SUMMARY.md` for full roadmap.
