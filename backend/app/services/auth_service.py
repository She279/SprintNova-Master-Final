"""
Authentication business logic: login, first-login forced password change,
and the OTP-based forgot-password flow (spec §10-§12).
"""
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.login_history import LoginHistory
from app.models.otp import OTP, OTPPurpose
from app.models.user import User
from app.services.email_service import email_service
from app.utils.otp_generator import generate_otp


def login(
    db: Session, *, company_email: str, password: str,
    ip_address: str | None, user_agent: str | None,
) -> dict:
    user = db.query(User).filter(User.company_email == company_email).first()

    def record(success: bool, reason: str | None = None):
        db.add(LoginHistory(
            user_id=user.id if user else None,
            company_email_attempted=company_email,
            success=success,
            failure_reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
        ))
        db.commit()

    if not user:
        record(False, "account_not_found")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid company email or password")

    if not user.is_active:
        record(False, "account_inactive")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is deactivated. Contact your administrator.")

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        db.commit()
        record(False, "bad_password")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid company email or password")

    user.failed_login_attempts = 0
    db.commit()
    record(True)

    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})

    return {
        "access_token": token,
        "must_change_password": user.must_change_password,
        "role": user.role.value,
        "full_name": f"{user.first_name} {user.last_name}",
    }


def change_password(db: Session, *, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Current password is incorrect")

    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    db.commit()


def request_password_reset(db: Session, *, company_email: str) -> None:
    """Always returns success-shaped behavior to the caller (route layer)
    regardless of whether the account exists, to avoid account enumeration."""
    user = db.query(User).filter(User.company_email == company_email).first()
    if not user or not user.is_active:
        return

    otp_value = generate_otp()
    otp_record = OTP(
        user_id=user.id,
        purpose=OTPPurpose.PASSWORD_RESET,
        otp_hash=hash_password(otp_value),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
    )
    db.add(otp_record)
    db.commit()

    # OTP always goes to the PERSONAL email (spec §12), not the company email.
    email_service.send_otp_email(
        personal_email=user.personal_email,
        full_name=f"{user.first_name} {user.last_name}",
        otp=otp_value,
        purpose="password_reset",
    )


def _get_valid_otp(db: Session, user: User) -> OTP:
    otp_record = (
        db.query(OTP)
        .filter(OTP.user_id == user.id, OTP.purpose == OTPPurpose.PASSWORD_RESET, OTP.is_used == False)  # noqa: E712
        .order_by(OTP.created_at.desc())
        .first()
    )
    if not otp_record:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No active OTP found. Please request a new one.")
    if otp_record.expires_at < datetime.utcnow():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "OTP has expired. Please request a new one.")
    if otp_record.attempts_used >= settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Please request a new OTP.")
    return otp_record


def verify_otp(db: Session, *, company_email: str, otp_value: str) -> None:
    user = db.query(User).filter(User.company_email == company_email).first()
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid request")

    otp_record = _get_valid_otp(db, user)
    otp_record.attempts_used += 1

    if not verify_password(otp_value, otp_record.otp_hash):
        db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect OTP")

    db.commit()


def reset_password(db: Session, *, company_email: str, otp_value: str, new_password: str) -> None:
    user = db.query(User).filter(User.company_email == company_email).first()
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid request")

    otp_record = _get_valid_otp(db, user)

    if not verify_password(otp_value, otp_record.otp_hash):
        otp_record.attempts_used += 1
        db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect OTP")

    otp_record.is_used = True
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    db.commit()

    email_service.send_password_reset_confirmation_email(
        personal_email=user.personal_email,
        full_name=f"{user.first_name} {user.last_name}",
    )
