import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { WorkSessionProvider } from "./context/WorkSessionContext";
import { ProtectedRoute, RequirePasswordChangeRoute } from "./components/ProtectedRoute";
import { AdminLayout } from "./components/layout/AdminLayout";
import { RoleBasedLayout } from "./components/layout/RoleBasedLayout";
import { RoleBasedRedirect } from "./components/RoleBasedRedirect";

import LoginPage from "./pages/LoginPage";
import ChangePasswordPage from "./pages/ChangePasswordPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import DashboardPage from "./pages/admin/dashboard/DashboardPage";
import EmployeesListPage from "./pages/admin/EmployeesListPage";
import CreateEmployeePage from "./pages/admin/CreateEmployeePage";
import EmployeeDetailPage from "./pages/admin/EmployeeDetailPage";
import ProjectsListPage from "./pages/admin/projects/ProjectsListPage";
import CreateProjectPage from "./pages/admin/projects/CreateProjectPage";
import ProjectDetailPage from "./pages/admin/projects/ProjectDetailPage";
import SprintDetailPage from "./pages/admin/projects/SprintDetailPage";
import ProjectTemplatesPage from "./pages/admin/templates/ProjectTemplatesPage";
import LeaveRequestsPage from "./pages/admin/leave/LeaveRequestsPage";
import AvailabilityPage from "./pages/admin/availability/AvailabilityPage";
import WorkloadPage from "./pages/admin/workload/WorkloadPage";
import AICommandCenterPage from "./pages/admin/ai/AICommandCenterPage";

// Role-specific dashboards
import DeveloperDashboard from "./pages/developer/DeveloperDashboard";
import TesterDashboard from "./pages/tester/TesterDashboard";
import ScrumMasterDashboard from "./pages/scrum-master/ScrumMasterDashboard";
import ProjectManagerDashboard from "./pages/pm/ProjectManagerDashboard";
import ProductOwnerDashboard from "./pages/product-owner/ProductOwnerDashboard";
import TeamLeadDashboard from "./pages/team-lead/TeamLeadDashboard";
import DailyUpdatePage from "./pages/shared/DailyUpdatePage";
import AvailabilityPageSelf from "./pages/shared/AvailabilityPageSelf";
import TimePage from "./pages/shared/TimePage";
import ClientDashboard from "./pages/client/ClientDashboard";
import { AvailabilityCheckRoute } from "./components/AvailabilityCheckRoute";

/**
 * Route tree. Module 1 owns everything under /login, /change-password,
 * /forgot-password, and /admin/employees/*. Module 2 owns /admin/projects/*.
 *
 * Future modules attach their own routes the same way: add a <Route> under
 * the <AdminLayout> element below (or a new layout, e.g. for the Kanban
 * board), guarded by <ProtectedRoute> as needed. Example:
 *
 *   <Route element={<AvailabilityCheckRoute><AdminLayout /></AvailabilityCheckRoute>}>
 *     ...
 *     <Route path="/sprints/:id/board" element={<KanbanBoardPage />} />
 *   </Route>
 */
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <WorkSessionProvider>
          <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />

          <Route element={<RequirePasswordChangeRoute />}>
            <Route path="/change-password" element={<ChangePasswordPage />} />
          </Route>

          <Route element={<ProtectedRoute />}>
            <Route element={<AvailabilityCheckRoute><AdminLayout /></AvailabilityCheckRoute>}>
              <Route path="/admin/dashboard" element={<DashboardPage />} />
              <Route path="/admin/ai-command-center" element={<AICommandCenterPage />} />

              <Route path="/admin/employees" element={<EmployeesListPage />} />
              <Route path="/admin/employees/new" element={<CreateEmployeePage />} />
              <Route path="/admin/employees/:id" element={<EmployeeDetailPage />} />

              <Route path="/admin/projects" element={<ProjectsListPage />} />
              <Route path="/admin/projects/new" element={<CreateProjectPage />} />
              <Route path="/admin/projects/:id" element={<ProjectDetailPage />} />
              <Route path="/admin/projects/:id/sprints/:sprintId" element={<SprintDetailPage />} />

              <Route path="/admin/templates" element={<ProjectTemplatesPage />} />
              <Route path="/admin/leave" element={<LeaveRequestsPage />} />
              <Route path="/admin/availability" element={<AvailabilityPage />} />
              <Route path="/admin/workload" element={<WorkloadPage />} />
              {/* Future modules attach more <Route> entries here. */}
            </Route>
          </Route>

          {/* Root redirect based on role */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<RoleBasedRedirect />} />
          </Route>

          {/* Role-specific dashboards */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AvailabilityCheckRoute><RoleBasedLayout /></AvailabilityCheckRoute>}>
              <Route path="/developer/dashboard" element={<DeveloperDashboard />} />
              <Route path="/tester/dashboard" element={<TesterDashboard />} />
              <Route path="/scrum-master/dashboard" element={<ScrumMasterDashboard />} />
              <Route path="/pm/dashboard" element={<ProjectManagerDashboard />} />
              <Route path="/product-owner/dashboard" element={<ProductOwnerDashboard />} />
              <Route path="/team-lead/dashboard" element={<TeamLeadDashboard />} />
              <Route path="/client/dashboard" element={<ClientDashboard />} />
              <Route path="/developer/daily-update" element={<DailyUpdatePage />} />
              <Route path="/tester/daily-update" element={<DailyUpdatePage />} />
              <Route path="/scrum-master/daily-updates" element={<DailyUpdatePage teamView />} />
              <Route path="/pm/daily-updates" element={<DailyUpdatePage teamView />} />
              <Route path="/team-lead/daily-updates" element={<DailyUpdatePage teamView />} />
              <Route path="/product-owner/daily-update" element={<DailyUpdatePage />} />
              <Route path="/scrum-master/daily-update" element={<DailyUpdatePage />} />
              <Route path="/pm/daily-update" element={<DailyUpdatePage />} />
              <Route path="/team-lead/daily-update" element={<DailyUpdatePage />} />
              <Route path="/product-owner/availability" element={<AvailabilityPageSelf />} />
              <Route path="/scrum-master/availability" element={<AvailabilityPageSelf />} />
              <Route path="/pm/availability" element={<AvailabilityPageSelf />} />
              <Route path="/team-lead/availability" element={<AvailabilityPageSelf />} />
              <Route path="/product-owner/time" element={<TimePage />} />
              <Route path="/scrum-master/time" element={<TimePage />} />
              <Route path="/pm/time" element={<TimePage />} />
              <Route path="/team-lead/time" element={<TimePage />} />
              <Route path="/developer/availability" element={<AvailabilityPageSelf />} />
              <Route path="/tester/availability" element={<AvailabilityPageSelf />} />
              <Route path="/developer/time" element={<TimePage />} />
              <Route path="/tester/time" element={<TimePage />} />
            </Route>
          </Route>

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
        </WorkSessionProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
