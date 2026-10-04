export function VelocityChart({ velocity }) {
  if (!velocity) return null;
  const { sprints, average_velocity } = velocity;

  if (sprints.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-line p-6 text-center text-sm text-muted">
        No completed sprints yet — velocity will appear here once a sprint is closed.
      </div>
    );
  }

  const width = 640;
  const height = 160;
  const padding = { top: 12, right: 16, bottom: 24, left: 32 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;
  const maxY = Math.max(...sprints.map((s) => s.completed_points), average_velocity, 1);
  const barW = (plotW / sprints.length) * 0.6;
  const gap = (plotW / sprints.length) * 0.4;

  const avgY = padding.top + plotH - (average_velocity / maxY) * plotH;

  return (
    <div className="rounded-lg border border-line bg-white p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display font-semibold text-sm">Velocity</h3>
        <span className="text-xs font-mono text-muted">avg {average_velocity} pts</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-40">
        <line x1={padding.left} x2={width - padding.right} y1={avgY} y2={avgY} stroke="#B7791F" strokeWidth="1.5" strokeDasharray="3 3" />
        {sprints.map((s, i) => {
          const barH = (s.completed_points / maxY) * plotH;
          const bx = padding.left + i * (barW + gap) + gap / 2;
          const by = padding.top + plotH - barH;
          return (
            <g key={s.sprint_id}>
              <rect x={bx} y={by} width={barW} height={barH} rx="3" fill="#3654FF" />
              <text x={bx + barW / 2} y={by - 4} fontSize="10" textAnchor="middle" fill="#14181F">{s.completed_points}</text>
              <text x={bx + barW / 2} y={height - 8} fontSize="9" textAnchor="middle" fill="#6B7280">
                {s.sprint_name.length > 10 ? s.sprint_name.slice(0, 9) + "…" : s.sprint_name}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
