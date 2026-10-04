import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { employeesApi } from "../../api/employees";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Feedback";
import { Alert } from "../../components/ui/Feedback";

export default function EmployeesListPage() {
  const [employees, setEmployees] = useState(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function load() {
    try {
      setEmployees(await employeesApi.list());
    } catch (err) {
      setError(err.message || "Could not load employees.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function toggleStatus(emp) {
    setBusyId(emp.id);
    try {
      await employeesApi.setStatus(emp.id, !emp.is_active);
      await load();
    } catch (err) {
      setError(err.message || "Could not update employee status.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight">Employees</h1>
          <p className="text-sm text-muted mt-1">
            Every account here logs in with an auto-generated{" "}
            <code className="font-mono text-xs bg-black/[0.04] px-1.5 py-0.5 rounded">@sprintnova.com</code> address.
          </p>
        </div>
        <Link to="/admin/employees/new">
          <Button>+ Create employee</Button>
        </Link>
      </div>

      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      <div className="rounded-lg border border-line bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-black/[0.015] text-left text-xs uppercase tracking-wider text-muted">
              <th className="px-5 py-3 font-medium">Employee</th>
              <th className="px-5 py-3 font-medium">Company email</th>
              <th className="px-5 py-3 font-medium">Personal email</th>
              <th className="px-5 py-3 font-medium">Role</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {employees === null && (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-muted">Loading…</td>
              </tr>
            )}
            {employees?.length === 0 && (
              <tr>
                <td colSpan={6} className="px-5 py-10 text-center text-muted">
                  No employees yet. Create the first one to see their generated company email here.
                </td>
              </tr>
            )}
            {employees?.map((emp) => (
              <tr key={emp.id} className="border-b border-line last:border-0 hover:bg-black/[0.01]">
                <td className="px-5 py-3.5">
                  <Link to={`/admin/employees/${emp.id}`} className="font-medium hover:text-accent">
                    {emp.first_name} {emp.last_name}
                  </Link>
                  <div className="text-xs text-muted font-mono">{emp.employee_id}</div>
                </td>
                <td className="px-5 py-3.5 font-mono text-xs">{emp.company_email}</td>
                <td className="px-5 py-3.5 font-mono text-xs text-muted">{emp.personal_email}</td>
                <td className="px-5 py-3.5 capitalize">{emp.role.replace("_", " ")}</td>
                <td className="px-5 py-3.5">
                  <Badge tone={emp.is_active ? "success" : "muted"}>{emp.is_active ? "Active" : "Deactivated"}</Badge>
                </td>
                <td className="px-5 py-3.5 text-right">
                  <button
                    onClick={() => toggleStatus(emp)}
                    disabled={busyId === emp.id}
                    className="text-xs font-medium text-accent hover:underline disabled:opacity-50"
                  >
                    {emp.is_active ? "Deactivate" : "Activate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
