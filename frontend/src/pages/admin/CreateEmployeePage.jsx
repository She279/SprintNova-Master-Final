import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { employeesApi } from "../../api/employees";
import { Field, Input, Select } from "../../components/ui/Field";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { EmailAssemblyLine } from "../../components/EmailAssemblyLine";

const ROLES = [
  { value: "product_owner", label: "Product Owner" },
  { value: "scrum_master", label: "Scrum Master" },
  { value: "project_manager", label: "Project Manager" },
  { value: "team_lead", label: "Team Lead" },
  { value: "developer", label: "Developer" },
  { value: "tester", label: "Tester" },
  { value: "client", label: "Client" },
];

const initialForm = {
  first_name: "",
  last_name: "",
  employee_id: "",
  role: "developer",
  department: "",
  personal_email: "",
  phone: "",
  skills: "",
  experience: "",
  joining_date: "",
};

export default function CreateEmployeePage() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [previewEmail, setPreviewEmail] = useState("");
  const [previewStatus, setPreviewStatus] = useState("idle"); // idle | generating | ready
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [created, setCreated] = useState(null);
  const debounceRef = useRef(null);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  useEffect(() => {
    if (!form.first_name || !form.last_name) {
      setPreviewEmail("");
      setPreviewStatus("idle");
      return;
    }
    setPreviewStatus("generating");
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await employeesApi.previewCompanyEmail(form.first_name, form.last_name);
        setPreviewEmail(res.company_email);
        setPreviewStatus("ready");
      } catch {
        setPreviewStatus("idle");
      }
    }, 400);
    return () => clearTimeout(debounceRef.current);
  }, [form.first_name, form.last_name]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = { ...form };
      if (!payload.joining_date) delete payload.joining_date;
      const result = await employeesApi.create(payload);
      setCreated(result);
    } catch (err) {
      setError(err.message || "Could not create employee.");
    } finally {
      setLoading(false);
    }
  }

  if (created) {
    return (
      <div className="max-w-lg">
        <div className="rounded-lg border border-line bg-white p-6">
          <div className="flex items-center gap-2 text-success mb-3">
            <span className="h-2 w-2 rounded-full bg-success" />
            <span className="text-sm font-medium">Account created</span>
          </div>
          <h2 className="font-display text-lg font-semibold">
            {created.first_name} {created.last_name}
          </h2>
          <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
            <dt className="text-muted">Company email</dt>
            <dd className="font-mono">{created.company_email}</dd>
            <dt className="text-muted">Personal email</dt>
            <dd className="font-mono">{created.personal_email}</dd>
            <dt className="text-muted">Role</dt>
            <dd className="capitalize">{created.role.replace("_", " ")}</dd>
          </dl>
          <p className="mt-4 text-sm text-muted">
            A welcome email with the login email and a temporary password has been sent to their personal
            email. They'll be required to set a new password on first login.
          </p>
          <div className="mt-6 flex gap-3">
            <Button onClick={() => navigate("/admin/employees")}>Back to employees</Button>
            <Button
              variant="secondary"
              onClick={() => {
                setCreated(null);
                setForm(initialForm);
                setPreviewEmail("");
                setPreviewStatus("idle");
              }}
            >
              Create another
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <h1 className="font-display text-xl font-semibold tracking-tight mb-1">Create employee</h1>
      <p className="text-sm text-muted mb-6">
        Enter their personal email — SprintNova generates their company login email and a temporary password
        automatically.
      </p>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
        {error && (
          <div className="md:col-span-2">
            <Alert>{error}</Alert>
          </div>
        )}

        <Field label="First name" htmlFor="first_name">
          <Input id="first_name" value={form.first_name} onChange={(e) => update("first_name", e.target.value)} required />
        </Field>
        <Field label="Last name" htmlFor="last_name">
          <Input id="last_name" value={form.last_name} onChange={(e) => update("last_name", e.target.value)} required />
        </Field>

        <div className="md:col-span-2">
          <EmailAssemblyLine email={previewEmail} status={previewStatus} />
        </div>

        <Field label="Employee ID" htmlFor="employee_id">
          <Input id="employee_id" value={form.employee_id} onChange={(e) => update("employee_id", e.target.value)} required />
        </Field>
        <Field label="Role" htmlFor="role">
          <Select id="role" value={form.role} onChange={(e) => update("role", e.target.value)}>
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Personal email" htmlFor="personal_email" hint="Any provider — Gmail, Yahoo, Outlook, college or company email all work.">
          <Input
            id="personal_email"
            type="email"
            placeholder="arun@gmail.com"
            value={form.personal_email}
            onChange={(e) => update("personal_email", e.target.value)}
            required
          />
        </Field>
        <Field label="Phone" htmlFor="phone">
          <Input id="phone" value={form.phone} onChange={(e) => update("phone", e.target.value)} />
        </Field>

        <Field label="Department" htmlFor="department">
          <Input id="department" value={form.department} onChange={(e) => update("department", e.target.value)} />
        </Field>
        <Field label="Joining date" htmlFor="joining_date">
          <Input id="joining_date" type="date" value={form.joining_date} onChange={(e) => update("joining_date", e.target.value)} />
        </Field>

        <Field label="Skills" htmlFor="skills" hint="Comma-separated">
          <Input id="skills" value={form.skills} onChange={(e) => update("skills", e.target.value)} />
        </Field>
        <Field label="Experience" htmlFor="experience">
          <Input id="experience" value={form.experience} onChange={(e) => update("experience", e.target.value)} />
        </Field>

        <div className="md:col-span-2 flex justify-end gap-3 mt-2">
          <Button type="button" variant="secondary" onClick={() => navigate("/admin/employees")}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? "Creating…" : "Create employee"}
          </Button>
        </div>
      </form>
    </div>
  );
}
