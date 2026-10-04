import { useEffect, useState } from "react";
import { availabilityApi } from "../../../api/availability";
import { employeesApi } from "../../../api/employees";
import { Field, Input, Select } from "../../../components/ui/Field";
import { Button } from "../../../components/ui/Button";
import { Badge, Alert } from "../../../components/ui/Feedback";
import { useAuth } from "../../../context/AuthContext";

const STATUS_TONE = { available: "success", partial: "warning", unavailable: "danger" };
const PLANNING_ROLES = ["owner_admin", "product_owner", "scrum_master"];

function isoToday(offsetDays = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

export default function AvailabilityPage() {
  const { session } = useAuth();
  const canSeeTeam = PLANNING_ROLES.includes(session?.role);

  return (
    <div className="max-w-4xl space-y-8">
      <div>
        <h1 className="font-display text-xl font-semibold tracking-tight mb-1">Availability</h1>
        <p className="text-sm text-muted">Set your own availability so sprint planning and AI suggestions reflect real capacity.</p>
      </div>

      <MyAvailability />
      {canSeeTeam && <TeamAvailability />}
    </div>
  );
}

function MyAvailability() {
  const [form, setForm] = useState({ date: isoToday(1), status: "available", hours_available: 8, note: "" });
  const [entries, setEntries] = useState(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function load() {
    try {
      setEntries(await availabilityApi.mine(isoToday(-7), isoToday(30)));
    } catch (err) {
      setError(err.message || "Could not load availability.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await availabilityApi.setMine({ ...form, hours_available: form.hours_available ? Number(form.hours_available) : null });
      load();
    } catch (err) {
      setError(err.message || "Could not save availability.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <h2 className="font-display font-semibold text-sm mb-3">My availability</h2>
      <form onSubmit={handleSubmit} className="rounded-lg border border-line bg-white p-5 grid grid-cols-1 md:grid-cols-4 gap-3 items-end mb-4">
        {error && <div className="md:col-span-4"><Alert>{error}</Alert></div>}
        <Field label="Date" htmlFor="adate">
          <Input id="adate" type="date" value={form.date} onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))} required />
        </Field>
        <Field label="Status" htmlFor="astatus">
          <Select id="astatus" value={form.status} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}>
            <option value="available">Available</option>
            <option value="partial">Partial</option>
            <option value="unavailable">Unavailable</option>
          </Select>
        </Field>
        <Field label="Hours" htmlFor="ahours">
          <Input id="ahours" type="number" min="0" max="24" value={form.hours_available} onChange={(e) => setForm((f) => ({ ...f, hours_available: e.target.value }))} />
        </Field>
        <Button type="submit" disabled={saving}>{saving ? "Saving…" : "Save"}</Button>
      </form>

      <div className="flex flex-wrap gap-2">
        {entries?.map((e) => (
          <div key={e.id} className="rounded-md border border-line bg-white px-3 py-2 text-xs">
            <span className="font-mono">{e.date}</span>{" "}
            <Badge tone={STATUS_TONE[e.status]}>{e.status}</Badge>
            {e.hours_available != null && <span className="text-muted ml-1">{e.hours_available}h</span>}
          </div>
        ))}
        {entries?.length === 0 && <p className="text-sm text-muted">No availability set for this range yet.</p>}
      </div>
    </div>
  );
}

function TeamAvailability() {
  const [employees, setEmployees] = useState([]);
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    employeesApi
      .list()
      .then((emps) => {
        setEmployees(emps);
        const ids = emps.map((e) => e.id);
        return availabilityApi.team(isoToday(0), isoToday(13), ids);
      })
      .then(setRows)
      .catch((err) => setError(err.message || "Could not load team availability."));
  }, []);

  const byUser = {};
  rows?.forEach((r) => {
    byUser[r.user_id] = byUser[r.user_id] || [];
    byUser[r.user_id].push(r);
  });

  return (
    <div>
      <h2 className="font-display font-semibold text-sm mb-3">Team availability — next 14 days</h2>
      {error && <div className="mb-4"><Alert>{error}</Alert></div>}
      {rows === null && !error && <p className="text-sm text-muted">Loading…</p>}
      <div className="space-y-3">
        {employees.map((emp) => (
          <div key={emp.id} className="rounded-lg border border-line bg-white p-4">
            <p className="text-sm font-medium mb-2">{emp.first_name} {emp.last_name}</p>
            <div className="flex flex-wrap gap-1.5">
              {(byUser[emp.id] || []).length === 0 && <span className="text-xs text-muted">No records set — assumed available.</span>}
              {(byUser[emp.id] || []).map((d, i) => (
                <span key={i} className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-black/[0.04]">
                  {d.date.slice(5)} <Badge tone={STATUS_TONE[d.status]}>{d.status[0].toUpperCase()}</Badge>
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
