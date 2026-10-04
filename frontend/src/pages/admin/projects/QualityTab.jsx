import { useEffect, useState } from "react";
import { codeReviewsApi, buildsApi } from "../../../api/quality";
import { Field, Input, Select } from "../../../components/ui/Field";
import { Button } from "../../../components/ui/Button";
import { Badge, Alert } from "../../../components/ui/Feedback";

const REVIEW_TONE = { pending: "warning", approved: "success", changes_requested: "danger", rejected: "danger" };
const BUILD_TONE = { running: "warning", successful: "success", failed: "danger" };

export default function QualityTab({ projectId, members }) {
  return (
    <div className="space-y-8">
      <CodeReviewsSection projectId={projectId} members={members} />
      <BuildsSection projectId={projectId} />
    </div>
  );
}

function CodeReviewsSection({ projectId, members }) {
  const [reviews, setReviews] = useState(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ title: "", reviewer_id: "" });
  const [saving, setSaving] = useState(false);

  async function load() {
    try {
      setReviews(await codeReviewsApi.list(projectId));
    } catch (err) {
      setError(err.message || "Could not load code reviews.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await codeReviewsApi.create(projectId, { title: form.title, reviewer_id: form.reviewer_id ? Number(form.reviewer_id) : undefined });
      setForm({ title: "", reviewer_id: "" });
      load();
    } catch (err) {
      setError(err.message || "Could not create review.");
    } finally {
      setSaving(false);
    }
  }

  async function setStatus(id, status) {
    try {
      await codeReviewsApi.update(projectId, id, { status });
      load();
    } catch (err) {
      setError(err.message || "Could not update review.");
    }
  }

  return (
    <div>
      <h2 className="font-display font-semibold text-sm mb-3">Code reviews</h2>
      {error && <div className="mb-3"><Alert>{error}</Alert></div>}
      <form onSubmit={handleSubmit} className="flex flex-wrap gap-2 mb-4">
        <Input value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} placeholder="Review title" className="flex-1 min-w-[200px]" required />
        <Select value={form.reviewer_id} onChange={(e) => setForm((f) => ({ ...f, reviewer_id: e.target.value }))} className="w-44">
          <option value="">Reviewer (optional)</option>
          {members?.map((m) => <option key={m.user_id} value={m.user_id}>{m.full_name}</option>)}
        </Select>
        <Button type="submit" disabled={saving}>Request review</Button>
      </form>

      <div className="space-y-2">
        {reviews?.length === 0 && <p className="text-sm text-muted">No code reviews yet.</p>}
        {reviews?.map((r) => (
          <div key={r.id} className="rounded-md border border-line bg-white px-4 py-3 flex items-center justify-between">
            <span className="text-sm font-medium">{r.title}</span>
            <Select value={r.status} onChange={(e) => setStatus(r.id, e.target.value)} className="text-xs py-1.5 w-auto">
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="changes_requested">Changes requested</option>
              <option value="rejected">Rejected</option>
            </Select>
          </div>
        ))}
      </div>
    </div>
  );
}

function BuildsSection({ projectId }) {
  const [builds, setBuilds] = useState(null);
  const [label, setLabel] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function load() {
    try {
      setBuilds(await buildsApi.list(projectId));
    } catch (err) {
      setError(err.message || "Could not load builds.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await buildsApi.create(projectId, { label });
      setLabel("");
      load();
    } catch (err) {
      setError(err.message || "Could not start build.");
    } finally {
      setSaving(false);
    }
  }

  async function setStatus(id, status) {
    try {
      await buildsApi.update(projectId, id, { status });
      load();
    } catch (err) {
      setError(err.message || "Could not update build.");
    }
  }

  return (
    <div>
      <h2 className="font-display font-semibold text-sm mb-3">Build status</h2>
      {error && <div className="mb-3"><Alert>{error}</Alert></div>}
      <form onSubmit={handleSubmit} className="flex gap-2 mb-4">
        <Input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Build label (e.g. build-142)" className="flex-1" required />
        <Button type="submit" disabled={saving}>Trigger build</Button>
      </form>

      <div className="space-y-2">
        {builds?.length === 0 && <p className="text-sm text-muted">No builds yet.</p>}
        {builds?.map((b) => (
          <div key={b.id} className="rounded-md border border-line bg-white px-4 py-3 flex items-center justify-between">
            <div>
              <span className="text-sm font-mono font-medium">{b.label}</span>
              <p className="text-[11px] text-muted">{new Date(b.created_at).toLocaleString()}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge tone={BUILD_TONE[b.status]}>{b.status}</Badge>
              {b.status === "running" && (
                <div className="flex gap-1">
                  <button onClick={() => setStatus(b.id, "successful")} className="text-xs text-success hover:underline">Pass</button>
                  <button onClick={() => setStatus(b.id, "failed")} className="text-xs text-danger hover:underline">Fail</button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
