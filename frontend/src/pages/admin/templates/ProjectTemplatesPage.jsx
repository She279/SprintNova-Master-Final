import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectTemplatesApi } from "../../../api/projectTemplates";
import { Field, Input, Select } from "../../../components/ui/Field";
import { Button } from "../../../components/ui/Button";
import { Alert } from "../../../components/ui/Feedback";

const PROJECT_ROLES = ["product_owner", "scrum_master", "developer", "tester", "client_viewer"];

export default function ProjectTemplatesPage() {
  const [templates, setTemplates] = useState(null);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [applyingId, setApplyingId] = useState(null);

  async function load() {
    try {
      setTemplates(await projectTemplatesApi.list());
    } catch (err) {
      setError(err.message || "Could not load templates.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight">Project templates</h1>
          <p className="text-sm text-muted mt-1">
            Reusable blueprints — applying one creates a project with its milestones pre-populated.
          </p>
        </div>
        <Button onClick={() => setCreating((v) => !v)}>{creating ? "Cancel" : "+ New template"}</Button>
      </div>

      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      {creating && (
        <div className="mb-6">
          <CreateTemplateForm
            onCreated={() => {
              setCreating(false);
              load();
            }}
          />
        </div>
      )}

      {templates === null && <p className="text-sm text-muted">Loading…</p>}
      {templates?.length === 0 && !creating && (
        <div className="rounded-lg border border-dashed border-line bg-white/50 p-10 text-center">
          <p className="text-sm text-muted">No templates yet.</p>
        </div>
      )}

      <div className="space-y-3">
        {templates?.map((t) => (
          <div key={t.id} className="rounded-lg border border-line bg-white p-5">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-display font-semibold">{t.name}</h3>
                {t.description && <p className="text-sm text-muted mt-1">{t.description}</p>}
              </div>
              <Button variant="secondary" onClick={() => setApplyingId(applyingId === t.id ? null : t.id)}>
                {applyingId === t.id ? "Cancel" : "Use template"}
              </Button>
            </div>

            <div className="flex flex-wrap gap-1.5 mt-3">
              {t.default_milestones.map((m, i) => (
                <span key={i} className="text-xs font-mono bg-black/[0.04] px-2 py-1 rounded">
                  {m.phase ? `${m.phase} · ` : ""}
                  {m.title} (+{m.offset_days}d)
                </span>
              ))}
            </div>

            {applyingId === t.id && (
              <ApplyTemplateForm templateId={t.id} onCreated={() => setApplyingId(null)} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function CreateTemplateForm({ onCreated }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [roles, setRoles] = useState([]);
  const [milestones, setMilestones] = useState([{ title: "", phase: "", offset_days: 0 }]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function updateMilestone(i, field, value) {
    setMilestones((ms) => ms.map((m, idx) => (idx === i ? { ...m, [field]: value } : m)));
  }

  function toggleRole(role) {
    setRoles((r) => (r.includes(role) ? r.filter((x) => x !== role) : [...r, role]));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await projectTemplatesApi.create({
        name,
        description: description || undefined,
        default_milestones: milestones
          .filter((m) => m.title)
          .map((m) => ({ ...m, offset_days: Number(m.offset_days) || 0 })),
        default_project_roles: roles,
      });
      onCreated();
    } catch (err) {
      setError(err.message || "Could not create template.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-line bg-white p-5 space-y-4">
      {error && <Alert>{error}</Alert>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Template name" htmlFor="tname">
          <Input id="tname" value={name} onChange={(e) => setName(e.target.value)} required />
        </Field>
        <Field label="Description" htmlFor="tdesc">
          <Input id="tdesc" value={description} onChange={(e) => setDescription(e.target.value)} />
        </Field>
      </div>

      <div>
        <p className="text-sm font-medium text-ink/80 mb-2">Default project roles</p>
        <div className="flex flex-wrap gap-2">
          {PROJECT_ROLES.map((r) => (
            <button
              type="button"
              key={r}
              onClick={() => toggleRole(r)}
              className={`text-xs px-2.5 py-1 rounded-full border capitalize transition-colors ${
                roles.includes(r) ? "bg-accent text-white border-accent" : "border-line text-ink/60"
              }`}
            >
              {r.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="text-sm font-medium text-ink/80 mb-2">Default milestones</p>
        <div className="space-y-2">
          {milestones.map((m, i) => (
            <div key={i} className="grid grid-cols-[1fr_auto_auto] gap-2">
              <Input placeholder="Milestone title" value={m.title} onChange={(e) => updateMilestone(i, "title", e.target.value)} />
              <Input placeholder="Phase" className="w-32" value={m.phase} onChange={(e) => updateMilestone(i, "phase", e.target.value)} />
              <Input placeholder="Days" type="number" className="w-20" value={m.offset_days} onChange={(e) => updateMilestone(i, "offset_days", e.target.value)} />
            </div>
          ))}
        </div>
        <button
          type="button"
          onClick={() => setMilestones((ms) => [...ms, { title: "", phase: "", offset_days: 0 }])}
          className="text-xs text-accent hover:underline mt-2"
        >
          + Add milestone
        </button>
      </div>

      <div className="flex justify-end">
        <Button type="submit" disabled={saving}>
          {saving ? "Saving…" : "Save template"}
        </Button>
      </div>
    </form>
  );
}

function ApplyTemplateForm({ templateId, onCreated }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ code: "", name: "", start_date: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const project = await projectTemplatesApi.apply(templateId, form);
      onCreated();
      navigate(`/admin/projects/${project.id}`);
    } catch (err) {
      setError(err.message || "Could not create project from template.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 pt-4 border-t border-line grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
      {error && <div className="md:col-span-3"><Alert>{error}</Alert></div>}
      <Field label="Project code" htmlFor="acode">
        <Input id="acode" className="font-mono" value={form.code} onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))} required />
      </Field>
      <Field label="Project name" htmlFor="aname">
        <Input id="aname" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
      </Field>
      <Field label="Start date" htmlFor="astart">
        <Input id="astart" type="date" value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} required />
      </Field>
      <div className="md:col-span-3 flex justify-end">
        <Button type="submit" disabled={saving}>
          {saving ? "Creating…" : "Create project"}
        </Button>
      </div>
    </form>
  );
}
