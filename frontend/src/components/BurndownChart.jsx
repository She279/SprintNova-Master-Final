/**
 * Real sprint burndown: ideal (straight-line) remaining points vs. actual
 * remaining points computed from real story completion data. Actual stops
 * partway through if the sprint is still active (no future data to plot).
 */
export function BurndownChart({ burndown }) {
  if (!burndown || burndown.points.length === 0) return null;
  const { total_points, points } = burndown;

  const width = 640;
  const height = 220;
  const padding = { top: 16, right: 16, bottom: 28, left: 36 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  const maxY = Math.max(total_points, 1);
  const stepX = plotW / (points.length - 1 || 1);
  const x = (i) => padding.left + i * stepX;
  const y = (v) => padding.top + plotH - (v / maxY) * plotH;

  const idealPath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${y(p.ideal_remaining).toFixed(1)}`).join(" ");

  const actualPoints = points.filter((p) => p.actual_remaining !== null);
  const actualPath = actualPoints
    .map((p, i) => `${i === 0 ? "M" : "L"} ${x(points.indexOf(p)).toFixed(1)} ${y(p.actual_remaining).toFixed(1)}`)
    .join(" ");

  return (
    <div className="rounded-lg border border-line bg-white p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display font-semibold text-sm">Burndown</h3>
        <div className="flex items-center gap-4 text-xs text-muted">
          <span className="flex items-center gap-1.5"><span className="h-0.5 w-4 bg-line inline-block" /> Ideal</span>
          <span className="flex items-center gap-1.5"><span className="h-0.5 w-4 bg-accent inline-block" /> Actual</span>
        </div>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-56">
        {/* y-axis gridlines */}
        {[0, 0.5, 1].map((f, i) => (
          <line key={i} x1={padding.left} x2={width - padding.right} y1={y(maxY * f)} y2={y(maxY * f)} stroke="#E4E2DA" strokeWidth="1" />
        ))}
        <text x={4} y={y(maxY) + 4} fontSize="10" fill="#6B7280">{maxY}</text>
        <text x={4} y={y(0) + 4} fontSize="10" fill="#6B7280">0</text>

        <path d={idealPath} fill="none" stroke="#C9C7BE" strokeWidth="2" strokeDasharray="4 4" />
        {actualPath && <path d={actualPath} fill="none" stroke="#3654FF" strokeWidth="2.5" />}
        {actualPoints.map((p) => (
          <circle key={p.date} cx={x(points.indexOf(p))} cy={y(p.actual_remaining)} r="3" fill="#3654FF" />
        ))}
      </svg>
      <div className="flex justify-between text-[10px] font-mono text-muted mt-1">
        <span>{points[0].date}</span>
        <span>{points[points.length - 1].date}</span>
      </div>
    </div>
  );
}
