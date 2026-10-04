import { useEffect, useState } from "react";
import { leaveApi } from "../../../api/leave";
import { Field, Input, Select } from "../../../components/ui/Field";
import { Button } from "../../../components/ui/Button";
import { Badge, Alert } from "../../../components/ui/Feedback";
import { Tabs } from "../../../components/ui/Tabs";
import { useAuth } from "../../../context/AuthContext";

const REVIEW_ROLES = ["owner_admin", "scrum_master"];
const STATUS_TONE = { pending: "warning", approved: "success", rejected: "danger", cancelled: "muted" };

export default function LeaveRequestsPage() {
  const { session } = useAuth();
  const canReview = REVIEW_ROLES.includes(session?.role);
  const [tab, setTab] = useState("mine");

  return (
    <div className="max-w-3xl">
      <h1 className="font-display text-xl font-semibold tracking-tight mb-1">Leave & permission</h1>
      <p className="text-sm text-muted mb-6">
        Leave blocks full days; permission is a short window within a single day.
      </p>

      {canReview && (
        <Tabs
          tabs={[
            { value: "mine", label: "My requests" },
            { value: "team", label: "Team requests" },
          ]}
          active={tab}
          onChange={setTab}
        />
      )}

      {tab === "mine" && <MyRequests />}
      {tab === "team" && canReview && <TeamRequests />}
    </div>
  );
}

function MyRequests() {
  const [requests, setRequests] = useState(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ type: "leave", start_date: "", end_date: "", start_time: "", end_time: "", reason: "" });
  const [saving, setSaving] = useState(false);

  async function load() {
    try {
      setRequests(await leaveApi.mine());
    } catch (err) {
      setError(err.message || "Could not load requests.");
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
      const payload = { ...form };
      if (payload.type === "leave") {
        delete payload.start_time;
        delete payload.end_time;
      } else {
        payload.end_date = payload.start_date;
      }
      await leaveApi.create(payload);
      setForm({ type: "leave", start_date: "", end_date: "", start_time: "", end_time: "", reason: "" });
      load();
    } catch (err) {
      setError(err.message || "Could not submit request.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="rounded-lg border border-line bg-white p-5 mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        {error && <div className="md:col-span-2"><Alert>{error}</Alert></div>}
        <Field label="Type" htmlFor="ltype">
          <Select id="ltype" value={form.type} onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}>
            <option value="leave">Leave (full day+)</option>
            <option value="permission">Permission (same day, short)</option>
          </Select>
        </Field>
        <div />
        <Field label="Start date" htmlFor="lstart">
          <Input id="lstart" type="date" value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} required />
        </Field>
        {form.type === "leave" ? (
          <Field label="End date" htmlFor="lend">
            <Input id="lend" type="date" value={form.end_date} onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))} required />
          </Field>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            <Field label="From" htmlFor="ltime1">
              <Input id="ltime1" type="time" value={form.start_time} onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))} required />
            </Field>
            <Field label="To" htmlFor="ltime2">
              <Input id="ltime2" type="time" value={form.end_time} onChange={(e) => setForm((f) => ({ ...f, end_time: e.target.value }))} required />
            </Field>
          </div>
        )}
        <div className="md:col-span-2">
          <Field label="Reason" htmlFor="lreason" hint="Optional">
            <Input id="lreason" value={form.reason} onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))} />
          </Field>
        </div>
        <div className="md:col-span-2 flex justify-end">
          <Button type="submit" disabled={saving}>
            {saving ? "Submitting…" : "Submit request"}
          </Button>
        </div>
      </form>

      <div className="rounded-lg border border-line bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-black/[0.015] text-left text-xs uppercase tracking-wider text-muted">
              <th className="px-5 py-3 font-medium">Type</th>
              <th className="px-5 py-3 font-medium">Dates</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium">Note</th>
            </tr>
          </thead>
          <tbody>
            {requests?.length === 0 && (
              <tr><td colSpan={4} className="px-5 py-8 text-center text-muted">No requests yet.</td></tr>
            )}
            {requests?.map((r) => (
              <tr key={r.id} className="border-b border-line last:border-0">
                <td className="px-5 py-3 capitalize">{r.type}</td>
                <td className="px-5 py-3 font-mono text-xs">
                  {r.start_date}{r.end_date !== r.start_date ? ` → ${r.end_date}` : ""}
                  {r.start_time ? ` · ${r.start_time}–${r.end_time}` : ""}
                </td>
                <td className="px-5 py-3"><Badge tone={STATUS_TONE[r.status]}>{r.status}</Badge></td>
                <td className="px-5 py-3 text-xs text-muted">{r.review_note || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TeamRequests() {
  const [requests, setRequests] = useState(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function load() {
    try {
      setRequests(await leaveApi.all());
    } catch (err) {
      setError(err.message || "Could not load requests.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function decide(id, approve) {
    setBusyId(id);
    try {
      await leaveApi.decide(id, approve);
      load();
    } catch (err) {
      setError(err.message || "Could not update request.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      {error && <div className="mb-4"><Alert>{error}</Alert></div>}
      <div className="rounded-lg border border-line bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-black/[0.015] text-left text-xs uppercase tracking-wider text-muted">
              <th className="px-5 py-3 font-medium">Employee</th>
              <th className="px-5 py-3 font-medium">Type</th>
              <th className="px-5 py-3 font-medium">Dates</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests?.length === 0 && (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-muted">No requests yet.</td></tr>
            )}
            {requests?.map((r) => (
              <tr key={r.id} className="border-b border-line last:border-0">
                <td className="px-5 py-3">{r.full_name}</td>
                <td className="px-5 py-3 capitalize">{r.type}</td>
                <td className="px-5 py-3 font-mono text-xs">
                  {r.start_date}{r.end_date !== r.start_date ? ` → ${r.end_date}` : ""}
                </td>
                <td className="px-5 py-3"><Badge tone={STATUS_TONE[r.status]}>{r.status}</Badge></td>
                <td className="px-5 py-3 text-right">
                  {r.status === "pending" ? (
                    <div className="flex gap-2 justify-end">
                      <button onClick={() => decide(r.id, true)} disabled={busyId === r.id} className="text-xs font-medium text-success hover:underline">
                        Approve
                      </button>
                      <button onClick={() => decide(r.id, false)} disabled={busyId === r.id} className="text-xs font-medium text-danger hover:underline">
                        Reject
                      </button>
                    </div>
                  ) : (
                    <span className="text-xs text-muted">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
