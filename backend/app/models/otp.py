import enum
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Integer, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OTPPurpose(str, enum.Enum):
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"


class OTP(Base):
    """
    OTP codes are always stored hashed, never in plain text, per spec §12.
    Enforces expiry, single-use, and a max-attempts counter for rate limiting.
    """
    __tablename__ = "otps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    purpose: Mapped[OTPPurpose] = mapped_column(SAEnum(OTPPurpose), nullable=False)

    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    attempts_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_used: Mapped[bool] = mapped_column(default=False, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
