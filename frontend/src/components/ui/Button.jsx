export function Button({ variant = "primary", className = "", children, ...props }) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-accent text-white hover:bg-accent-dark",
    secondary: "bg-white text-ink border border-line hover:border-ink/30",
    ghost: "text-ink/70 hover:text-ink hover:bg-black/[0.03]",
    danger: "bg-danger text-white hover:bg-danger/90",
  };
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}
