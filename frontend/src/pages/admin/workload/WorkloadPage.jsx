import { useEffect, useState } from "react";
import { aiApi } from "../../../api/ai";
import { Alert } from "../../../components/ui/Feedback";
import { Badge } from "../../../components/ui/Feedback";

const STATUS_TONE = { underutilized: "muted", healthy: "success", high_load: "warning", overloaded: "danger", unavailable: "muted" };

export default function WorkloadPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    aiApi
      .workloadSummary()
      .then(setData)
      .catch((err) => setError(err.message || "Could not load workload summary."));
  }, []);

  if (error) return <Alert>{error}</Alert>;
  if (!data) return <p className="text-sm text-muted">Loading…</p>;

  const maxLoad = Math.max(...data.team.map((t) => t.active_project_count), 1);

  return (
    <div className="max-w-6xl">
      <h1 className="font-display text-xl font-semibold tracking-tight mb-1">Workload & planning</h1>
      <p className="text-sm text-muted mb-6">
        AI workload intelligence from real capacity, assigned effort, tasks, leave, and availability records.
      </p>

      <div className="rounded-lg border border-line bg-ink text-white p-5 mb-6">
        <div className="flex items-center gap-2 mb-2">
          <span className="h-1.5 w-1.5 rounded-full bg-accent" />
          <span className="text-[11px] uppercase tracking-wider text-white/50">
            {data.ai_generated ? "Gemini-generated recommendation" : "Rule-based recommendation"}
          </span>
        </div>
        <p className="text-sm leading-relaxed">{data.recommendation}</p>
      </div>

      <div className="rounded-lg border border-line bg-white overflow-x-auto">
        <table className="w-full min-w-[900px] text-sm">
          <thead>
            <tr className="border-b border-line bg-black/[0.015] text-left text-xs uppercase tracking-wider text-muted">
              <th className="px-5 py-3 font-medium">Employee</th>
              <th className="px-5 py-3 font-medium">Role</th>
              <th className="px-5 py-3 font-medium">Active projects</th>
              <th className="px-5 py-3 font-medium">Capacity / assigned</th>
              <th className="px-5 py-3 font-medium">Utilization</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium">Task signals</th>
              <th className="px-5 py-3 font-medium">Unavailable (next 14d)</th>
            </tr>
          </thead>
          <tbody>
            {data.team.map((t) => (
              <tr key={t.user_id} className="border-b border-line last:border-0">
                <td className="px-5 py-3">{t.full_name}</td>
                <td className="px-5 py-3 capitalize"><Badge tone="muted">{t.role.replace("_", " ")}</Badge></td>
                <td className="px-5 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-20 rounded-full bg-black/[0.06] overflow-hidden">
                      <div
                        className="h-full bg-accent"
                        style={{ width: `${(t.active_project_count / maxLoad) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono">{t.active_project_count}</span>
                  </div>
                </td>
                <td className="px-5 py-3 text-xs font-mono">
                  {t.available_capacity_hours}h / {t.assigned_effort_hours}h
                </td>
                <td className="px-5 py-3 text-xs font-mono">
                  {t.utilization_percent == null ? "—" : `${t.utilization_percent}%`}
                </td>
                <td className="px-5 py-3">
                  <Badge tone={STATUS_TONE[t.workload_status] || "muted"}>{t.workload_status.replace("_", " ")}</Badge>
                </td>
                <td className="px-5 py-3 text-xs text-muted">
                  {t.active_task_count} active · {t.overdue_task_count} overdue · {t.blocked_task_count} blocked
                </td>
                <td className="px-5 py-3 text-xs text-muted">{t.unavailable_days_next_14} days</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
