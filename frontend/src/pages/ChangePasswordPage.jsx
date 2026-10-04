import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthShell } from "../components/layout/AuthShell";
import { Field, Input } from "../components/ui/Field";
import { Button } from "../components/ui/Button";
import { Alert } from "../components/ui/Feedback";
import { PasswordChecklist } from "../components/PasswordChecklist";
import { authApi } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import { isPasswordValid } from "../utils/password";
import { ApiError } from "../api/client";

export default function ChangePasswordPage() {
  const { completePasswordChange, session } = useAuth();
  const navigate = useNavigate();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const mismatch = confirm.length > 0 && confirm !== next;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!isPasswordValid(next)) {
      setError("Your new password doesn't meet all the requirements below.");
      return;
    }
    if (mismatch) {
      setError("New password and confirmation don't match.");
      return;
    }
    setLoading(true);
    try {
      await authApi.changePassword(current, next, confirm);
      completePasswordChange();
      navigate("/admin/employees");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      eyebrow="Required step"
      title="Set a new password"
      subtitle={
        session?.companyEmail
          ? `Signed in as ${session.companyEmail}. You must change your temporary password before continuing.`
          : "You must change your temporary password before continuing."
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {error && <Alert>{error}</Alert>}
        <Field label="Temporary password" htmlFor="current">
          <Input
            id="current"
            type="password"
            autoComplete="current-password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            required
          />
        </Field>
        <Field label="New password" htmlFor="next">
          <Input
            id="next"
            type="password"
            autoComplete="new-password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            required
          />
          <PasswordChecklist password={next} />
        </Field>
        <Field label="Confirm new password" htmlFor="confirm" error={mismatch ? "Doesn't match" : ""}>
          <Input
            id="confirm"
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
          />
        </Field>
        <Button type="submit" disabled={loading} className="w-full mt-1">
          {loading ? "Updating…" : "Update password & continue"}
        </Button>
      </form>
    </AuthShell>
  );
}
