import { useEffect, useState } from "react";
import { backlogApi } from "../../../api/backlog";
import { epicsApi } from "../../../api/epics";
import { sprintsApi } from "../../../api/sprints";
import { Field, Input, Select } from "../../../components/ui/Field";
import { Button } from "../../../components/ui/Button";
import { Badge, Alert } from "../../../components/ui/Feedback";
import { useAuth } from "../../../context/AuthContext";

const PRIORITY_TONE = { critical: "danger", high: "warning", medium: "accent", low: "muted" };
const STATUS_LABEL = { backlog: "Backlog", ready: "Ready", in_sprint: "In sprint", in_progress: "In progress", done: "Done" };
const BACKLOG_ROLES = ["owner_admin", "product_owner"];

export default function BacklogTab({ projectId, members }) {
  const { session } = useAuth();
  const canManage = BACKLOG_ROLES.includes(session?.role);

  const [stories, setStories] = useState(null);
  const [epics, setEpics] = useState([]);
  const [sprints, setSprints] = useState([]);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [dragId, setDragId] = useState(null);

  async function load() {
    try {
      const [s, e, sp] = await Promise.all([
        backlogApi.list(projectId, { sprint_id: "" }),
        epicsApi.list(projectId),
        sprintsApi.list(projectId),
      ]);
      // Only show items not already in a sprint here — sprint-assigned items live in the Sprints tab.
      setStories(s.filter((x) => !x.sprint_id));
      setEpics(e);
      setSprints(sp.filter((sp) => sp.status === "planned" || sp.status === "active"));
    } catch (err) {
      setError(err.message || "Could not load backlog.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleDrop(targetId) {
    if (dragId === null || dragId === targetId) return;
    const ids = stories.map((s) => s.id);
    const from = ids.indexOf(dragId);
    const to = ids.indexOf(targetId);
    ids.splice(to, 0, ids.splice(from, 1)[0]);
    setStories(ids.map((id) => stories.find((s) => s.id === id)));
    try {
      await backlogApi.reorder(projectId, ids);
    } catch {
      load();
    }
    setDragId(null);
  }

  async function updateStory(story, payload) {
    try {
      await backlogApi.update(projectId, story.id, payload);
      load();
    } catch (err) {
      setError(err.message || "Could not update story.");
    }
  }

  async function moveToSprint(story, sprintId) {
    try {
      await backlogApi.assignToSprint(projectId, story.id, sprintId ? Number(sprintId) : null);
      load();
    } catch (err) {
      setError(err.message || "Could not move story to sprint.");
    }
  }

  async function deleteStory(story) {
    try {
      await backlogApi.remove(projectId, story.id);
      load();
    } catch (err) {
      setError(err.message || "Could not delete story.");
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs text-muted">
          {canManage ? "Drag to reorder. This order feeds AI sprint planning." : "Ordered by the Product Owner's priority."}
        </p>
        {canManage && (
          <Button onClick={() => setCreating((v) => !v)}>{creating ? "Cancel" : "+ New story"}</Button>
        )}
      </div>

      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      {creating && (
        <div className="mb-4">
          <CreateStoryForm
            projectId={projectId}
            epics={epics}
            members={members}
            onCreated={() => {
              setCreating(false);
              load();
            }}
          />
        </div>
      )}

      {stories === null && <p className="text-sm text-muted">Loading…</p>}
      {stories?.length === 0 && !creating && (
        <div className="rounded-lg border border-dashed border-line p-10 text-center text-sm text-muted">
          Backlog is empty.
        </div>
      )}

      <div className="space-y-2">
        {stories?.map((story) => (
          <div
            key={story.id}
            draggable={canManage}
            onDragStart={() => setDragId(story.id)}
            onDragOver={(e) => e.preventDefault()}
            onDrop={() => handleDrop(story.id)}
            className={`rounded-lg border border-line bg-white p-4 ${canManage ? "cursor-grab active:cursor-grabbing" : ""}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-xs text-muted">{story.key}</span>
                  <Badge tone={PRIORITY_TONE[story.priority]}>{story.priority}</Badge>
                  {story.story_points != null && (
                    <span className="text-xs font-mono bg-black/[0.04] px-1.5 py-0.5 rounded">{story.story_points} pts</span>
                  )}
                </div>
                <p className="text-sm font-medium">{story.title}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Select
                  value={story.status}
                  onChange={(e) => updateStory(story, { status: e.target.value })}
                  className="w-auto text-xs py-1.5"
                >
                  {Object.entries(STATUS_LABEL).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </Select>
                {canManage && (
                  <>
                    <Select
                      value=""
                      onChange={(e) => moveToSprint(story, e.target.value)}
                      className="w-auto text-xs py-1.5"
                    >
                      <option value="">Move to sprint…</option>
                      {sprints.map((sp) => (
                        <option key={sp.id} value={sp.id}>{sp.name}</option>
                      ))}
                    </Select>
                    <button onClick={() => deleteStory(story)} className="text-xs text-danger hover:underline">
                      Delete
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CreateStoryForm({ projectId, epics, members, onCreated }) {
  const [form, setForm] = useState({ title: "", description: "", acceptance_criteria: "", priority: "medium", story_points: "", epic_id: "", assignee_id: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await backlogApi.create(projectId, {
        title: form.title,
        description: form.description || undefined,
        acceptance_criteria: form.acceptance_criteria || undefined,
        priority: form.priority,
        story_points: form.story_points ? Number(form.story_points) : undefined,
        epic_id: form.epic_id ? Number(form.epic_id) : undefined,
        assignee_id: form.assignee_id ? Number(form.assignee_id) : undefined,
      });
      onCreated();
    } catch (err) {
      setError(err.message || "Could not create story.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-line bg-white p-5 space-y-4">
      {error && <Alert>{error}</Alert>}
      <Field label="Story" htmlFor="stitle" hint='"As a [user], I want [feature], so that [benefit]."'>
        <Input id="stitle" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
      </Field>
      <Field label="Acceptance criteria" htmlFor="sac">
        <Input id="sac" value={form.acceptance_criteria} onChange={(e) => setForm((f) => ({ ...f, acceptance_criteria: e.target.value }))} />
      </Field>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Field label="Priority" htmlFor="spriority">
          <Select id="spriority" value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </Select>
        </Field>
        <Field label="Story points" htmlFor="spoints">
          <Input id="spoints" type="number" min="0" value={form.story_points} onChange={(e) => setForm((f) => ({ ...f, story_points: e.target.value }))} />
        </Field>
        <Field label="Epic" htmlFor="sepic">
          <Select id="sepic" value={form.epic_id} onChange={(e) => setForm((f) => ({ ...f, epic_id: e.target.value }))}>
            <option value="">None</option>
            {epics.map((e) => <option key={e.id} value={e.id}>{e.title}</option>)}
          </Select>
        </Field>
        <Field label="Assignee" htmlFor="sassignee">
          <Select id="sassignee" value={form.assignee_id} onChange={(e) => setForm((f) => ({ ...f, assignee_id: e.target.value }))}>
            <option value="">Unassigned</option>
            {members.map((m) => <option key={m.user_id} value={m.user_id}>{m.full_name}</option>)}
          </Select>
        </Field>
      </div>
      <div className="flex justify-end">
        <Button type="submit" disabled={saving}>{saving ? "Creating…" : "Add to backlog"}</Button>
      </div>
    </form>
  );
}
