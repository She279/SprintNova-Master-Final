# SprintNova Employee Workspace - API Endpoints Reference

## Work Sessions API

### Base Path: `/api/v1/work-sessions`

| Method | Endpoint | Description | Auth | Returns |
|--------|----------|-------------|------|---------|
| POST | `/start` | Start work session | JWT | WorkSessionResponse |
| GET | `/current` | Get active session | JWT | WorkSessionDetailResponse \| null |
| POST | `/{session_id}/stop` | Stop work session | JWT | WorkSessionResponse |
| GET | `/today-total` | Get today's total minutes | JWT | `{total_minutes, formatted, hours, minutes}` |
| GET | `/history?limit=50&skip=0` | Session history | JWT | `{sessions[], total, limit, skip}` |
| GET | `/currently-working` | Admin: currently working users | JWT (Admin/SM) | `{count, users[]}` |

## Weekly Availability API

### Base Path: `/api/v1/availability/weekly`

| Method | Endpoint | Description | Auth | Request Body |
|--------|----------|-------------|------|--------------|
| POST | `/setup` | Configure weekly schedule | JWT | WeeklyScheduleSetup |
| GET | `/schedule` | Get user's schedule | JWT | - |
| GET | `/is-configured` | Check if configured | JWT | - |
| GET | `/available-hours?days=7` | Calculate available hours | JWT | - |
| GET | `/{user_id}/schedule` | View other user's schedule | JWT | - |

### Request Schema: WeeklyScheduleSetup
```json
{
  "timezone": "UTC",
  "schedule": {
    "monday": {"start_time": "09:00", "end_time": "17:30"},
    "tuesday": {"start_time": "09:00", "end_time": "17:30"},
    "wednesday": {"start_time": "09:00", "end_time": "17:30"},
    "thursday": {"start_time": "09:00", "end_time": "17:30"},
    "friday": {"start_time": "09:00", "end_time": "17:30"},
    "saturday": {"start_time": null, "end_time": null},
    "sunday": {"start_time": null, "end_time": null}
  }
}
```

### Response: FullWeeklyScheduleResponse
```json
{
  "user_id": 1,
  "timezone": "UTC",
  "is_configured": true,
  "schedule": [
    {
      "id": 1,
      "user_id": 1,
      "day_of_week": "monday",
      "start_time": "09:00:00",
      "end_time": "17:30:00",
      "effective_from": "2024-09-20T00:00:00",
      "effective_to": null,
      "created_at": "2024-09-20T10:00:00",
      "updated_at": "2024-09-20T10:00:00"
    }
  ]
}
```

## Daily Work Updates API

### Base Path: `/api/v1/daily-updates`

| Method | Endpoint | Description | Auth | Request Body |
|--------|----------|-------------|------|--------------|
| POST | `/` | Create update | JWT | DailyWorkUpdateCreate |
| GET | `/me/today` | Today's update | JWT | - |
| GET | `/me/pending` | Check if pending | JWT | - |
| GET | `/me/history?start_date=X&end_date=X&limit=30&skip=0` | History | JWT | - |
| PUT | `/{update_id}` | Update existing | JWT | DailyWorkUpdateUpdate |
| GET | `/{update_id}/analysis` | Get analysis | JWT | - |
| POST | `/{update_id}/analyze` | Trigger analysis | JWT | - |
| GET | `/team/today` | Team updates today | JWT (SM/Admin) | - |

### Request Schema: DailyWorkUpdateCreate
```json
{
  "project_id": 1,
  "date": "2024-09-20",
  "work_done": "Worked on login API implementation",
  "completed_work": "Created auth endpoints, JWT validation",
  "pending_work": "Integrate with database, write tests",
  "blockers": "PostgreSQL connection issue",
  "additional_notes": "Need to set up connection pooling",
  "progress_percentage": 70
}
```

### Response: DailyWorkUpdateResponse
```json
{
  "id": 1,
  "user_id": 1,
  "project_id": 1,
  "date": "2024-09-20",
  "work_done": "Worked on login API implementation",
  "completed_work": "Created auth endpoints, JWT validation",
  "pending_work": "Integrate with database, write tests",
  "blockers": "PostgreSQL connection issue",
  "additional_notes": "Need to set up connection pooling",
  "progress_percentage": 70,
  "submitted_at": "2024-09-20T17:00:00",
  "updated_at": "2024-09-20T17:00:00"
}
```

### Response: DailyWorkUpdateDetailResponse (with analysis)
```json
{
  "id": 1,
  "user_id": 1,
  "project_id": 1,
  "date": "2024-09-20",
  "...": "...all fields from DailyWorkUpdateResponse",
  "analysis": {
    "id": 1,
    "daily_update_id": 1,
    "summary": "Employee completed auth endpoints, 70% progress. PostgreSQL blocker identified.",
    "completed_items": "Created auth endpoints, JWT validation",
    "pending_items": "Database integration, tests",
    "detected_blockers": "PostgreSQL connection issue",
    "risk_level": "medium",
    "risk_reason": "Blocker reported",
    "suggested_progress": 70,
    "suggested_actions": "Resolve PostgreSQL connection before proceeding; Consider breaking database work into smaller tasks",
    "task_suggestions": "[]",
    "ai_provider": "rule_based",
    "model_version": null,
    "created_at": "2024-09-20T17:00:01"
  }
}
```

### Response: DailyWorkUpdateAnalysisResponse
```json
{
  "id": 1,
  "daily_update_id": 1,
  "summary": "Employee completed auth endpoints, 70% progress.",
  "completed_items": "Created auth endpoints, JWT validation",
  "pending_items": "Database integration, tests",
  "detected_blockers": "PostgreSQL connection issue",
  "risk_level": "medium",
  "risk_reason": "Blocker reported",
  "suggested_progress": 70,
  "suggested_actions": "Resolve PostgreSQL connection before proceeding",
  "task_suggestions": "[]",
  "ai_provider": "rule_based",
  "model_version": null,
  "created_at": "2024-09-20T17:00:01"
}
```

## Error Responses

### 400 Bad Request
```json
{"detail": "Invalid time format for monday. Use HH:MM"}
```

### 401 Unauthorized
```json
{"detail": "Could not validate credentials"}
```

### 403 Forbidden
```json
{"detail": "You do not have permission to perform this action"}
```

### 404 Not Found
```json
{"detail": "Daily work update not found"}
```

### 409 Conflict
```json
{"detail": "Daily work update for 2024-09-20 already exists. Use PUT to update it."}
```

## Role-Based Access Control

| Endpoint | Admin | PM | PO | SM | TL | Dev | Test | Client |
|----------|-------|----|----|----|----|-----|------|--------|
| /work-sessions/* | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| /availability/weekly/setup | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| /availability/weekly/{user_id} | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| /daily-updates/* | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| /daily-updates/team/today | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

## HTTP Status Codes

| Code | Scenario |
|------|----------|
| 200 | Success |
| 201 | Created |
| 204 | No content |
| 400 | Invalid request (bad format, logic error) |
| 401 | Missing/invalid JWT token |
| 403 | Authenticated but insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate daily update) |
| 500 | Server error |

## Common Workflows

### Workflow 1: User Login and Setup
```
1. POST /api/v1/auth/login → get JWT token
2. GET /api/v1/availability/weekly/is-configured → check
3. If not configured:
   - POST /api/v1/availability/weekly/setup → configure
4. POST /api/v1/work-sessions/start → start work session
5. Redirect to role-specific dashboard
```

### Workflow 2: Daily Work Update Submission
```
1. GET /api/v1/daily-updates/me/today → check if exists
2. If not exists:
   - POST /api/v1/daily-updates → create
   - Triggers AI analysis automatically
3. GET /api/v1/daily-updates/{id}/analysis → view analysis
4. User reviews and accepts/rejects suggestions
```

### Workflow 3: Scrum Master Views Team Updates
```
1. GET /api/v1/daily-updates/team/today → get all updates
2. For each update:
   - GET /api/v1/daily-updates/{id}/analysis → review analysis
   - Identify blockers and risks
   - Take action on high-risk items
```

## Notes

- All timestamps are in UTC
- Authentication: Bearer token in Authorization header
- Content-Type: application/json
- All endpoints require JWT authentication except `/login`
- Audit logging happens automatically for all mutations
- Gemini analysis requires GEMINI_API_KEY environment variable
- Fallback to rule-based analysis if Gemini unavailable
