"""
Dedicated email service (spec §8/§9). All outbound email for every
SprintNova module (account creation, OTP, task/bug/sprint/leave/project
notifications, etc.) must go through this module -- never send email
directly from a route handler.

Provider is chosen entirely by the EMAIL_PROVIDER env var:
  - "console": prints the email (safe default for local dev/demo, no
    credentials required, nothing sent over the network)
  - "smtp": sends via SMTP using SMTP_* env vars (works with Gmail SMTP,
    SendGrid, Resend, Amazon SES, or any standard SMTP endpoint)

No credentials, API keys, or secrets are hardcoded anywhere in this file.
"""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger("sprintnova.email")


class EmailService:
    def send(self, to_email: str, subject: str, body: str) -> None:
        if settings.EMAIL_PROVIDER == "smtp":
            self._send_via_smtp(to_email, subject, body)
        else:
            self._send_via_console(to_email, subject, body)

    # --- Providers -------------------------------------------------

    def _send_via_console(self, to_email: str, subject: str, body: str) -> None:
        logger.info(
            "\n----- [DEV EMAIL - not actually sent] -----\n"
            "To: %s\nSubject: %s\n\n%s\n--------------------------------------------",
            to_email, subject, body,
        )

    def _send_via_smtp(self, to_email: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        msg.set_content(body)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

    # --- Templated messages -----------------------------------------
    # Kept here (not inline in routes) so every module reuses the same,
    # reviewed copy and the same delivery path.

    def send_account_creation_email(
        self, *, personal_email: str, full_name: str, role: str,
        company_email: str, temporary_password: str,
    ) -> None:
        subject = "Welcome to SprintNova – Your Account Has Been Created"
        body = f"""Welcome to SprintNova!

Your SprintNova employee account has been created.

Name:
{full_name}

Role:
{role}

SprintNova Login Email:
{company_email}

Temporary Password:
{temporary_password}

Please log in using your SprintNova company email and temporary password.

For security reasons, you will be required to change your password during your first login.

Regards,
SprintNova Administration
"""
        self.send(personal_email, subject, body)

    def send_otp_email(self, *, personal_email: str, full_name: str, otp: str, purpose: str) -> None:
        subject = "SprintNova – Your One-Time Password (OTP)"
        body = f"""Hello {full_name},

Your one-time password for {purpose.replace('_', ' ')} is:

{otp}

This code will expire shortly and can only be used once.
If you did not request this, please contact your SprintNova Administrator.

Regards,
SprintNova Administration
"""
        self.send(personal_email, subject, body)

    def send_password_reset_confirmation_email(self, *, personal_email: str, full_name: str) -> None:
        subject = "SprintNova – Your Password Was Reset"
        body = f"""Hello {full_name},

This confirms that your SprintNova account password was successfully reset.
If you did not perform this action, please contact your SprintNova Administrator immediately.

Regards,
SprintNova Administration
"""
        self.send(personal_email, subject, body)

    # Placeholders other modules will call into as they're built:
    def send_task_notification_email(self, *, personal_email: str, subject: str, body: str) -> None:
        self.send(personal_email, subject, body)

    def send_bug_notification_email(self, *, personal_email: str, subject: str, body: str) -> None:
        self.send(personal_email, subject, body)

    def send_sprint_notification_email(self, *, personal_email: str, subject: str, body: str) -> None:
        self.send(personal_email, subject, body)

    def send_leave_notification_email(self, *, personal_email: str, subject: str, body: str) -> None:
        self.send(personal_email, subject, body)

    def send_project_notification_email(self, *, personal_email: str, subject: str, body: str) -> None:
        self.send(personal_email, subject, body)


email_service = EmailService()
