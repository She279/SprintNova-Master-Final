import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { sprintsApi } from "../../../api/sprints";
import { backlogApi } from "../../../api/backlog";
import { Badge, Alert } from "../../../components/ui/Feedback";
import { Select } from "../../../components/ui/Field";
import { BurndownChart } from "../../../components/BurndownChart";
import { useRealtime } from "../../../hooks/useRealtime";

const STATUS_TONE = { planned: "muted", active: "success", completed: "accent", cancelled: "danger" };
const PRIORITY_TONE = { critical: "danger", high: "warning", medium: "accent", low: "muted" };
const STATUS_LABEL = { backlog: "Backlog", ready: "Ready", in_sprint: "In sprint", in_progress: "In progress", done: "Done" };

export default function SprintDetailPage() {
  const { id: projectId, sprintId } = useParams();
  const [sprint, setSprint] = useState(null);
  const [burndown, setBurndown] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      const [s, b] = await Promise.all([
        sprintsApi.get(projectId, sprintId),
        sprintsApi.burndown(projectId, sprintId),
      ]);
      setSprint(s);
      setBurndown(b);
    } catch (err) {
      setError(err.message || "Could not load sprint.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, sprintId]);

  useRealtime({ projectId, onEvent: (event) => {
    if (event.type.startsWith("task.") || event.type.startsWith("sprint.")) load();
  }});

  async function updateStoryStatus(storyId, status) {
    try {
      await backlogApi.update(projectId, storyId, { status });
      load();
    } catch (err) {
      setError(err.message || "Could not update story.");
    }
  }

  if (error) return <Alert>{error}</Alert>;
  if (!sprint) return <p className="text-sm text-muted">Loading…</p>;

  return (
    <div className="max-w-4xl">
      <Link to={`/admin/projects/${projectId}`} className="text-xs text-muted hover:text-ink">
        ← Back to project
      </Link>

      <div className="mt-3 flex items-start justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight">{sprint.name}</h1>
          {sprint.goal && <p className="text-sm text-muted mt-1">{sprint.goal}</p>}
          <p className="text-xs font-mono text-muted mt-1">{sprint.start_date} → {sprint.end_date}</p>
        </div>
        <Badge tone={STATUS_TONE[sprint.status]}>{sprint.status}</Badge>
      </div>

      <div className="grid grid-cols-3 gap-3 my-5">
        <StatCard label="Total points" value={sprint.total_points} />
        <StatCard label="Completed points" value={sprint.completed_points} tone="text-success" />
        <StatCard label="Stories" value={sprint.stories.length} />
      </div>

      <div className="mb-6">
        <BurndownChart burndown={burndown} />
      </div>

      <h2 className="font-display font-semibold text-sm mb-3">Stories in this sprint</h2>
      <div className="space-y-2">
        {sprint.stories.length === 0 && (
          <p className="text-sm text-muted">No stories were pulled into this sprint.</p>
        )}
        {sprint.stories.map((s) => (
          <div key={s.id} className="rounded-lg border border-line bg-white p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-muted">{s.key}</span>
              <Badge tone={PRIORITY_TONE[s.priority]}>{s.priority}</Badge>
              {s.story_points != null && (
                <span className="text-xs font-mono bg-black/[0.04] px-1.5 py-0.5 rounded">{s.story_points} pts</span>
              )}
              <span className="text-sm">{s.title}</span>
            </div>
            <Select value={s.status} onChange={(e) => updateStoryStatus(s.id, e.target.value)} className="w-auto text-xs py-1.5">
              {Object.entries(STATUS_LABEL).map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </Select>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value, tone = "text-ink" }) {
  return (
    <div className="rounded-lg border border-line bg-white p-4 text-center">
      <div className={`font-display text-xl font-semibold ${tone}`}>{value}</div>
      <div className="text-xs text-muted mt-1">{label}</div>
    </div>
  );
}
