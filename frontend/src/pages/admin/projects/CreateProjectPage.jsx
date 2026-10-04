import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectsApi } from "../../../api/projects";
import { clientsApi } from "../../../api/clients";
import { employeesApi } from "../../../api/employees";
import { Field, Input, Select } from "../../../components/ui/Field";
import { Button } from "../../../components/ui/Button";
import { Alert } from "../../../components/ui/Feedback";

const initialForm = {
  code: "",
  name: "",
  description: "",
  client_id: "",
  product_owner_id: "",
  start_date: "",
  end_date: "",
};

export default function CreateProjectPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [clients, setClients] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [abstractFile, setAbstractFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisNote, setAnalysisNote] = useState("");

  useEffect(() => {
    clientsApi.list().then(setClients).catch(() => {});
    employeesApi.list().then(setEmployees).catch(() => {});
  }, []);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleAbstractAnalysis() {
    if (!abstractFile) return;
    setError("");
    setAnalysisNote("");
    setAnalyzing(true);
    try {
      const draft = await projectsApi.analyzeAbstract(abstractFile);
      setForm((current) => ({
        ...current,
        code: draft.code || current.code,
        name: draft.name || current.name,
        description: draft.description || current.description,
      }));
      setAnalysisNote(`${draft.ai_generated ? "AI" : "Smart draft"} suggestions added. Review and edit them before creating the project.`);
    } catch (err) {
      setError(err.message || "Could not analyze the project abstract.");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = { ...form };
      if (!payload.client_id) delete payload.client_id;
      else payload.client_id = Number(payload.client_id);
      if (!payload.product_owner_id) delete payload.product_owner_id;
      else payload.product_owner_id = Number(payload.product_owner_id);
      if (!payload.start_date) delete payload.start_date;
      if (!payload.end_date) delete payload.end_date;
      if (!payload.description) delete payload.description;

      const project = await projectsApi.create(payload);
      navigate(`/admin/projects/${project.id}`);
    } catch (err) {
      setError(err.message || "Could not create project.");
    } finally {
      setLoading(false);
    }
  }

  const productOwners = employees.filter((e) => e.role === "product_owner" || e.role === "owner_admin");

  return (
    <div className="max-w-2xl">
      <h1 className="font-display text-xl font-semibold tracking-tight mb-1">New project</h1>
      <p className="text-sm text-muted mb-6">
        The Product Owner you assign is automatically added to the project's team.
      </p>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
        <div className="md:col-span-2 rounded-lg border border-accent/20 bg-accent/[0.04] p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <Field
              label="Project abstract"
              htmlFor="abstract-file"
              hint="Upload a .txt, .md, .pdf, or .docx file to draft the code, title, and description."
            >
              <Input
                id="abstract-file"
                type="file"
                accept=".txt,.md,.pdf,.docx,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(e) => setAbstractFile(e.target.files?.[0] || null)}
                className="file:mr-3 file:rounded file:border-0 file:bg-accent/10 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-accent"
              />
            </Field>
            <Button type="button" variant="secondary" onClick={handleAbstractAnalysis} disabled={!abstractFile || analyzing}>
              {analyzing ? "Analyzing…" : "Analyze abstract"}
            </Button>
          </div>
          {analysisNote && <p className="mt-3 text-xs text-accent">{analysisNote}</p>}
        </div>

        {error && (
          <div className="md:col-span-2">
            <Alert>{error}</Alert>
          </div>
        )}

        <Field label="Project code" htmlFor="code" hint="Short, unique — e.g. SN-001">
          <Input id="code" className="font-mono" value={form.code} onChange={(e) => update("code", e.target.value)} required />
        </Field>
        <Field label="Project name" htmlFor="name">
          <Input id="name" value={form.name} onChange={(e) => update("name", e.target.value)} required />
        </Field>

        <div className="md:col-span-2">
          <Field label="Description" htmlFor="description">
            <textarea
              id="description"
              rows={3}
              className="w-full rounded-md border border-line bg-white px-3.5 py-2.5 text-sm focus:border-accent focus:ring-1 focus:ring-accent outline-none"
              value={form.description}
              onChange={(e) => update("description", e.target.value)}
            />
          </Field>
        </div>

        <Field label="Client" htmlFor="client_id" hint="Optional">
          <Select id="client_id" value={form.client_id} onChange={(e) => update("client_id", e.target.value)}>
            <option value="">No client</option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} {c.company_name ? `(${c.company_name})` : ""}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Product Owner" htmlFor="product_owner_id" hint="Optional — auto-added to the team">
          <Select id="product_owner_id" value={form.product_owner_id} onChange={(e) => update("product_owner_id", e.target.value)}>
            <option value="">Unassigned</option>
            {productOwners.map((e) => (
              <option key={e.id} value={e.id}>
                {e.first_name} {e.last_name}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Start date" htmlFor="start_date">
          <Input id="start_date" type="date" value={form.start_date} onChange={(e) => update("start_date", e.target.value)} />
        </Field>
        <Field label="End date" htmlFor="end_date">
          <Input id="end_date" type="date" value={form.end_date} onChange={(e) => update("end_date", e.target.value)} />
        </Field>

        <div className="md:col-span-2 flex justify-end gap-3 mt-2">
          <Button type="button" variant="secondary" onClick={() => navigate("/admin/projects")}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? "Creating…" : "Create project"}
          </Button>
        </div>
      </form>
    </div>
  );
}
