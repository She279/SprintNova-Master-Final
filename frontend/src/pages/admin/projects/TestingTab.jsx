import { useEffect, useState, Fragment } from "react";
import { testCasesApi } from "../../../api/testCases";
import { Field, Input, Select } from "../../../components/ui/Field";
import { Button } from "../../../components/ui/Button";
import { Badge, Alert } from "../../../components/ui/Feedback";

const STATUS_TONE = { draft: "muted", ready: "accent", passed: "success", failed: "danger", blocked: "warning" };
const PRIORITY_TONE = { critical: "danger", high: "warning", medium: "accent", low: "muted" };

export default function TestingTab({ projectId }) {
  const [cases, setCases] = useState(null);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [expandedId, setExpandedId] = useState(null);

  async function load() {
    try {
      setCases(await testCasesApi.list(projectId));
    } catch (err) {
      setError(err.message || "Could not load test cases.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs text-muted">A test case's status always reflects its most recent execution result.</p>
        <Button onClick={() => setCreating((v) => !v)}>{creating ? "Cancel" : "+ New test case"}</Button>
      </div>

      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      {creating && (
        <div className="mb-5">
          <CreateTestCaseForm projectId={projectId} onCreated={() => { setCreating(false); load(); }} />
        </div>
      )}

      <div className="rounded-lg border border-line bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-black/[0.015] text-left text-xs uppercase tracking-wider text-muted">
              <th className="px-5 py-3 font-medium">Test case</th>
              <th className="px-5 py-3 font-medium">Priority</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {cases === null && <tr><td colSpan={4} className="px-5 py-8 text-center text-muted">Loading…</td></tr>}
            {cases?.length === 0 && <tr><td colSpan={4} className="px-5 py-10 text-center text-muted">No test cases yet.</td></tr>}
            {cases?.map((tc) => (
              <Fragment key={tc.id}>
                <tr className="border-b border-line last:border-0">
                  <td className="px-5 py-3">
                    <p className="font-medium">{tc.title}</p>
                    <p className="text-xs text-muted font-mono">{tc.key}</p>
                  </td>
                  <td className="px-5 py-3"><Badge tone={PRIORITY_TONE[tc.priority]}>{tc.priority}</Badge></td>
                  <td className="px-5 py-3"><Badge tone={STATUS_TONE[tc.status]}>{tc.status}</Badge></td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => setExpandedId(expandedId === tc.id ? null : tc.id)}
                      className="text-xs font-medium text-accent hover:underline"
                    >
                      {expandedId === tc.id ? "Close" : "Execute / History"}
                    </button>
                  </td>
                </tr>
                {expandedId === tc.id && (
                  <tr className="border-b border-line bg-black/[0.01]">
                    <td colSpan={4} className="px-5 py-4">
                      <TestCaseDetail projectId={projectId} testCase={tc} onExecuted={load} />
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CreateTestCaseForm({ projectId, onCreated }) {
  const [form, setForm] = useState({ title: "", steps: "", expected_result: "", priority: "medium" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await testCasesApi.create(projectId, form);
      onCreated();
    } catch (err) {
      setError(err.message || "Could not create test case.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-line bg-white p-5 space-y-4">
      {error && <Alert>{error}</Alert>}
      <Field label="Title" htmlFor="tctitle">
        <Input id="tctitle" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
      </Field>
      <Field label="Steps" htmlFor="tcsteps" hint="One step per line">
        <textarea
          id="tcsteps" rows={3} value={form.steps} onChange={(e) => setForm((f) => ({ ...f, steps: e.target.value }))}
          className="w-full rounded-md border border-line bg-white px-3.5 py-2.5 text-sm focus:border-accent focus:ring-1 focus:ring-accent outline-none"
        />
      </Field>
      <Field label="Expected result" htmlFor="tcexpected">
        <Input id="tcexpected" value={form.expected_result} onChange={(e) => setForm((f) => ({ ...f, expected_result: e.target.value }))} />
      </Field>
      <Field label="Priority" htmlFor="tcpriority">
        <Select id="tcpriority" value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))} className="max-w-xs">
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </Select>
      </Field>
      <div className="flex justify-end">
        <Button type="submit" disabled={saving}>{saving ? "Creating…" : "Add test case"}</Button>
      </div>
    </form>
  );
}

function TestCaseDetail({ projectId, testCase, onExecuted }) {
  const [executions, setExecutions] = useState(null);
  const [result, setResult] = useState("pass");
  const [actualResult, setActualResult] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      setExecutions(await testCasesApi.executions(projectId, testCase.id));
    } catch (err) {
      setError(err.message || "Could not load executions.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [testCase.id]);

  async function submitExecution(e) {
    e.preventDefault();
    setError("");
    try {
      await testCasesApi.execute(projectId, testCase.id, { result, actual_result: actualResult || undefined });
      setActualResult("");
      load();
      onExecuted();
    } catch (err) {
      setError(err.message || "Could not record execution.");
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      <div>
        {testCase.steps && <p className="text-xs text-muted whitespace-pre-line mb-2">{testCase.steps}</p>}
        {testCase.expected_result && <p className="text-xs"><span className="text-muted">Expected: </span>{testCase.expected_result}</p>}

        <form onSubmit={submitExecution} className="mt-3 space-y-2">
          {error && <Alert>{error}</Alert>}
          <div className="flex gap-2">
            <Select value={result} onChange={(e) => setResult(e.target.value)} className="w-32 text-xs py-1.5">
              <option value="pass">Pass</option>
              <option value="fail">Fail</option>
              <option value="blocked">Blocked</option>
            </Select>
            <Input value={actualResult} onChange={(e) => setActualResult(e.target.value)} placeholder="Actual result / notes" className="flex-1 text-xs py-1.5" />
            <Button type="submit" variant="secondary">Record</Button>
          </div>
        </form>
      </div>
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-muted mb-2">Execution history</p>
        <div className="space-y-1.5 max-h-40 overflow-y-auto">
          {executions?.length === 0 && <p className="text-xs text-muted">No executions yet.</p>}
          {executions?.map((e) => (
            <div key={e.id} className="text-xs">
              <Badge tone={e.result === "pass" ? "success" : e.result === "fail" ? "danger" : "warning"}>{e.result}</Badge>
              <span className="ml-2 text-muted">{new Date(e.executed_at).toLocaleString()}</span>
              {e.actual_result && <p className="text-muted mt-0.5">{e.actual_result}</p>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
