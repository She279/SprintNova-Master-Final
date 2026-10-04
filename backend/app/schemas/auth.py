from pydantic import BaseModel, EmailStr, field_validator


class LoginRequest(BaseModel):
    company_email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool
    role: str
    full_name: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

    @field_validator("confirm_new_password")
    @classmethod
    def validate_match(cls, v: str, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class ForgotPasswordRequest(BaseModel):
    company_email: EmailStr


class VerifyOTPRequest(BaseModel):
    company_email: EmailStr
    otp: str


class ResetPasswordRequest(BaseModel):
    company_email: EmailStr
    otp: str
    new_password: str
    confirm_new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

    @field_validator("confirm_new_password")
    @classmethod
    def validate_match(cls, v: str, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


def _validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain an uppercase letter")
    if not any(c.islower() for c in password):
        raise ValueError("Password must contain a lowercase letter")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain a number")
    if not any(not c.isalnum() for c in password):
        raise ValueError("Password must contain a special character")
    return password
