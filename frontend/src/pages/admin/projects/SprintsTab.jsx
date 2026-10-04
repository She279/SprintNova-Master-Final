import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { sprintsApi } from "../../../api/sprints";
import { Field, Input } from "../../../components/ui/Field";
import { Button } from "../../../components/ui/Button";
import { Badge, Alert } from "../../../components/ui/Feedback";
import { VelocityChart } from "../../../components/VelocityChart";
import { useAuth } from "../../../context/AuthContext";

const STATUS_TONE = { planned: "muted", active: "success", completed: "accent", cancelled: "danger" };
const SPRINT_ROLES = ["owner_admin", "scrum_master"];

export default function SprintsTab({ projectId }) {
  const { session } = useAuth();
  const canManage = SPRINT_ROLES.includes(session?.role);

  const [sprints, setSprints] = useState(null);
  const [velocity, setVelocity] = useState(null);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [busyId, setBusyId] = useState(null);

  async function load() {
    try {
      const [s, v] = await Promise.all([sprintsApi.list(projectId), sprintsApi.velocity(projectId)]);
      setSprints(s);
      setVelocity(v);
    } catch (err) {
      setError(err.message || "Could not load sprints.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleAction(sprintId, action) {
    setBusyId(sprintId);
    try {
      await sprintsApi[action](projectId, sprintId);
      load();
    } catch (err) {
      setError(err.message || "Could not update sprint.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <VelocityChart velocity={velocity} />

      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-display font-semibold text-sm">Sprints</h3>
          {canManage && <Button onClick={() => setCreating((v) => !v)}>{creating ? "Cancel" : "+ New sprint"}</Button>}
        </div>

        {error && <div className="mb-4"><Alert>{error}</Alert></div>}

        {creating && (
          <div className="mb-4">
            <CreateSprintForm projectId={projectId} onCreated={() => { setCreating(false); load(); }} />
          </div>
        )}

        {sprints === null && <p className="text-sm text-muted">Loading…</p>}
        {sprints?.length === 0 && !creating && (
          <div className="rounded-lg border border-dashed border-line p-8 text-center text-sm text-muted">
            No sprints yet.
          </div>
        )}

        <div className="space-y-2">
          {sprints?.map((sp) => (
            <div key={sp.id} className="rounded-lg border border-line bg-white p-4 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Link to={`/admin/projects/${projectId}/sprints/${sp.id}`} className="font-medium text-sm hover:text-accent">
                    {sp.name}
                  </Link>
                  <Badge tone={STATUS_TONE[sp.status]}>{sp.status}</Badge>
                </div>
                {sp.goal && <p className="text-xs text-muted">{sp.goal}</p>}
                <p className="text-xs font-mono text-muted mt-0.5">{sp.start_date} → {sp.end_date}</p>
              </div>
              {canManage && (
                <div className="flex gap-2">
                  {sp.status === "planned" && (
                    <button onClick={() => handleAction(sp.id, "start")} disabled={busyId === sp.id} className="text-xs font-medium text-success hover:underline">
                      Start
                    </button>
                  )}
                  {sp.status === "active" && (
                    <button onClick={() => handleAction(sp.id, "close")} disabled={busyId === sp.id} className="text-xs font-medium text-accent hover:underline">
                      Close
                    </button>
                  )}
                  {(sp.status === "planned" || sp.status === "active") && (
                    <button onClick={() => handleAction(sp.id, "cancel")} disabled={busyId === sp.id} className="text-xs font-medium text-danger hover:underline">
                      Cancel
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function CreateSprintForm({ projectId, onCreated }) {
  const [form, setForm] = useState({ name: "", goal: "", start_date: "", end_date: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await sprintsApi.create(projectId, { ...form, goal: form.goal || undefined });
      onCreated();
    } catch (err) {
      setError(err.message || "Could not create sprint.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-line bg-white p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
      {error && <div className="md:col-span-2"><Alert>{error}</Alert></div>}
      <Field label="Sprint name" htmlFor="spname">
        <Input id="spname" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
      </Field>
      <Field label="Sprint goal" htmlFor="spgoal" hint="Optional">
        <Input id="spgoal" value={form.goal} onChange={(e) => setForm((f) => ({ ...f, goal: e.target.value }))} />
      </Field>
      <Field label="Start date" htmlFor="spstart">
        <Input id="spstart" type="date" value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} required />
      </Field>
      <Field label="End date" htmlFor="spend">
        <Input id="spend" type="date" value={form.end_date} onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))} required />
      </Field>
      <div className="md:col-span-2 flex justify-end">
        <Button type="submit" disabled={saving}>{saving ? "Creating…" : "Create sprint"}</Button>
      </div>
    </form>
  );
}
