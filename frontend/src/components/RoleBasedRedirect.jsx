import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ROLE_REDIRECTS = {
  owner_admin: "/admin/dashboard",
  product_owner: "/product-owner/dashboard",
  scrum_master: "/scrum-master/dashboard",
  project_manager: "/pm/dashboard",
  team_lead: "/team-lead/dashboard",
  developer: "/developer/dashboard",
  tester: "/tester/dashboard",
  client: "/client/dashboard",
};

export function RoleBasedRedirect() {
  const { session } = useAuth();

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  const dashboardPath = ROLE_REDIRECTS[session.role] || "/admin/dashboard";
  return <Navigate to={dashboardPath} replace />;
}
