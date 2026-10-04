import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, Doughnut } from "react-chartjs-2";
import "../../../components/charts/chartSetup";
import { CHART_COLORS, chartBaseOptions } from "../../../components/charts/chartSetup";
import { dashboardApi } from "../../../api/dashboard";
import { useAuth } from "../../../context/AuthContext";
import { Badge, Alert } from "../../../components/ui/Feedback";

export default function DashboardPage() {
  const { session } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    dashboardApi
      .me()
      .then(setData)
      .catch((err) => setError(err.message || "Could not load your dashboard."));
  }, []);

  if (error) return <Alert>{error}</Alert>;
  if (!data) return <p className="text-sm text-muted">Loading…</p>;

  return (
    <div>
      <h1 className="font-display text-xl font-semibold tracking-tight mb-1">Dashboard</h1>
      <p className="text-sm text-muted mb-6">
        Welcome back, {session?.fullName} — here's what's real right now, computed from the database.
      </p>

      {session?.role === "owner_admin" && <AdminDashboard data={data} />}
      {session?.role === "product_owner" && <ProductOwnerDashboard data={data} />}
      {session?.role === "project_manager" && <ManagementDashboard data={data} title="Project Manager" />}
      {session?.role === "team_lead" && <ManagementDashboard data={data} title="Team Lead" />}
      {session?.role === "scrum_master" && <ScrumMasterDashboard data={data} />}
      {session?.role === "developer" && <DeveloperDashboard data={data} />}
      {session?.role === "tester" && <TesterDashboard data={data} />}
      {session?.role === "client" && <ClientDashboard data={data} />}
    </div>
  );
}

function StatCard({ label, value, tone = "text-ink" }) {
  return (
    <div className="rounded-lg border border-line bg-white p-4">
      <div className={`font-display text-2xl font-semibold ${tone}`}>{value}</div>
      <div className="text-xs text-muted mt-1">{label}</div>
    </div>
  );
}

function ChartCard({ title, height = 220, children }) {
  return (
    <div className="rounded-lg border border-line bg-white p-4">
      <p className="text-sm font-medium mb-3">{title}</p>
      <div style={{ height }}>{children}</div>
    </div>
  );
}

// --- Admin ---

function AdminDashboard({ data }) {
  const statusLabels = Object.keys(data.project_status_distribution);
  const statusColors = { planning: CHART_COLORS.muted, active: CHART_COLORS.accent, on_hold: CHART_COLORS.warning, completed: CHART_COLORS.success, cancelled: CHART_COLORS.danger };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Employees" value={data.total_employees} />
        <StatCard label="Total projects" value={data.total_projects} />
        <StatCard label="Active projects" value={data.active_projects} tone="text-accent" />
        <StatCard label="Completed" value={data.completed_projects} tone="text-success" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ChartCard title="Project status distribution">
          {statusLabels.length === 0 ? (
            <EmptyChart />
          ) : (
            <Doughnut
              data={{
                labels: statusLabels.map((s) => s.replace("_", " ")),
                datasets: [{
                  data: statusLabels.map((s) => data.project_status_distribution[s]),
                  backgroundColor: statusLabels.map((s) => statusColors[s] || CHART_COLORS.muted),
                }],
              }}
              options={chartBaseOptions}
            />
          )}
        </ChartCard>

        <ChartCard title="Employee workload (active projects)">
          {data.employee_workload.length === 0 ? (
            <EmptyChart />
          ) : (
            <Bar
              data={{
                labels: data.employee_workload.map((w) => w.full_name),
                datasets: [{ label: "Active projects", data: data.employee_workload.map((w) => w.active_project_count), backgroundColor: CHART_COLORS.accent }],
              }}
              options={{ ...chartBaseOptions, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }}
            />
          )}
        </ChartCard>
      </div>

      <div className="rounded-lg border border-line bg-white p-4">
        <div className="flex items-center justify-between mb-3"><div><p className="text-sm font-medium">Organization project health</p><p className="text-xs text-muted mt-1">Live delivery and capacity signals across projects.</p></div></div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {(data.project_health || []).map((p) => <Link key={p.project_id} to={`/admin/projects/${p.project_id}`} className="rounded-lg border border-line p-3 hover:bg-black/[0.02]"><div className="flex items-center justify-between gap-2"><span className="text-sm font-medium">{p.project_name}</span><Badge tone={p.health_label === "healthy" ? "success" : p.health_label === "watch" ? "warning" : "danger"}>{p.overall_health}/100</Badge></div><p className="text-xs text-muted mt-2">{p.risk_count} active risk signal{p.risk_count === 1 ? "" : "s"}</p></Link>)}
          {!data.project_health?.length && <p className="text-sm text-muted">No projects yet.</p>}
        </div>
        <p className="text-xs text-muted mt-4"><b>Capacity recommendation:</b> {data.workload_recommendation}</p>
      </div>

      <div className="rounded-lg border border-line bg-white p-4">
        <p className="text-sm font-medium mb-3">Leave requests</p>
        <div className="flex gap-6">
          <span className="text-sm"><Badge tone="warning">{data.leave_stats.pending}</Badge> pending</span>
          <span className="text-sm"><Badge tone="success">{data.leave_stats.approved}</Badge> approved</span>
          <span className="text-sm"><Badge tone="danger">{data.leave_stats.rejected}</Badge> rejected</span>
        </div>
      </div>
    </div>
  );
}

// --- Product Owner ---

function ProductOwnerDashboard({ data }) {
  const priorityLabels = data.backlog_priority_counts.map((p) => p.priority);
  const velocityProjects = Object.keys(data.latest_velocity_by_project);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ChartCard title="Backlog by priority (not yet done)">
          {priorityLabels.length === 0 ? <EmptyChart /> : (
            <Bar
              data={{
                labels: priorityLabels,
                datasets: [{ data: data.backlog_priority_counts.map((p) => p.count), backgroundColor: CHART_COLORS.accent }],
              }}
              options={{ ...chartBaseOptions, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }}
            />
          )}
        </ChartCard>

        <ChartCard title="Average velocity by project">
          {velocityProjects.length === 0 ? <EmptyChart label="No completed sprints yet." /> : (
            <Bar
              data={{
                labels: velocityProjects,
                datasets: [{ data: velocityProjects.map((p) => data.latest_velocity_by_project[p]), backgroundColor: CHART_COLORS.success }],
              }}
              options={{ ...chartBaseOptions, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }}
            />
          )}
        </ChartCard>
      </div>

      <ListSection title="My projects" empty="No projects yet.">
        {data.projects.map((p) => (
          <Link key={p.id} to={`/admin/projects/${p.id}`} className="flex items-center justify-between px-4 py-3 hover:bg-black/[0.02]">
            <span className="text-sm font-medium">{p.name} <span className="text-muted font-mono text-xs">{p.code}</span></span>
            <span className="text-xs font-mono text-muted">{p.percent_complete}%</span>
          </Link>
        ))}
      </ListSection>

      <ListSection title="Active sprints" empty="No active sprints.">
        {data.active_sprints.map((s) => (
          <div key={s.id} className="flex items-center justify-between px-4 py-3">
            <span className="text-sm">{s.name} <span className="text-muted font-mono text-xs">{s.project_code}</span></span>
            <span className="text-xs font-mono text-muted">{s.completed_points}/{s.total_points} pts</span>
          </div>
        ))}
      </ListSection>
    </div>
  );
}

// --- Scrum Master ---

function ScrumMasterDashboard({ data }) {
  return (
    <div className="space-y-6">
      <ChartCard title="Active sprint progress (points)">
        {data.active_sprints.length === 0 ? <EmptyChart /> : (
          <Bar
            data={{
              labels: data.active_sprints.map((s) => `${s.project_code} · ${s.name}`),
              datasets: [
                { label: "Completed", data: data.active_sprints.map((s) => s.completed_points), backgroundColor: CHART_COLORS.success },
                { label: "Remaining", data: data.active_sprints.map((s) => s.total_points - s.completed_points), backgroundColor: CHART_COLORS.muted },
              ],
            }}
            options={{ ...chartBaseOptions, scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } } }}
          />
        )}
      </ChartCard>

      <ChartCard title="Team workload (active projects)">
        {data.team_workload.length === 0 ? <EmptyChart /> : (
          <Bar
            data={{
              labels: data.team_workload.map((w) => w.full_name),
              datasets: [{ data: data.team_workload.map((w) => w.active_project_count), backgroundColor: CHART_COLORS.accent }],
            }}
            options={{ ...chartBaseOptions, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }}
          />
        )}
      </ChartCard>

      <ListSection title="Blocked or stale tasks (5+ days without progress)" empty="Nothing stuck right now.">
        {data.blocked_or_stale_tasks.map((t, i) => (
          <div key={i} className="flex items-center justify-between px-4 py-3">
            <span className="text-sm">{t.title} <span className="text-muted font-mono text-xs">{t.key}</span></span>
            <Badge tone="warning">{t.days_stale}d stale</Badge>
          </div>
        ))}
      </ListSection>
    </div>
  );
}

// --- Developer ---

function DeveloperDashboard({ data }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-3">
        <StatCard label="My tasks" value={data.my_tasks.length} />
        <StatCard label="Due today" value={data.tasks_due_today.length} tone="text-warning" />
        <StatCard label="Overdue" value={data.tasks_overdue.length} tone="text-danger" />
      </div>

      <ListSection title="Overdue tasks" empty="Nothing overdue — good shape.">
        {data.tasks_overdue.map((t) => (
          <div key={t.key} className="flex items-center justify-between px-4 py-3">
            <span className="text-sm">{t.title} <span className="text-muted font-mono text-xs">{t.key}</span></span>
            <span className="text-xs font-mono text-danger">{t.due_date}</span>
          </div>
        ))}
      </ListSection>

      <ListSection title="Current sprints" empty="Not in an active sprint right now.">
        {data.current_sprints.map((s) => (
          <div key={s.id} className="flex items-center justify-between px-4 py-3">
            <span className="text-sm">{s.name} <span className="text-muted font-mono text-xs">{s.project_code}</span></span>
            <span className="text-xs font-mono text-muted">{s.completed_points}/{s.total_points} pts</span>
          </div>
        ))}
      </ListSection>

      <ListSection title="Bugs assigned to me" empty="No bugs assigned.">
        {data.bugs_assigned.map((b) => (
          <div key={b.key} className="flex items-center justify-between px-4 py-3">
            <span className="text-sm">{b.title} <span className="text-muted font-mono text-xs">{b.key}</span></span>
            <Badge tone={b.severity === "critical" ? "danger" : "warning"}>{b.severity}</Badge>
          </div>
        ))}
      </ListSection>

      <ListSection title="Recent notifications" empty="You're all caught up.">
        {data.recent_notifications.map((n, i) => (
          <div key={i} className="flex items-center justify-between px-4 py-3">
            <span className={`text-sm ${!n.is_read ? "font-medium" : "text-muted"}`}>{n.title}</span>
            <span className="text-xs text-muted">{new Date(n.created_at).toLocaleDateString()}</span>
          </div>
        ))}
      </ListSection>
    </div>
  );
}

// --- Tester ---

function TesterDashboard({ data }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="grid grid-cols-2 gap-3">
          <StatCard label="Test cases" value={data.test_cases_total} />
          <StatCard label="Pass rate" value={`${data.testing_progress_percent}%`} tone="text-accent" />
          <StatCard label="Passed" value={data.tests_passed} tone="text-success" />
          <StatCard label="Failed" value={data.tests_failed} tone="text-danger" />
        </div>
        <ChartCard title="Pass / fail split">
          {data.tests_passed + data.tests_failed === 0 ? <EmptyChart /> : (
            <Doughnut
              data={{ labels: ["Passed", "Failed"], datasets: [{ data: [data.tests_passed, data.tests_failed], backgroundColor: [CHART_COLORS.success, CHART_COLORS.danger] }] }}
              options={chartBaseOptions}
            />
          )}
        </ChartCard>
      </div>

      <ListSection title="Open bugs" empty="No open bugs.">
        {data.open_bugs.map((b) => (
          <div key={b.key} className="flex items-center justify-between px-4 py-3">
            <span className="text-sm">{b.title} <span className="text-muted font-mono text-xs">{b.key}</span></span>
            <Badge tone={b.severity === "critical" ? "danger" : "warning"}>{b.severity}</Badge>
          </div>
        ))}
      </ListSection>

      <ListSection title="Awaiting retest" empty="Nothing waiting on retest.">
        {data.bugs_awaiting_retest.map((b) => (
          <div key={b.key} className="flex items-center justify-between px-4 py-3">
            <span className="text-sm">{b.title} <span className="text-muted font-mono text-xs">{b.key}</span></span>
          </div>
        ))}
      </ListSection>
    </div>
  );
}

// --- Client ---

function ClientDashboard({ data }) {
  return (
    <div className="space-y-4">
      {data.projects.length === 0 && (
        <p className="text-sm text-muted">No projects have been shared with you yet.</p>
      )}
      {data.projects.map((p) => (
        <div key={p.id} className="rounded-lg border border-line bg-white p-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-display font-semibold">{p.name}</h3>
            <Badge tone="accent">{p.status.replace("_", " ")}</Badge>
          </div>
          <div className="h-2 rounded-full bg-black/[0.06] overflow-hidden mb-3">
            <div className="h-full bg-accent" style={{ width: `${p.percent_complete}%` }} />
          </div>
          <p className="text-xs text-muted mb-4">{p.percent_complete}% complete</p>

          {p.current_sprint_name && (
            <p className="text-sm mb-3">
              Current sprint: <span className="font-medium">{p.current_sprint_name}</span>{" "}
              <span className="text-muted">({p.current_sprint_status})</span>
            </p>
          )}

          {p.milestones.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-muted mb-2">Milestones</p>
              <div className="space-y-1.5">
                {p.milestones.map((m, i) => (
                  <div key={i} className="flex items-center justify-between text-sm">
                    <span>{m.title}</span>
                    <Badge tone={m.status === "completed" ? "success" : "muted"}>{m.status.replace("_", " ")}</Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// --- Shared bits ---

function ListSection({ title, empty, children }) {
  const hasChildren = Array.isArray(children) ? children.length > 0 : !!children;
  return (
    <div className="rounded-lg border border-line bg-white overflow-hidden">
      <p className="text-sm font-medium px-4 py-3 border-b border-line bg-black/[0.015]">{title}</p>
      {hasChildren ? <div className="divide-y divide-line">{children}</div> : (
        <p className="text-sm text-muted px-4 py-6 text-center">{empty}</p>
      )}
    </div>
  );
}

function EmptyChart({ label = "No data yet." }) {
  return <div className="h-full flex items-center justify-center text-xs text-muted">{label}</div>;
}

function ManagementDashboard({ data, title }) { return <div className="space-y-5"><div className="grid grid-cols-2 md:grid-cols-4 gap-3"><StatCard label="Projects" value={data.projects.length}/><StatCard label="Team members" value={data.team_members}/><StatCard label="Working now" value={data.active_team_members}/><StatCard label="Overdue tasks" value={data.overdue_tasks} tone="text-danger"/></div><ListSection title={`${title} risks`} empty="No current risk items.">{data.risks.map((r,i)=><div key={i} className="px-4 py-3 text-sm border-b last:border-0"><b>{r.key}</b> — {r.reason}</div>)}</ListSection></div>; }
