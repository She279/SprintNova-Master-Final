import { useEffect, useState } from "react";
import { tasksApi } from "../../../api/tasks";
import { Field, Input, Select } from "../../../components/ui/Field";
import { Button } from "../../../components/ui/Button";
import { Badge, Alert } from "../../../components/ui/Feedback";
import { Modal } from "../../../components/ui/Modal";
import { useRealtime } from "../../../hooks/useRealtime";

const COLUMNS = [
  { value: "todo", label: "To Do" },
  { value: "in_progress", label: "In Progress" },
  { value: "testing", label: "Testing" },
  { value: "done", label: "Done" },
];

const PRIORITY_TONE = { critical: "danger", high: "warning", medium: "accent", low: "muted" };
const MANAGE_ROLES = ["owner_admin", "product_owner", "scrum_master"];

function isOverdue(task) {
  if (!task.due_date || task.status === "done") return false;
  return new Date(task.due_date) < new Date(new Date().toDateString());
}

function initials(fullName) {
  if (!fullName) return "?";
  return fullName.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();
}

export default function KanbanBoard({ projectId, members }) {
  const [tasks, setTasks] = useState(null);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [openTaskId, setOpenTaskId] = useState(null);
  const [dragId, setDragId] = useState(null);

  const memberById = Object.fromEntries((members || []).map((m) => [m.user_id, m]));

  async function load() {
    try {
      setTasks(await tasksApi.list(projectId));
    } catch (err) {
      setError(err.message || "Could not load tasks.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  useRealtime({ projectId, onEvent: (event) => {
    if (event.type.startsWith("task.") || event.type.startsWith("sprint.")) load();
  }});

  async function moveTask(taskId, status) {
    const task = tasks.find((t) => t.id === taskId);
    if (!task || task.status === status) return;
    setTasks((prev) => prev.map((t) => (t.id === taskId ? { ...t, status } : t)));
    try {
      await tasksApi.update(projectId, taskId, { status });
    } catch (err) {
      setError(err.message || "Could not move task.");
      load();
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs text-muted">Drag a card between columns to update its status.</p>
        <Button onClick={() => setCreating((v) => !v)}>{creating ? "Cancel" : "+ New task"}</Button>
      </div>

      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      {creating && (
        <div className="mb-5">
          <CreateTaskForm
            projectId={projectId}
            members={members}
            onCreated={() => {
              setCreating(false);
              load();
            }}
          />
        </div>
      )}

      {tasks === null ? (
        <p className="text-sm text-muted">Loading…</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {COLUMNS.map((col) => {
            const colTasks = tasks.filter((t) => t.status === col.value);
            return (
              <div
                key={col.value}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => dragId && moveTask(dragId, col.value)}
                className="rounded-lg bg-black/[0.02] border border-line p-3 min-h-[200px]"
              >
                <div className="flex items-center justify-between mb-3 px-1">
                  <span className="text-xs font-semibold uppercase tracking-wider text-ink/60">{col.label}</span>
                  <span className="text-xs font-mono text-muted">{colTasks.length}</span>
                </div>
                <div className="space-y-2">
                  {colTasks.map((task) => (
                    <div
                      key={task.id}
                      draggable
                      onDragStart={() => setDragId(task.id)}
                      onDragEnd={() => setDragId(null)}
                      onClick={() => setOpenTaskId(task.id)}
                      className="rounded-md border border-line bg-white p-3 cursor-grab active:cursor-grabbing hover:border-accent/40 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-mono text-[11px] text-muted">{task.key}</span>
                        <Badge tone={PRIORITY_TONE[task.priority]}>{task.priority}</Badge>
                      </div>
                      <p className="text-sm font-medium leading-snug mb-2">{task.title}</p>
                      <div className="flex items-center justify-between">
                        {task.due_date ? (
                          <span className={`text-[11px] font-mono ${isOverdue(task) ? "text-danger font-medium" : "text-muted"}`}>
                            {isOverdue(task) ? "⚠ " : ""}{task.due_date}
                          </span>
                        ) : <span />}
                        {task.assignee_id && memberById[task.assignee_id] && (
                          <span
                            title={memberById[task.assignee_id].full_name}
                            className="h-5 w-5 rounded-full bg-accent-soft text-accent-dark text-[10px] font-semibold flex items-center justify-center"
                          >
                            {initials(memberById[task.assignee_id].full_name)}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                  {colTasks.length === 0 && (
                    <div className="rounded-md border border-dashed border-line/70 p-4 text-center text-[11px] text-muted">
                      Drop a task here
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <TaskDetailModal
        projectId={projectId}
        taskId={openTaskId}
        members={members}
        onClose={() => setOpenTaskId(null)}
        onChange={load}
      />
    </div>
  );
}

function CreateTaskForm({ projectId, members, onCreated }) {
  const [form, setForm] = useState({ title: "", description: "", priority: "medium", due_date: "", estimated_hours: "", assignee_id: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await tasksApi.create(projectId, {
        title: form.title,
        description: form.description || undefined,
        priority: form.priority,
        due_date: form.due_date || undefined,
        estimated_hours: form.estimated_hours ? Number(form.estimated_hours) : undefined,
        assignee_id: form.assignee_id ? Number(form.assignee_id) : undefined,
      });
      onCreated();
    } catch (err) {
      setError(err.message || "Could not create task.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-line bg-white p-5 space-y-4">
      {error && <Alert>{error}</Alert>}
      <Field label="Title" htmlFor="ttitle">
        <Input id="ttitle" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
      </Field>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Field label="Priority" htmlFor="tpriority">
          <Select id="tpriority" value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </Select>
        </Field>
        <Field label="Due date" htmlFor="tdue">
          <Input id="tdue" type="date" value={form.due_date} onChange={(e) => setForm((f) => ({ ...f, due_date: e.target.value }))} />
        </Field>
        <Field label="Est. hours" htmlFor="test">
          <Input id="test" type="number" min="0" step="0.5" value={form.estimated_hours} onChange={(e) => setForm((f) => ({ ...f, estimated_hours: e.target.value }))} />
        </Field>
        <Field label="Assignee" htmlFor="tassignee">
          <Select id="tassignee" value={form.assignee_id} onChange={(e) => setForm((f) => ({ ...f, assignee_id: e.target.value }))}>
            <option value="">Unassigned</option>
            {members?.map((m) => <option key={m.user_id} value={m.user_id}>{m.full_name}</option>)}
          </Select>
        </Field>
      </div>
      <div className="flex justify-end">
        <Button type="submit" disabled={saving}>{saving ? "Creating…" : "Add task"}</Button>
      </div>
    </form>
  );
}

function TaskDetailModal({ projectId, taskId, members, onClose, onChange }) {
  const [task, setTask] = useState(null);
  const [comments, setComments] = useState([]);
  const [history, setHistory] = useState([]);
  const [commentBody, setCommentBody] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const [tasks, c, h] = await Promise.all([
        tasksApi.list(projectId),
        tasksApi.listComments(projectId, taskId),
        tasksApi.history(projectId, taskId),
      ]);
      setTask(tasks.find((t) => t.id === taskId) || null);
      setComments(c);
      setHistory(h);
    } catch (err) {
      setError(err.message || "Could not load task.");
    }
  }

  useEffect(() => {
    if (taskId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  async function updateField(field, value) {
    try {
      await tasksApi.update(projectId, taskId, { [field]: value });
      load();
      onChange();
    } catch (err) {
      setError(err.message || "Could not update task.");
    }
  }

  async function submitComment(e) {
    e.preventDefault();
    if (!commentBody.trim()) return;
    try {
      await tasksApi.addComment(projectId, taskId, commentBody.trim());
      setCommentBody("");
      load();
    } catch (err) {
      setError(err.message || "Could not add comment.");
    }
  }

  const memberById = Object.fromEntries((members || []).map((m) => [m.user_id, m]));

  return (
    <Modal open={!!taskId} onClose={onClose} title={task ? `${task.key} — ${task.title}` : "Task"} width="max-w-2xl">
      {error && <div className="mb-4"><Alert>{error}</Alert></div>}
      {!task ? (
        <p className="text-sm text-muted">Loading…</p>
      ) : (
        <div className="space-y-5">
          {task.description && <p className="text-sm text-ink/80">{task.description}</p>}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Field label="Status" htmlFor="mstatus">
              <Select id="mstatus" value={task.status} onChange={(e) => updateField("status", e.target.value)} className="text-xs py-1.5">
                {COLUMNS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </Select>
            </Field>
            <Field label="Priority" htmlFor="mpriority">
              <Select id="mpriority" value={task.priority} onChange={(e) => updateField("priority", e.target.value)} className="text-xs py-1.5">
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </Select>
            </Field>
            <Field label="Assignee" htmlFor="massignee">
              <Select id="massignee" value={task.assignee_id || ""} onChange={(e) => updateField("assignee_id", e.target.value ? Number(e.target.value) : null)} className="text-xs py-1.5">
                <option value="">Unassigned</option>
                {members?.map((m) => <option key={m.user_id} value={m.user_id}>{m.full_name}</option>)}
              </Select>
            </Field>
            <Field label="Actual hours" htmlFor="mactual">
              <Input id="mactual" type="number" min="0" step="0.5" value={task.actual_hours ?? ""} onChange={(e) => updateField("actual_hours", e.target.value ? Number(e.target.value) : null)} className="text-xs py-1.5" />
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
