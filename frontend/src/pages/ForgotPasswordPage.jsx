import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthShell } from "../components/layout/AuthShell";
import { Field, Input } from "../components/ui/Field";
import { Button } from "../components/ui/Button";
import { Alert } from "../components/ui/Feedback";
import { PasswordChecklist } from "../components/PasswordChecklist";
import { authApi } from "../api/auth";
import { isPasswordValid } from "../utils/password";
import { ApiError } from "../api/client";

const STEPS = { REQUEST: "request", VERIFY: "verify", RESET: "reset", DONE: "done" };

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(STEPS.REQUEST);
  const [companyEmail, setCompanyEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleRequest(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.forgotPassword(companyEmail);
      setStep(STEPS.VERIFY);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.verifyOtp(companyEmail, otp);
      setStep(STEPS.RESET);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Incorrect or expired code.");
    } finally {
      setLoading(false);
    }
  }

  async function handleReset(e) {
    e.preventDefault();
    setError("");
    if (!isPasswordValid(newPassword)) {
      setError("Your new password doesn't meet all the requirements below.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation don't match.");
      return;
    }
    setLoading(true);
    try {
      await authApi.resetPassword(companyEmail, otp, newPassword, confirmPassword);
      setStep(STEPS.DONE);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (step === STEPS.DONE) {
    return (
      <AuthShell eyebrow="Password reset" title="Your password has been reset" subtitle="You can now sign in with your new password.">
        <Button className="w-full" onClick={() => navigate("/login")}>
          Back to sign in
        </Button>
      </AuthShell>
    );
  }

  if (step === STEPS.RESET) {
    return (
      <AuthShell eyebrow="Step 3 of 3" title="Choose a new password" subtitle="This will become your SprintNova login password.">
        <form onSubmit={handleReset} className="flex flex-col gap-4">
          {error && <Alert>{error}</Alert>}
          <Field label="New password" htmlFor="new_password">
            <Input id="new_password" type="password" autoComplete="new-password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
            <PasswordChecklist password={newPassword} />
          </Field>
          <Field label="Confirm new password" htmlFor="confirm_password">
            <Input id="confirm_password" type="password" autoComplete="new-password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
          </Field>
          <Button type="submit" disabled={loading} className="w-full mt-1">
            {loading ? "Resetting…" : "Reset password"}
          </Button>
        </form>
      </AuthShell>
    );
  }

  if (step === STEPS.VERIFY) {
    return (
      <AuthShell eyebrow="Step 2 of 3" title="Enter the code" subtitle={`We sent a one-time code to the personal email on file for ${companyEmail}.`}>
        <form onSubmit={handleVerify} className="flex flex-col gap-4">
          {error && <Alert>{error}</Alert>}
          <Field label="One-time code" htmlFor="otp" hint="Codes expire after a few minutes.">
            <Input id="otp" inputMode="numeric" maxLength={6} className="font-mono tracking-[0.3em] text-center text-lg" value={otp} onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))} required />
          </Field>
          <Button type="submit" disabled={loading} className="w-full mt-1">
            {loading ? "Verifying…" : "Verify code"}
          </Button>
        </form>
      </AuthShell>
    );
  }

  return (
    <AuthShell eyebrow="Step 1 of 3" title="Reset your password" subtitle="Enter your SprintNova company email. We'll send a one-time code to your personal email on file.">
      <form onSubmit={handleRequest} className="flex flex-col gap-4">
        {error && <Alert>{error}</Alert>}
        <Field label="Company email" htmlFor="company_email">
          <Input id="company_email" type="email" placeholder="arun.kumar@sprintnova.com" value={companyEmail} onChange={(e) => setCompanyEmail(e.target.value)} required />
        </Field>
        <Button type="submit" disabled={loading} className="w-full mt-1">
          {loading ? "Sending…" : "Send code"}
        </Button>
        <Link to="/login" className="text-center text-xs text-muted hover:text-ink">
          Back to sign in
        </Link>
      </form>
    </AuthShell>
  );
}
