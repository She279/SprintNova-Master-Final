import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { employeesApi } from "../../api/employees";
import { Badge, Alert } from "../../components/ui/Feedback";
import { Button } from "../../components/ui/Button";

export default function EmployeeDetailPage() {
  const { id } = useParams();
  const [employee, setEmployee] = useState(null);
  const [history, setHistory] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const [emp, hist] = await Promise.all([employeesApi.get(id), employeesApi.loginHistory(id)]);
      setEmployee(emp);
      setHistory(hist);
    } catch (err) {
      setError(err.message || "Could not load employee.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function toggleStatus() {
    setBusy(true);
    try {
      await employeesApi.setStatus(id, !employee.is_active);
      await load();
    } catch (err) {
      setError(err.message || "Could not update status.");
    } finally {
      setBusy(false);
    }
  }

  if (error) return <Alert>{error}</Alert>;
  if (!employee) return <p className="text-muted text-sm">Loading…</p>;

  return (
    <div className="max-w-3xl">
      <Link to="/admin/employees" className="text-xs text-muted hover:text-ink">
        ← Back to employees
      </Link>

      <div className="mt-3 flex items-start justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight">
            {employee.first_name} {employee.last_name}
          </h1>
          <p className="text-sm text-muted font-mono mt-1">{employee.employee_id}</p>
        </div>
        <Badge tone={employee.is_active ? "success" : "muted"}>{employee.is_active ? "Active" : "Deactivated"}</Badge>
      </div>

      <div className="mt-6 rounded-lg border border-line bg-white p-5 grid grid-cols-2 gap-y-3 text-sm">
        <div className="text-muted">Company email</div>
        <div className="font-mono">{employee.company_email}</div>
        <div className="text-muted">Personal email</div>
        <div className="font-mono">{employee.personal_email}</div>
        <div className="text-muted">Role</div>
        <div className="capitalize">{employee.role.replace("_", " ")}</div>
        <div className="text-muted">Department</div>
        <div>{employee.department || "—"}</div>
      </div>

      <div className="mt-4">
        <Button variant={employee.is_active ? "danger" : "primary"} onClick={toggleStatus} disabled={busy}>
          {employee.is_active ? "Deactivate account" : "Activate account"}
        </Button>
      </div>

      <h2 className="font-display text-base font-semibold mt-8 mb-3">Login history</h2>
      <div className="rounded-lg border border-line bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-black/[0.015] text-left text-xs uppercase tracking-wider text-muted">
              <th className="px-5 py-3 font-medium">When</th>
              <th className="px-5 py-3 font-medium">Result</th>
              <th className="px-5 py-3 font-medium">IP address</th>
              <th className="px-5 py-3 font-medium">User agent</th>
            </tr>
          </thead>
          <tbody>
            {history?.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-muted">
                  No login attempts recorded yet.
                </td>
              </tr>
            )}
            {history?.map((h, i) => (
              <tr key={i} className="border-b border-line last:border-0">
                <td className="px-5 py-3 font-mono text-xs">{new Date(h.login_at).toLocaleString()}</td>
                <td className="px-5 py-3">
                  <Badge tone={h.success ? "success" : "danger"}>
                    {h.success ? "Success" : h.failure_reason?.replace(/_/g, " ") || "Failed"}
                  </Badge>
                </td>
                <td className="px-5 py-3 font-mono text-xs text-muted">{h.ip_address || "—"}</td>
                <td className="px-5 py-3 text-xs text-muted truncate max-w-[220px]">{h.user_agent || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
