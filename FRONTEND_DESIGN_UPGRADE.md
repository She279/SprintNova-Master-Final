# SprintNova Frontend Design Upgrade

The existing React application was retained and visually upgraded rather than rebuilt.

## Product flow
LOGIN -> ROLE DETECTION -> AVAILABILITY CHECK -> WORK SESSION -> ROLE WORKSPACE -> DAILY WORK -> AI INSIGHTS -> REVIEW -> AUDIT -> LOGOUT

## Design system
- Primary: indigo/violet for product actions and active navigation
- Secondary: blue for progress and operational context
- Success: green for healthy/completed states
- Warning: amber for risk and pending states
- Danger: red for blockers/errors
- Neutral: deep navy sidebar + cool gray workspace background

## UX changes
- Persistent role-aware sidebar navigation
- Role identity chip
- Sticky topbar with work-session state, notifications and profile
- Breadcrumb context
- Responsive mobile header
- Product-style login screen with Plan -> Build -> Test -> Deliver flow
- Cleaner visual hierarchy and shadows
- Removed misleading navigation links that did not have implemented routes from the role sidebar
- Login now returns to role-based redirect after authentication instead of always opening the admin area

## Existing functionality preserved
Backend APIs, authentication, RBAC, project data, AI services, ChromaDB, dashboards, daily updates, availability, leave and work-session logic were not replaced by this visual upgrade.
