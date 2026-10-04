"""
Secure random temporary password generation. The plain-text value is only
ever held in memory long enough to hash it and hand it to the email
service -- it is never written to the database or logged in production.
"""
import secrets
import string

from app.core.config import settings

_UPPER = string.ascii_uppercase
_LOWER = string.ascii_lowercase
_DIGITS = string.digits
_SPECIAL = "!@#$%^&*?-_"


def generate_temporary_password(length: int | None = None) -> str:
    length = length or settings.TEMP_PASSWORD_LENGTH
    length = max(length, 8)

    # Guarantee at least one of each required character class.
    required = [
        secrets.choice(_UPPER),
        secrets.choice(_LOWER),
        secrets.choice(_DIGITS),
        secrets.choice(_SPECIAL),
    ]
    pool = _UPPER + _LOWER + _DIGITS + _SPECIAL
    remaining = [secrets.choice(pool) for _ in range(length - len(required))]

    password_chars = required + remaining
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)
