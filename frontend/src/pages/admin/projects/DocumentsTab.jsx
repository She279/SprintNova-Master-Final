import { useEffect, useState } from "react";
import { documentsApi } from "../../../api/documents";
import { Field, Input, Select } from "../../../components/ui/Field";
import { Button } from "../../../components/ui/Button";
import { Badge, Alert } from "../../../components/ui/Feedback";

const DOC_TYPE_LABEL = {
  documentation: "Documentation",
  requirement: "Requirement",
  sprint_note: "Sprint note",
  guideline: "Guideline",
  testing_doc: "Testing doc",
};

export default function DocumentsTab({ projectId }) {
  const [docs, setDocs] = useState(null);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [expandedId, setExpandedId] = useState(null);

  async function load() {
    try {
      setDocs(await documentsApi.list(projectId));
    } catch (err) {
      setError(err.message || "Could not load documents.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleDelete(id) {
    try {
      await documentsApi.remove(projectId, id);
      load();
    } catch (err) {
      setError(err.message || "Could not delete document.");
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs text-muted">
          The AI Assistant searches these documents to answer project questions — add requirements, sprint
          notes, and guidelines here.
        </p>
        <Button onClick={() => setCreating((v) => !v)}>{creating ? "Cancel" : "+ New document"}</Button>
      </div>

      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      {creating && (
        <div className="mb-5">
          <CreateDocumentForm projectId={projectId} onCreated={() => { setCreating(false); load(); }} />
        </div>
      )}

      <div className="space-y-2">
        {docs === null && <p className="text-sm text-muted">Loading…</p>}
        {docs?.length === 0 && (
          <div className="rounded-lg border border-dashed border-line p-10 text-center text-sm text-muted">
            No documents yet. Add requirements or sprint notes so the AI Assistant can reference them.
          </div>
        )}
        {docs?.map((doc) => (
          <div key={doc.id} className="rounded-lg border border-line bg-white p-4">
            <div className="flex items-center justify-between">
              <button
                onClick={() => setExpandedId(expandedId === doc.id ? null : doc.id)}
                className="text-left flex items-center gap-2"
              >
                <span className="text-sm font-medium">{doc.title}</span>
                <Badge tone="muted">{DOC_TYPE_LABEL[doc.doc_type]}</Badge>
              </button>
              <button onClick={() => handleDelete(doc.id)} className="text-xs text-danger hover:underline">
                Delete
              </button>
            </div>
            {expandedId === doc.id && (
              <p className="text-sm text-ink/80 mt-3 whitespace-pre-line border-t border-line pt-3">{doc.content}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function CreateDocumentForm({ projectId, onCreated }) {
  const [form, setForm] = useState({ title: "", doc_type: "documentation", content: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await documentsApi.create(projectId, form);
      onCreated();
    } catch (err) {
      setError(err.message || "Could not create document.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-line bg-white p-5 space-y-4">
      {error && <Alert>{error}</Alert>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Title" htmlFor="doctitle">
          <Input id="doctitle" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
        </Field>
        <Field label="Type" htmlFor="doctype">
          <Select id="doctype" value={form.doc_type} onChange={(e) => setForm((f) => ({ ...f, doc_type: e.target.value }))}>
            {Object.entries(DOC_TYPE_LABEL).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </Select>
        </Field>
      </div>
      <Field label="Content" htmlFor="doccontent">
        <textarea
          id="doccontent" rows={6} value={form.content} onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))}
          className="w-full rounded-md border border-line bg-white px-3.5 py-2.5 text-sm focus:border-accent focus:ring-1 focus:ring-accent outline-none"
          required
        />
      </Field>
      <div className="flex justify-end">
        <Button type="submit" disabled={saving}>{saving ? "Saving…" : "Add document"}</Button>
      </div>
    </form>
  );
}
