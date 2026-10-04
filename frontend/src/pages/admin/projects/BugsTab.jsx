import { useEffect, useState } from "react";
import { bugsApi } from "../../../api/bugs";
import { Field, Input, Select } from "../../../components/ui/Field";
import { Button } from "../../../components/ui/Button";
import { Badge, Alert } from "../../../components/ui/Feedback";
import { Modal } from "../../../components/ui/Modal";

const BUG_STATUSES = ["open", "assigned", "in_progress", "fixed", "retesting", "verified", "reopened", "closed"];
const SEVERITY_TONE = { critical: "danger", major: "warning", minor: "accent", trivial: "muted" };
const PRIORITY_TONE = { critical: "danger", high: "warning", medium: "accent", low: "muted" };
const STATUS_TONE = {
  open: "danger", assigned: "warning", in_progress: "accent", fixed: "success",
  retesting: "warning", verified: "success", reopened: "danger", closed: "muted",
};

export default function BugsTab({ projectId, members }) {
  const [bugs, setBugs] = useState(null);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [openBugId, setOpenBugId] = useState(null);

  const memberById = Object.fromEntries((members || []).map((m) => [m.user_id, m]));

  async function load() {
    try {
      setBugs(await bugsApi.list(projectId, statusFilter ? { status: statusFilter } : {}));
    } catch (err) {
      setError(err.message || "Could not load bugs.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, statusFilter]);

  async function quickStatusChange(bugId, status) {
    try {
      await bugsApi.update(projectId, bugId, { status });
      load();
    } catch (err) {
      setError(err.message || "Could not update bug.");
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4 gap-3">
        <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-48">
          <option value="">All statuses</option>
          {BUG_STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
        </Select>
        <Button onClick={() => setCreating((v) => !v)}>{creating ? "Cancel" : "+ Report bug"}</Button>
      </div>

      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      {creating && (
        <div className="mb-5">
          <CreateBugForm projectId={projectId} members={members} onCreated={() => { setCreating(false); load(); }} />
        </div>
      )}

      <div className="rounded-lg border border-line bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-black/[0.015] text-left text-xs uppercase tracking-wider text-muted">
              <th className="px-5 py-3 font-medium">Bug</th>
              <th className="px-5 py-3 font-medium">Severity</th>
              <th className="px-5 py-3 font-medium">Priority</th>
              <th className="px-5 py-3 font-medium">Assignee</th>
              <th className="px-5 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {bugs === null && <tr><td colSpan={5} className="px-5 py-8 text-center text-muted">Loading…</td></tr>}
            {bugs?.length === 0 && <tr><td colSpan={5} className="px-5 py-10 text-center text-muted">No bugs reported yet.</td></tr>}
            {bugs?.map((bug) => (
              <tr key={bug.id} className="border-b border-line last:border-0 hover:bg-black/[0.01]">
                <td className="px-5 py-3 cursor-pointer" onClick={() => setOpenBugId(bug.id)}>
                  <p className="font-medium hover:text-accent">{bug.title}</p>
                  <p className="text-xs text-muted font-mono">{bug.key}</p>
                </td>
                <td className="px-5 py-3"><Badge tone={SEVERITY_TONE[bug.severity]}>{bug.severity}</Badge></td>
                <td className="px-5 py-3"><Badge tone={PRIORITY_TONE[bug.priority]}>{bug.priority}</Badge></td>
                <td className="px-5 py-3 text-xs">{bug.assignee_id ? memberById[bug.assignee_id]?.full_name || "—" : "Unassigned"}</td>
                <td className="px-5 py-3">
                  <Select value={bug.status} onChange={(e) => quickStatusChange(bug.id, e.target.value)} className="text-xs py-1.5 w-auto">
                    {BUG_STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
                  </Select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <BugDetailModal projectId={projectId} bugId={openBugId} members={members} onClose={() => setOpenBugId(null)} onChange={load} />
    </div>
  );
}

function CreateBugForm({ projectId, members, onCreated }) {
  const [form, setForm] = useState({
    title: "", description: "", steps_to_reproduce: "", severity: "minor", priority: "medium", assignee_id: "",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await bugsApi.create(projectId, {
        ...form,
        assignee_id: form.assignee_id ? Number(form.assignee_id) : undefined,
      });
      onCreated();
    } catch (err) {
      setError(err.message || "Could not report bug.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-line bg-white p-5 space-y-4">
      {error && <Alert>{error}</Alert>}
      <Field label="Title" htmlFor="bugtitle">
        <Input id="bugtitle" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
      </Field>
      <Field label="Steps to reproduce" htmlFor="bugsteps">
        <textarea
          id="bugsteps" rows={3} value={form.steps_to_reproduce}
          onChange={(e) => setForm((f) => ({ ...f, steps_to_reproduce: e.target.value }))}
          className="w-full rounded-md border border-line bg-white px-3.5 py-2.5 text-sm focus:border-accent focus:ring-1 focus:ring-accent outline-none"
        />
      </Field>
      <div className="grid grid-cols-3 gap-3">
        <Field label="Severity" htmlFor="bugseverity">
          <Select id="bugseverity" value={form.severity} onChange={(e) => setForm((f) => ({ ...f, severity: e.target.value }))}>
            <option value="critical">Critical</option>
            <option value="major">Major</option>
            <option value="minor">Minor</option>
            <option value="trivial">Trivial</option>
          </Select>
        </Field>
        <Field label="Priority" htmlFor="bugpriority">
          <Select id="bugpriority" value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </Select>
        </Field>
        <Field label="Assignee" htmlFor="bugassignee">
          <Select id="bugassignee" value={form.assignee_id} onChange={(e) => setForm((f) => ({ ...f, assignee_id: e.target.value }))}>
            <option value="">Unassigned</option>
            {members?.map((m) => <option key={m.user_id} value={m.user_id}>{m.full_name}</option>)}
          </Select>
        </Field>
      </div>
      <div className="flex justify-end">
        <Button type="submit" disabled={saving}>{saving ? "Reporting…" : "Report bug"}</Button>
      </div>
    </form>
  );
}

function BugDetailModal({ projectId, bugId, members, onClose, onChange }) {
  const [bug, setBug] = useState(null);
  const [comments, setComments] = useState([]);
  const [history, setHistory] = useState([]);
  const [commentBody, setCommentBody] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const [bugs, c, h] = await Promise.all([
        bugsApi.list(projectId), bugsApi.listComments(projectId, bugId), bugsApi.history(projectId, bugId),
      ]);
      setBug(bugs.find((b) => b.id === bugId) || null);
      setComments(c);
      setHistory(h);
    } catch (err) {
      setError(err.message || "Could not load bug.");
    }
  }

  useEffect(() => {
    if (bugId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bugId]);

  async function updateField(field, value) {
    try {
      await bugsApi.update(projectId, bugId, { [field]: value });
      load();
      onChange();
    } catch (err) {
      setError(err.message || "Could not update bug.");
    }
  }

  async function submitComment(e) {
    e.preventDefault();
    if (!commentBody.trim()) return;
    try {
      await bugsApi.addComment(projectId, bugId, commentBody.trim());
      setCommentBody("");
      load();
    } catch (err) {
      setError(err.message || "Could not add comment.");
    }
  }

  return (
    <Modal open={!!bugId} onClose={onClose} title={bug ? `${bug.key} — ${bug.title}` : "Bug"} width="max-w-2xl">
      {error && <div className="mb-4"><Alert>{error}</Alert></div>}
      {!bug ? (
        <p className="text-sm text-muted">Loading…</p>
      ) : (
        <div className="space-y-5">
          {bug.description && <p className="text-sm text-ink/80">{bug.description}</p>}
          {bug.steps_to_reproduce && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-muted mb-1">Steps to reproduce</p>
              <p className="text-sm whitespace-pre-line">{bug.steps_to_reproduce}</p>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Field label="Status" htmlFor="bmstatus">
              <Select id="bmstatus" value={bug.status} onChange={(e) => updateField("status", e.target.value)} className="text-xs py-1.5">
                {BUG_STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
              </Select>
            </Field>
            <Field label="Severity" htmlFor="bmseverity">
              <Select id="bmseverity" value={bug.severity} onChange={(e) => updateField("severity", e.target.value)} className="text-xs py-1.5">
                <option value="critical">Critical</option>
                <option value="major">Major</option>
                <option value="minor">Minor</option>
                <option value="trivial">Trivial</option>
              </Select>
            </Field>
            <Field label="Priority" htmlFor="bmpriority">
              <Select id="bmpriority" value={bug.priority} onChange={(e) => updateField("priority", e.target.value)} className="text-xs py-1.5">
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </Select>
            </Field>
            <Field label="Assignee" htmlFor="bmassignee">
              <Select id="bmassignee" value={bug.assignee_id || ""} onChange={(e) => updateField("assignee_id", e.target.value ? Number(e.target.value) : null)} className="text-xs py-1.5">
                <option value="">Unassigned</option>
                {members?.map((m) => <option key={m.user_id} value={m.user_id}>{m.full_name}</option>)}
              </Select>
            </Field>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-2">Comments</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto mb-3">
              {comments.length === 0 && <p className="text-xs text-muted">No comments yet.</p>}
              {comments.map((c) => (
                <div key={c.id} className="rounded-md bg-black/[0.03] px-3 py-2">
                  <p className="text-sm">{c.body}</p>
                  <p className="text-[10px] text-muted mt-1 font-mono">{new Date(c.created_at).toLocaleString()}</p>
                </div>
              ))}
            </div>
            <form onSubmit={submitComment} className="flex gap-2">
              <Input value={commentBody} onChange={(e) => setCommentBody(e.target.value)} placeholder="Add a comment…" className="flex-1" />
              <Button type="submit" variant="secondary">Post</Button>
            </form>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-2">Activity</h3>
            <div className="space-y-1.5">
              {history.length === 0 && <p className="text-xs text-muted">No activity yet.</p>}
              {history.map((h) => (
                <p key={h.id} className="text-xs text-muted">
                  <span className="font-mono">{h.field_changed}</span>: {h.old_value || "—"} → {h.new_value || "—"}
                  <span className="ml-2 text-[10px]">{new Date(h.created_at).toLocaleString()}</span>
                </p>
              ))}
            </div>
          </div>
        </div>
      )}
    </Modal>
  );
}
