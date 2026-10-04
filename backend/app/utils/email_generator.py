"""
Generates unique SprintNova company email addresses.

firstName.lastName@<COMPANY_EMAIL_DOMAIN>, with a numeric suffix appended
on collision (arun.kumar1@..., arun.kumar2@..., ...). The domain always
comes from settings.COMPANY_EMAIL_DOMAIN -- never hardcoded here.
"""
import re

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z]", "", name).lower()
    return slug or "user"


def generate_company_email(db: Session, first_name: str, last_name: str) -> str:
    base_local_part = f"{_slugify(first_name)}.{_slugify(last_name)}"
    domain = settings.COMPANY_EMAIL_DOMAIN

    candidate = f"{base_local_part}@{domain}"
    suffix = 0
    while db.query(User).filter(User.company_email == candidate).first() is not None:
        suffix += 1
        candidate = f"{base_local_part}{suffix}@{domain}"

    return candidate
