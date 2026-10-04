import { useEffect, useState } from "react";
import { dashboardApi } from "../api/dashboard";
import { Badge, Alert } from "./ui/Feedback";
import { useRealtime } from "../hooks/useRealtime";

const tone = { healthy: "success", watch: "warning", at_risk: "danger" };

export default function ManagementIntelligence() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try { setData(await dashboardApi.me()); setError(""); }
    catch (e) { setError(e.message || "Unable to load management intelligence."); }
  }

  useEffect(() => { load(); }, []);
  useRealtime({ onEvent: (event) => {
    if (["task.", "bug.", "sprint.", "daily_update.", "work_session.", "availability.", "leave."].some(prefix => event.type?.startsWith(prefix))) load();
  }});

  if (error) return <Alert>{error}</Alert>;
  if (!data) return <p className="text-sm text-muted">Loading project intelligence…</p>;

  return <div className="space-y-5 mt-6">
    <section className="rounded-xl border border-line bg-white p-5">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div><h2 className="font-semibold">Project intelligence</h2><p className="text-xs text-muted mt-1">Live health signals from tasks, quality, capacity and daily reporting.</p></div>
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {(data.project_health || []).map(p => <div key={p.project_id} className="rounded-lg border border-line p-4">
          <div className="flex items-start justify-between gap-2"><div><p className="font-mono text-[11px] text-muted">{p.project_code}</p><p className="font-medium text-sm mt-1">{p.project_name}</p></div><Badge tone={tone[p.health_label] || "muted"}>{p.overall_health}/100</Badge></div>
          <p className="text-xs text-muted mt-3">{p.risk_count} active risk signal{p.risk_count === 1 ? "" : "s"}</p>
        </div>)}
      </div>
    </section>

    <section className="grid gap-5 lg:grid-cols-2">
      <div className="rounded-xl border border-line bg-white p-5">
        <h2 className="font-semibold">Team capacity</h2>
        <div className="space-y-3 mt-4">
          {(data.team_workload || []).slice(0, 8).map(w => <div key={w.user_id} className="flex items-center justify-between text-sm"><span>{w.full_name}</span><span className="text-muted">{w.active_project_count} active project{w.active_project_count === 1 ? "" : "s"} · {w.unavailable_days_next_14} unavailable day{w.unavailable_days_next_14 === 1 ? "" : "s"}</span></div>)}
          {!data.team_workload?.length && <p className="text-sm text-muted">No project team members found.</p>}
        </div>
      </div>
      <div className="rounded-xl border border-line bg-white p-5">
        <div className="flex items-center gap-2"><h2 className="font-semibold">AI workload recommendation</h2>{data.workload_ai_generated && <Badge tone="accent">AI</Badge>}</div>
        <p className="text-sm text-ink/80 leading-6 mt-3">{data.workload_recommendation}</p>
        <p className="text-[11px] text-muted mt-4">Recommendation is advisory. SprintNova does not automatically reassign work.</p>
      </div>
    </section>
  </div>;
}
