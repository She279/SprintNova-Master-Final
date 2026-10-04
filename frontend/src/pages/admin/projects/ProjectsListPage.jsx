import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { projectsApi } from "../../../api/projects";
import { Button } from "../../../components/ui/Button";
import { Badge, Alert } from "../../../components/ui/Feedback";

const STATUS_TONE = {
  planning: "muted",
  active: "success",
  on_hold: "warning",
  completed: "accent",
  cancelled: "danger",
};

export default function ProjectsListPage() {
  const [projects, setProjects] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    projectsApi
      .list()
      .then(setProjects)
      .catch((err) => setError(err.message || "Could not load projects."));
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight">Projects</h1>
          <p className="text-sm text-muted mt-1">
            You see every project you're on the team for — Admins see all of them.
          </p>
        </div>
        <Link to="/admin/projects/new">
          <Button>+ New project</Button>
        </Link>
      </div>

      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      {projects === null && !error && <p className="text-sm text-muted">Loading…</p>}

      {projects?.length === 0 && (
        <div className="rounded-lg border border-dashed border-line bg-white/50 p-10 text-center">
          <p className="text-sm text-muted">No projects yet — or none you've been added to.</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects?.map((p) => (
          <Link
            key={p.id}
            to={`/admin/projects/${p.id}`}
            className="rounded-lg border border-line bg-white p-5 hover:border-accent/40 hover:shadow-sm transition-all"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-xs text-muted">{p.code}</span>
              <Badge tone={STATUS_TONE[p.status]}>{p.status.replace("_", " ")}</Badge>
            </div>
            <h3 className="font-display font-semibold text-ink">{p.name}</h3>
            {p.description && <p className="text-sm text-muted mt-1.5 line-clamp-2">{p.description}</p>}
            {p.start_date && (
              <p className="text-xs text-muted mt-3 font-mono">
                {p.start_date} {p.end_date ? `→ ${p.end_date}` : ""}
              </p>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
