import { NavLink, Outlet, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useWorkSession } from "../../context/WorkSessionContext";
import { Button } from "../ui/Button";
import { NotificationBell } from "../NotificationBell";
import { dailyWorkUpdatesApi } from "../../api/daily-work-updates";
import { useRealtime } from "../../hooks/useRealtime";
import { useCallback, useState } from "react";

const ROLE_CONFIG = {
  product_owner: { name: "Product Owner", short: "PO", home: "/product-owner/dashboard", links: [
    ["Dashboard", "/product-owner/dashboard"], ["Daily Update", "/product-owner/daily-update"], ["Availability", "/product-owner/availability"], ["Time", "/product-owner/time"]
  ]},
  scrum_master: { name: "Scrum Master", short: "SM", home: "/scrum-master/dashboard", links: [
    ["Dashboard", "/scrum-master/dashboard"], ["Daily Update", "/scrum-master/daily-update"], ["Team Updates", "/scrum-master/daily-updates"], ["Availability", "/scrum-master/availability"], ["Time", "/scrum-master/time"]
  ]},
  project_manager: { name: "Project Manager", short: "PM", home: "/pm/dashboard", links: [
    ["Dashboard", "/pm/dashboard"], ["Daily Update", "/pm/daily-update"], ["Team Updates", "/pm/daily-updates"], ["Availability", "/pm/availability"], ["Time", "/pm/time"]
  ]},
  team_lead: { name: "Team Lead", short: "TL", home: "/team-lead/dashboard", links: [
    ["Dashboard", "/team-lead/dashboard"], ["Daily Update", "/team-lead/daily-update"], ["Team Updates", "/team-lead/daily-updates"], ["Availability", "/team-lead/availability"], ["Time", "/team-lead/time"]
  ]},
  developer: { name: "Developer", short: "DEV", home: "/developer/dashboard", links: [
    ["Dashboard", "/developer/dashboard"], ["My Tasks", "/developer/dashboard"], ["Daily Update", "/developer/daily-update"], ["Availability", "/developer/availability"], ["Time", "/developer/time"]
  ]},
  tester: { name: "Tester", short: "QA", home: "/tester/dashboard", links: [
    ["Dashboard", "/tester/dashboard"], ["Test & Bugs", "/tester/dashboard"], ["Daily Update", "/tester/daily-update"], ["Availability", "/tester/availability"], ["Time", "/tester/time"]
  ]},
  client: { name: "Client", short: "CL", home: "/client/dashboard", links: [
    ["Overview", "/client/dashboard"]
  ]}
};

function initials(name = "User") { return name.split(/\s+/).filter(Boolean).slice(0,2).map(x => x[0]).join("").toUpperCase(); }

export function RoleBasedLayout() {
  const { session, logout } = useAuth();
  const { stopSession, isActive } = useWorkSession();
  const location = useLocation();
  const [realtimeVersion, setRealtimeVersion] = useState(0);
  const handleRealtime = useCallback((event) => {
    if (event.type !== "connection.ready") setRealtimeVersion((value) => value + 1);
  }, []);
  useRealtime({ onEvent: handleRealtime, enabled: !!session });
  const config = ROLE_CONFIG[session?.role];
  if (!config) return <Navigate to="/" replace />;
  const prefix = config.home.split("/").slice(0,2).join("/") + "/";
  if (!location.pathname.startsWith(prefix)) return <Navigate to={config.home} replace />;

  const handleLogout = async () => {
    if (session?.role !== "client") {
      try {
        const pending = await dailyWorkUpdatesApi.checkPending();
        if (pending.is_pending) {
          window.alert("Today's work update is pending. Please submit it before logging out.");
          window.location.assign(`${prefix}daily-update`);
          return;
        }
      } catch (_) {}
    }
    if (isActive) await stopSession().catch(() => {});
    logout();
  };

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="brand-lockup">
          <div className="brand-mark">S</div>
          <div><div className="brand-name">SprintNova</div><div className="brand-tag">Agile workspace</div></div>
        </div>
        <div className="role-chip"><span className="role-dot" />{config.name}</div>
        <nav className="sidebar-nav">
          <p className="nav-caption">Workspace</p>
          {config.links.map(([label,to]) => <NavLink key={to} to={to} className={({isActive}) => `sidebar-link ${isActive ? "active" : ""}`}><span className="nav-bullet" />{label}</NavLink>)}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-help"><strong>Stay on track</strong><span>Use Daily Update to keep your project context accurate.</span></div>
          <button className="sidebar-signout" onClick={handleLogout}>Sign out</button>
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <div className="mobile-brand"><div className="brand-mark">S</div><span>SprintNova</span></div>
          <div className="topbar-context"><span className="context-kicker">Workspace</span><span>{config.name}</span></div>
          <div className="topbar-actions">
            <NotificationBell />
            <div className="profile-mini"><div className="avatar">{initials(session?.fullName)}</div><div className="profile-copy"><strong>{session?.fullName}</strong><span>{session?.companyEmail}</span></div></div>
            <Button variant="secondary" className="mobile-signout" onClick={handleLogout}>Sign out</Button>
          </div>
        </header>
        <main className="content-area"><div className="content-inner"><div className="page-breadcrumb"><span>SprintNova</span><b>/</b><span>{config.name}</span><span className="realtime-status">Live</span></div><Outlet key={realtimeVersion} /></div></main>
      </div>
    </div>
  );
}
