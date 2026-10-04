export function Badge({ tone = "muted", children }) {
  const tones = {
    success: "bg-success-soft text-success",
    warning: "bg-warning-soft text-warning",
    danger: "bg-danger-soft text-danger",
    accent: "bg-accent-soft text-accent-dark",
    muted: "bg-black/[0.05] text-ink/60",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function Alert({ tone = "danger", children }) {
  const tones = {
    danger: "bg-danger-soft text-danger border-danger/20",
    success: "bg-success-soft text-success border-success/20",
    warning: "bg-warning-soft text-warning border-warning/20",
  };
  return (
    <div className={`rounded-md border px-3.5 py-2.5 text-sm ${tones[tone]}`} role="alert">
      {children}
    </div>
  );
}
