/**
 * Milestone-completion progress, presented as a completion bar + a
 * cumulative-over-time line. This stands in for a real sprint
 * burndown/velocity chart until Module 3 (Scrum/Sprints) provides actual
 * sprint data -- labeled honestly as such rather than pretending to be
 * something it isn't.
 */
export function ProjectProgressChart({ progress }) {
  if (!progress) return null;
  const { total_milestones, completed_milestones, missed_milestones, percent_complete, timeline } = progress;

  return (
    <div className="rounded-lg border border-line bg-white p-5">
      <div className="flex items-center justify-between mb-1">
        <h3 className="font-display font-semibold text-sm">Team progress</h3>
        <span className="text-xs font-mono text-muted">{percent_complete}% complete</span>
      </div>
      <p className="text-xs text-muted mb-4">
        Based on milestone completion — sprint burndown/velocity charts will replace this once Sprints are live.
      </p>

      <div className="h-2 rounded-full bg-black/[0.06] overflow-hidden mb-4">
        <div className="h-full bg-accent transition-all" style={{ width: `${percent_complete}%` }} />
      </div>

      <div className="flex gap-6 text-sm mb-4">
        <Stat label="Total" value={total_milestones} />
        <Stat label="Completed" value={completed_milestones} tone="text-success" />
        <Stat label="Missed" value={missed_milestones} tone="text-danger" />
      </div>

      {timeline.length > 1 && <Sparkline points={timeline} />}
    </div>
  );
}

function Stat({ label, value, tone = "text-ink" }) {
  return (
    <div>
      <div className={`font-display font-semibold ${tone}`}>{value}</div>
      <div className="text-xs text-muted">{label}</div>
    </div>
  );
}

function Sparkline({ points }) {
  const width = 400;
  const height = 60;
  const max = Math.max(...points.map((p) => p.cumulative_completed));
  const stepX = width / (points.length - 1 || 1);

  const path = points
    .map((p, i) => {
      const x = i * stepX;
      const y = height - (p.cumulative_completed / max) * (height - 8) - 4;
      return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-14" preserveAspectRatio="none">
      <path d={path} fill="none" stroke="#3654FF" strokeWidth="2" />
    </svg>
  );
}
