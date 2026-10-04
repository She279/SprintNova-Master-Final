from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest, LoginResponse, ChangePasswordRequest,
    ForgotPasswordRequest, VerifyOTPRequest, ResetPasswordRequest,
)
from app.api.deps import get_current_user
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    result = auth_service.login(
        db,
        company_email=payload.company_email,
        password=payload.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result


@router.post("/change-password", status_code=204)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),  # note: NOT require_password_already_set --
    # this is the one endpoint reachable precisely because must_change_password is true.
):
    auth_service.change_password(
        db, user=user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )


@router.post("/forgot-password", status_code=202)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    auth_service.request_password_reset(db, company_email=payload.company_email)
    # Generic response regardless of whether the account exists (avoids
    # leaking which company emails are registered).
    return {"message": "If the account exists, an OTP has been sent to the registered personal email."}


@router.post("/verify-otp", status_code=204)
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    auth_service.verify_otp(db, company_email=payload.company_email, otp_value=payload.otp)


@router.post("/reset-password", status_code=204)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    auth_service.reset_password(
        db,
        company_email=payload.company_email,
        otp_value=payload.otp,
        new_password=payload.new_password,
    )
