import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { projectsApi } from "../../../api/projects";
import { employeesApi } from "../../../api/employees";
import { aiApi } from "../../../api/ai";
import { Badge, Alert } from "../../../components/ui/Feedback";
import { Button } from "../../../components/ui/Button";
import { Field, Input, Select } from "../../../components/ui/Field";
import { Tabs } from "../../../components/ui/Tabs";
import { ProjectProgressChart } from "../../../components/ProjectProgressChart";
import BacklogTab from "./BacklogTab";
import SprintsTab from "./SprintsTab";
import KanbanBoard from "./KanbanBoard";
import TestingTab from "./TestingTab";
import BugsTab from "./BugsTab";
import QualityTab from "./QualityTab";
import DocumentsTab from "./DocumentsTab";
import AttachmentsTab from "./AttachmentsTab";
import AssistantTab from "./AssistantTab";
import ProjectHealthPanel from "../../../components/ProjectHealthPanel";
import { useRealtime } from "../../../hooks/useRealtime";

const STATUS_TONE = { planning: "muted", active: "success", on_hold: "warning", completed: "accent", cancelled: "danger" };
const PROJECT_ROLES = ["product_owner", "project_manager", "scrum_master", "team_lead", "developer", "tester", "client_viewer"];

export default function ProjectDetailPage() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [milestones, setMilestones] = useState(null);
  const [progress, setProgress] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [tab, setTab] = useState("overview");
  const [error, setError] = useState("");

  async function load() {
    try {
      const [p, m, pr] = await Promise.all([
        projectsApi.get(id), projectsApi.listMilestones(id), projectsApi.progress(id),
      ]);
      setProject(p);
      setMilestones(m);
      setProgress(pr);
    } catch (err) {
      setError(err.message || "Could not load project.");
    }
  }

  useEffect(() => {
    load();
    employeesApi.list().then(setEmployees).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useRealtime({ projectId: id, onEvent: (event) => {
    if (event.type.startsWith("project.") || event.type.startsWith("task.") || event.type.startsWith("sprint.") || event.type.startsWith("story.") || event.type.startsWith("bug.") || event.type.startsWith("test_case.") || event.type.startsWith("daily_update.")) load();
  }});

  if (error) return <Alert>{error}</Alert>;
  if (!project) return <p className="text-sm text-muted">Loading…</p>;

  return (
    <div className="max-w-5xl">
      <Link to="/admin/projects" className="text-xs text-muted hover:text-ink">
        ← Back to projects
      </Link>

      <div className="mt-3 flex items-start justify-between">
        <div>
          <p className="font-mono text-xs text-muted">{project.code}</p>
          <h1 className="font-display text-xl font-semibold tracking-tight">{project.name}</h1>
        </div>
        <Badge tone={STATUS_TONE[project.status]}>{project.status.replace("_", " ")}</Badge>
      </div>

      <Tabs
        tabs={[
          { value: "overview", label: "Overview" },
          { value: "health", label: "Project Health" },
          { value: "team", label: `Team (${project.members.length})` },
          { value: "backlog", label: "Backlog" },
          { value: "sprints", label: "Sprints" },
          { value: "kanban", label: "Kanban" },
          { value: "testing", label: "Testing" },
          { value: "bugs", label: "Bugs" },
          { value: "quality", label: "Quality" },
          { value: "documents", label: "Documents" },
          { value: "files", label: "Files" },
          { value: "assistant", label: "Assistant" },
          { value: "milestones", label: `Milestones (${milestones?.length ?? 0})` },
          { value: "roadmap", label: "Roadmap" },
          { value: "ai", label: "AI Suggestions" },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === "overview" && <OverviewTab project={project} progress={progress} onChange={load} />}
      {tab === "health" && <ProjectHealthPanel projectId={project.id} />}
      {tab === "backlog" && <BacklogTab projectId={project.id} members={project.members} />}
      {tab === "sprints" && <SprintsTab projectId={project.id} />}
      {tab === "kanban" && <KanbanBoard projectId={project.id} members={project.members} />}
      {tab === "testing" && <TestingTab projectId={project.id} />}
      {tab === "bugs" && <BugsTab projectId={project.id} members={project.members} />}
      {tab === "quality" && <QualityTab projectId={project.id} members={project.members} />}
      {tab === "documents" && <DocumentsTab projectId={project.id} />}
      {tab === "files" && <AttachmentsTab projectId={project.id} />}
      {tab === "assistant" && <AssistantTab projectId={project.id} />}
      {tab === "roadmap" && <RoadmapTab projectId={project.id} />}
      {tab === "ai" && <AllocationTab projectId={project.id} />}
      {tab === "team" && (
        <TeamTab project={project} employees={employees} onChange={load} />
      )}
      {tab === "milestones" && (
        <MilestonesTab projectId={project.id} milestones={milestones} onChange={load} />
      )}
    </div>
  );
}

function OverviewTab({ project, progress, onChange }) {
  const [status, setStatus] = useState(project.status);
  const [saving, setSaving] = useState(false);

  async function updateStatus(e) {
    const value = e.target.value;
    setStatus(value);
    setSaving(true);
    try {
      await projectsApi.update(project.id, { status: value });
      onChange();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="rounded-lg border border-line bg-white p-5 space-y-4">
        {project.description && <p className="text-sm text-ink/80">{project.description}</p>}
        <dl className="grid grid-cols-2 gap-y-3 text-sm">
          <dt className="text-muted">Start date</dt>
          <dd>{project.start_date || "—"}</dd>
          <dt className="text-muted">End date</dt>
          <dd>{project.end_date || "—"}</dd>
        </dl>
        <div className="max-w-xs">
          <Field label="Status" htmlFor="status">
            <Select id="status" value={status} onChange={updateStatus} disabled={saving}>
              {Object.keys(STATUS_TONE).map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      </div>

      <ProjectProgressChart progress={progress} />
    </div>
  );
}

function TeamTab({ project, employees, onChange }) {
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState("developer");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const memberIds = new Set(project.members.map((m) => m.user_id));
  const available = employees.filter((e) => !memberIds.has(e.id));

  async function handleAdd(e) {
    e.preventDefault();
    if (!userId) return;
    setBusy(true);
    setError("");
    try {
      await projectsApi.addMember(project.id, { user_id: Number(userId), project_role: role });
      setUserId("");
      onChange();
    } catch (err) {
      setError(err.message || "Could not add team member.");
    } finally {
      setBusy(false);
    }
  }

  async function handleRemove(memberId) {
    setBusy(true);
    try {
      await projectsApi.removeMember(project.id, memberId);
      onChange();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-3 mb-5 rounded-lg border border-line bg-white p-4">
        <div className="min-w-[200px]">
          <Field label="Add employee" htmlFor="member_user">
            <Select id="member_user" value={userId} onChange={(e) => setUserId(e.target.value)}>
              <option value="">Choose…</option>
              {available.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.first_name} {e.last_name}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        <div className="min-w-[160px]">
          <Field label="Project role" htmlFor="member_role">
            <Select id="member_role" value={role} onChange={(e) => setRole(e.target.value)}>
              {PROJECT_ROLES.map((r) => (
                <option key={r} value={r}>
                  {r.replace("_", " ")}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        <Button type="submit" disabled={!userId || busy}>
          Add to team
        </Button>
      </form>

      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      <div className="rounded-lg border border-line bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-black/[0.015] text-left text-xs uppercase tracking-wider text-muted">
              <th className="px-5 py-3 font-medium">Name</th>
              <th className="px-5 py-3 font-medium">Company email</th>
              <th className="px-5 py-3 font-medium">Project role</th>
              <th className="px-5 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {project.members.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-muted">No team members yet.</td>
              </tr>
            )}
            {project.members.map((m) => (
              <tr key={m.id} className="border-b border-line last:border-0">
                <td className="px-5 py-3">{m.full_name}</td>
                <td className="px-5 py-3 font-mono text-xs">{m.company_email}</td>
                <td className="px-5 py-3 capitalize">{m.project_role.replace("_", " ")}</td>
                <td className="px-5 py-3 text-right">
                  <button
                    onClick={() => handleRemove(m.id)}
                    disabled={busy}
                    className="text-xs font-medium text-danger hover:underline disabled:opacity-50"
                  >
                    Remove
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

function MilestonesTab({ projectId, milestones, onChange }) {
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleAdd(e) {
    e.preventDefault();
    if (!title) return;
    setBusy(true);
    try {
      const payload = { title };
      if (dueDate) payload.due_date = dueDate;
      await projectsApi.createMilestone(projectId, payload);
      setTitle("");
      setDueDate("");
      onChange();
    } finally {
      setBusy(false);
    }
  }

  async function updateStatus(milestoneId, status) {
    setBusy(true);
    try {
      await projectsApi.updateMilestone(projectId, milestoneId, { status });
      onChange();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-3 mb-5 rounded-lg border border-line bg-white p-4">
        <div className="flex-1 min-w-[220px]">
          <Field label="Milestone title" htmlFor="milestone_title">
            <Input id="milestone_title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </Field>
        </div>
        <div className="min-w-[160px]">
          <Field label="Due date" htmlFor="milestone_due">
            <Input id="milestone_due" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </Field>
        </div>
        <Button type="submit" disabled={!title || busy}>
          Add milestone
        </Button>
      </form>

      <ul className="space-y-2">
        {milestones?.length === 0 && (
          <li className="rounded-lg border border-dashed border-line p-6 text-center text-sm text-muted">
            No milestones yet.
          </li>
        )}
        {milestones?.map((m) => (
          <li key={m.id} className="rounded-lg border border-line bg-white p-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-sm">{m.title}</p>
              {m.due_date && <p className="text-xs text-muted font-mono mt-0.5">Due {m.due_date}</p>}
            </div>
            <Select
              value={m.status}
              onChange={(e) => updateStatus(m.id, e.target.value)}
              disabled={busy}
              className="w-auto text-xs py-1.5"
            >
              <option value="pending">Pending</option>
              <option value="in_progress">In progress</option>
              <option value="completed">Completed</option>
              <option value="missed">Missed</option>
            </Select>
          </li>
        ))}
      </ul>
    </div>
  );
}

function RoadmapTab({ projectId }) {
  const [roadmap, setRoadmap] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    projectsApi
      .roadmap(projectId)
      .then(setRoadmap)
      .catch((err) => setError(err.message || "Could not load roadmap."));
  }, [projectId]);

  if (error) return <Alert>{error}</Alert>;
  if (!roadmap) return <p className="text-sm text-muted">Loading…</p>;

  if (roadmap.phases.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-line p-10 text-center text-sm text-muted">
        No milestones yet — add some in the Milestones tab, optionally with a phase, to see them here as a roadmap.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {roadmap.phases.map((phase) => (
        <div key={phase.phase}>
          <h3 className="font-display font-semibold text-sm mb-2 flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            {phase.phase}
          </h3>
          <div className="ml-3 pl-4 border-l-2 border-line space-y-2">
            {phase.milestones.map((m) => (
              <div key={m.id} className="rounded-md border border-line bg-white px-4 py-2.5 flex items-center justify-between">
                <span className="text-sm">{m.title}</span>
                <div className="flex items-center gap-3">
                  {m.due_date && <span className="text-xs font-mono text-muted">{m.due_date}</span>}
                  <Badge tone={m.status === "completed" ? "success" : m.status === "missed" ? "danger" : "muted"}>
                    {m.status.replace("_", " ")}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function AllocationTab({ projectId }) {
  const [data, setData] = useState(null);
  const [plan, setPlan] = useState(null);
  const [risk, setRisk] = useState(null);
  const [quality, setQuality] = useState(null);
  const [completion, setCompletion] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    aiApi
      .teamAllocation(projectId)
      .then(setData)
      .catch((err) => setError(err.message || "Could not load suggestions."));
    aiApi
      .sprintPlanning(projectId)
      .then(setPlan)
      .catch(() => {}); // sprint planning is a bonus section; don't block the tab on it
    aiApi
      .taskRisk(projectId)
      .then(setRisk)
      .catch(() => {}); // same — task risk is a bonus section
    aiApi
      .qualityRisk(projectId)
      .then(setQuality)
      .catch(() => {}); // quality risk is optional
    aiApi
      .completionPrediction(projectId)
      .then(setCompletion)
      .catch(() => {}); // completion forecast is optional
  }, [projectId]);

  if (error) return <Alert>{error}</Alert>;
  if (!data) return <p className="text-sm text-muted">Loading…</p>;

  return (
    <div className="space-y-8">
      <div>
        <h3 className="font-display font-semibold text-sm mb-3">Team allocation</h3>
        <div className="space-y-5">
          <div className="rounded-lg border border-line bg-ink text-white p-5">
            <div className="flex items-center gap-2 mb-2">
              <span className="h-1.5 w-1.5 rounded-full bg-accent" />
              <span className="text-[11px] uppercase tracking-wider text-white/50">
                {data.ai_generated ? "Gemini-generated recommendation" : "Rule-based recommendation"}
              </span>
            </div>
            <p className="text-sm leading-relaxed">{data.recommendation}</p>
          </div>

          {data.missing_roles.length === 0 ? (
            <p className="text-sm text-muted">All core project roles are staffed.</p>
          ) : (
            <div className="space-y-3">
              {data.missing_roles.map((role) => (
                <div key={role} className="rounded-lg border border-line bg-white p-4">
                  <p className="text-sm font-medium capitalize mb-2">{role.replace("_", " ")} — unfilled</p>
                  {data.candidates_by_role[role]?.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {data.candidates_by_role[role].map((c) => (
                        <span key={c.user_id} className="text-xs bg-black/[0.04] px-2.5 py-1 rounded-full">
                          {c.full_name} · {c.active_project_count} active
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted">No available employee currently holds this org role.</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {plan && (
        <div>
          <h3 className="font-display font-semibold text-sm mb-3">Sprint planning</h3>
          <div className="space-y-4">
            <div className="rounded-lg border border-line bg-ink text-white p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-white/50">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                  {plan.ai_generated ? "Gemini-generated recommendation" : "Rule-based recommendation"}
                </span>
                <span className="text-xs font-mono text-white/70">
                  capacity {plan.recommended_capacity} pts{plan.capacity_is_default ? " (default)" : ""}
                </span>
              </div>
              <p className="text-sm leading-relaxed">{plan.recommendation}</p>
            </div>

            {plan.recommended_stories.length > 0 && (
              <StoryPlanList title="Recommended for next sprint" tone="success" stories={plan.recommended_stories} />
            )}
            {plan.postponed_stories.length > 0 && (
              <StoryPlanList title="Suggested to postpone" tone="muted" stories={plan.postponed_stories} />
            )}
            {plan.needs_estimation.length > 0 && (
              <StoryPlanList title="Needs story points before planning" tone="warning" stories={plan.needs_estimation} />
            )}
          </div>
        </div>
      )}

      {risk && (
        <div>
          <h3 className="font-display font-semibold text-sm mb-3">Task risk</h3>
          <div className="space-y-4">
            <div className="rounded-lg border border-line bg-ink text-white p-5">
              <div className="flex items-center gap-2 mb-2">
                <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                <span className="text-[11px] uppercase tracking-wider text-white/50">
                  {risk.ai_generated ? "Gemini-generated recommendation" : "Rule-based recommendation"}
                </span>
              </div>
              <p className="text-sm leading-relaxed">{risk.recommendation}</p>
            </div>
            {risk.overdue_tasks.length > 0 && (
              <TaskRiskList title="⚠️ Overdue" tone="danger" tasks={risk.overdue_tasks} />
            )}
            {risk.at_risk_tasks.length > 0 && (
              <TaskRiskList title="Due within 2 days" tone="warning" tasks={risk.at_risk_tasks} />
            )}
            {risk.over_estimate_tasks.length > 0 && (
              <TaskRiskList title="Over time estimate" tone="muted" tasks={risk.over_estimate_tasks} />
            )}
            {risk.overdue_tasks.length === 0 && risk.at_risk_tasks.length === 0 && risk.over_estimate_tasks.length === 0 && (
              <p className="text-sm text-muted">No overdue, at-risk, or over-estimate tasks right now.</p>
            )}
          </div>
        </div>
      )}

      {completion && (
        <div>
          <h3 className="font-display font-semibold text-sm mb-3">AI completion forecast</h3>
          <div className="rounded-lg border border-line bg-white p-5 space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <QualityStat label="Forecast date" value={completion.predicted_completion_date} />
              <QualityStat label="Confidence" value={completion.confidence} />
              <QualityStat label="Remaining points" value={completion.remaining_story_points} />
              <QualityStat label="Remaining tasks" value={completion.remaining_tasks} />
              <QualityStat label="Overdue tasks" value={completion.overdue_tasks} />
            </div>
            <p className="text-sm text-ink/80">{completion.recommendation}</p>
            <p className="text-[11px] text-muted">Forecast source: {completion.provider}. The numeric date is calculated from real SprintNova delivery data.</p>
          </div>
        </div>
      )}

      {quality && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <h3 className="font-display font-semibold text-sm">Quality risk</h3>
            <Badge tone={quality.risk_level === "HIGH" ? "danger" : quality.risk_level === "MEDIUM" ? "warning" : "success"}>
              {quality.risk_level} · {quality.risk_score}%
            </Badge>
            <span className="text-[11px] text-muted">
              {quality.is_ml_prediction ? "ML-predicted" : "rule-based score"}
            </span>
          </div>
          <div className="space-y-4">
            <div className="rounded-lg border border-line bg-ink text-white p-5">
              <div className="flex items-center gap-2 mb-2">
                <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                <span className="text-[11px] uppercase tracking-wider text-white/50">
                  {quality.ai_generated ? "Gemini-generated recommendation" : "Rule-based recommendation"}
                </span>
              </div>
              <p className="text-sm leading-relaxed">{quality.recommendation}</p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <QualityStat label="Open bugs" value={quality.open_bug_count} />
              <QualityStat label="Test pass rate" value={quality.test_pass_rate != null ? `${quality.test_pass_rate}%` : "—"} />
              <QualityStat label="Avg. resolution" value={quality.avg_resolution_days != null ? `${quality.avg_resolution_days}d` : "—"} />
              <QualityStat label="Tests: pass/fail/untested" value={`${quality.tests_passed}/${quality.tests_failed}/${quality.tests_not_run}`} />
            </div>

            {quality.critical_open_bugs.length > 0 && (
              <BugRiskList title="🐞 Critical open bugs" bugs={quality.critical_open_bugs} />
            )}
            {quality.reopened_bugs.length > 0 && (
              <BugRiskList title="Reopened bugs" bugs={quality.reopened_bugs} />
            )}
            {quality.possible_duplicates.length > 0 && (
              <div className="rounded-lg border border-line bg-white p-4">
                <p className="text-sm font-medium mb-2">Possible duplicate bugs</p>
                <div className="space-y-1.5">
                  {quality.possible_duplicates.map((d, i) => (
                    <p key={i} className="text-xs text-muted">
                      <span className="font-mono">{d.bug_a}</span> ↔ <span className="font-mono">{d.bug_b}</span>
                      <span className="ml-2">({Math.round(d.title_similarity * 100)}% title match)</span>
                    </p>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function QualityStat({ label, value }) {
  return (
    <div className="rounded-lg border border-line bg-white p-3.5">
      <div className="font-display font-semibold text-lg">{value}</div>
      <div className="text-[11px] text-muted">{label}</div>
    </div>
  );
}

function BugRiskList({ title, bugs }) {
  return (
    <div className="rounded-lg border border-line bg-white p-4">
      <p className="text-sm font-medium mb-2">{title}</p>
      <div className="flex flex-wrap gap-2">
        {bugs.map((b) => (
          <span key={b.key} className="text-xs bg-black/[0.04] px-2.5 py-1 rounded-full font-mono">
            {b.key} · {b.severity}
          </span>
        ))}
      </div>
    </div>
  );
}

function TaskRiskList({ title, tone, tasks }) {
  return (
    <div className="rounded-lg border border-line bg-white p-4">
      <p className="text-sm font-medium mb-2">{title}</p>
      <div className="flex flex-wrap gap-2">
        {tasks.map((t) => (
          <span key={t.key} className="text-xs bg-black/[0.04] px-2.5 py-1 rounded-full font-mono">
            {t.key}{t.due_date ? ` · ${t.due_date}` : ""}
          </span>
        ))}
      </div>
    </div>
  );
}

function StoryPlanList({ title, tone, stories }) {
  return (
    <div className="rounded-lg border border-line bg-white p-4">
      <p className="text-sm font-medium mb-2">{title}</p>
      <div className="flex flex-wrap gap-2">
        {stories.map((s) => (
          <span key={s.key} className="text-xs bg-black/[0.04] px-2.5 py-1 rounded-full font-mono">
            {s.key} {s.story_points != null ? `· ${s.story_points}pt` : ""}
          </span>
        ))}
      </div>
    </div>
  );
}
