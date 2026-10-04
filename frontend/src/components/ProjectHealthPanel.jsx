import { useEffect, useState } from "react";
import { dashboardApi } from "../api/dashboard";
import { Badge, Alert } from "./ui/Feedback";

const tone = { healthy: "success", watch: "warning", at_risk: "danger" };
const riskTone = { critical: "danger", high: "danger", medium: "warning", low: "muted" };

export default function ProjectHealthPanel({ projectId }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      setData(await dashboardApi.projectHealth(projectId));
      setError("");
    } catch (err) {
      setError(err.message || "Could not load project health.");
    }
  }

  useEffect(() => { load(); }, [projectId]);

  if (error) return <Alert>{error}</Alert>;
  if (!data) return <p className="text-sm text-muted">Loading project health…</p>;

  const components = [
    ["Schedule", data.components.schedule],
    ["Sprint", data.components.sprint],
    ["Quality", data.components.quality],
    ["Capacity", data.components.capacity],
  ];

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-line bg-white p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-wider text-muted">Unified project health</p>
            <div className="flex items-end gap-3 mt-1">
              <span className="font-display text-4xl font-semibold">{data.overall_health}</span>
              <span className="text-sm text-muted pb-1">/ 100</span>
            </div>
          </div>
          <Badge tone={tone[data.health_label] || "muted"}>{data.health_label.replace("_", " ")}</Badge>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-5">
          {components.map(([label, value]) => (
            <div key={label} className="rounded-lg bg-black/[0.025] p-3">
              <div className="flex justify-between text-xs mb-2"><span>{label}</span><b>{value}%</b></div>
              <div className="h-2 rounded-full bg-black/10 overflow-hidden">
                <div className="h-full rounded-full bg-accent" style={{ width: `${value}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Signal label="Active tasks" value={data.signals.active_tasks} />
        <Signal label="Overdue" value={data.signals.overdue_tasks} />
        <Signal label="Open bugs" value={data.signals.open_bugs} />
        <Signal label="Critical bugs" value={data.signals.critical_bugs} />
      </div>

      <section className="rounded-xl border border-line bg-white overflow-hidden">
        <div className="p-4 border-b border-line"><h2 className="font-semibold">Detected risks</h2></div>
        {data.risks.length === 0 ? (
          <p className="p-5 text-sm text-muted">No current risk signals detected from the database.</p>
        ) : data.risks.map((risk, index) => (
          <div key={`${risk.type}-${index}`} className="p-4 border-b border-line last:border-0 flex gap-3 items-start">
            <Badge tone={riskTone[risk.severity] || "muted"}>{risk.severity}</Badge>
            <div><p className="text-sm font-medium">{risk.title}</p><p className="text-xs text-muted mt-1">{risk.detail}</p></div>
          </div>
        ))}
      </section>

      <section className="rounded-xl border border-line bg-white p-5">
        <h2 className="font-semibold mb-3">Recommended actions</h2>
        <ul className="space-y-2 text-sm">
          {data.recommendations.map((item, index) => <li key={index} className="flex gap-2"><span className="text-accent">→</span><span>{item}</span></li>)}
        </ul>
        <p className="text-[11px] text-muted mt-4">Health is computed from current SprintNova records; it does not automatically modify tasks or project data.</p>
      </section>
    </div>
  );
}

function Signal({ label, value }) {
  return <div className="rounded-lg border border-line bg-white p-4"><p className="text-xs text-muted">{label}</p><p className="font-display text-2xl font-semibold mt-1">{value}</p></div>;
}
