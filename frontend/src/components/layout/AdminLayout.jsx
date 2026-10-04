import { NavLink, Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../ui/Button";
import { NotificationBell } from "../NotificationBell";

const links = [
  ["Dashboard", "/admin/dashboard"], ["AI Command Center", "/admin/ai-command-center"], ["Projects", "/admin/projects"], ["Employees", "/admin/employees"],
  ["Templates", "/admin/templates"], ["Leave", "/admin/leave"], ["Availability", "/admin/availability"], ["Workload", "/admin/workload"]
];
function initials(name = "Admin") { return name.split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join("").toUpperCase(); }

export function AdminLayout() {
  const { session, logout } = useAuth();
  if (session?.role !== "owner_admin") return <Navigate to="/" replace />;
  return <div className="app-shell">
    <aside className="app-sidebar">
      <div className="brand-lockup"><div className="brand-mark">S</div><div><div className="brand-name">SprintNova</div><div className="brand-tag">Agile workspace</div></div></div>
      <div className="role-chip"><span className="role-dot" />Organization Admin</div>
      <nav className="sidebar-nav"><p className="nav-caption">Management</p>{links.map(([label,to])=><NavLink key={to} to={to} className={({isActive})=>`sidebar-link ${isActive?"active":""}`}><span className="nav-bullet" />{label}</NavLink>)}</nav>
      <div className="sidebar-footer"><div className="sidebar-help"><strong>Organization control</strong><span>People, projects, access and operational health.</span></div><button className="sidebar-signout" onClick={logout}>Sign out</button></div>
    </aside>
    <div className="app-main">
      <header className="topbar"><div className="mobile-brand"><div className="brand-mark">S</div><span>SprintNova</span></div><div className="topbar-context"><span className="context-kicker">Organization</span><span>Admin workspace</span></div><div className="topbar-actions"><NotificationBell/><div className="profile-mini"><div className="avatar">{initials(session?.fullName)}</div><div className="profile-copy"><strong>{session?.fullName}</strong><span>{session?.companyEmail}</span></div></div><Button variant="secondary" className="mobile-signout" onClick={logout}>Sign out</Button></div></header>
      <main className="content-area"><div className="content-inner"><div className="page-breadcrumb"><span>SprintNova</span><b>/</b><span>Organization</span></div><Outlet/></div></main>
    </div>
  </div>;
}
