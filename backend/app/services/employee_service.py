"""
Employee (account) creation business logic -- the Admin-facing half of
Module 1. Keeps the workflow from spec §6 out of the route handler so
future modules can reuse `create_employee` (e.g. bulk CSV import) without
duplicating it.
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import EmployeeCreateRequest
from app.services.email_service import email_service
from app.utils.email_generator import generate_company_email
from app.utils.password_generator import generate_temporary_password


def preview_company_email(db: Session, first_name: str, last_name: str) -> str:
    """Lets the Admin see the generated address before confirming creation (spec §18)."""
    return generate_company_email(db, first_name, last_name)


def create_employee(db: Session, payload: EmployeeCreateRequest) -> User:
    if db.query(User).filter(User.employee_id == payload.employee_id).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "employee_id already exists")
    if db.query(User).filter(User.personal_email == payload.personal_email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "personal_email already registered")

    company_email = generate_company_email(db, payload.first_name, payload.last_name)
    temporary_password = generate_temporary_password()

    user = User(
        employee_id=payload.employee_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        personal_email=payload.personal_email,
        company_email=company_email,
        phone=payload.phone,
        role=payload.role,
        department=payload.department,
        skills=payload.skills,
        experience=payload.experience,
        joining_date=payload.joining_date,
        password_hash=hash_password(temporary_password),
        must_change_password=True,
        is_active=True,
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Could not create employee (duplicate field)")
    db.refresh(user)

    # Send the temp password to the PERSONAL email only; the plain-text
    # value is discarded from memory once this call returns.
    email_service.send_account_creation_email(
        personal_email=user.personal_email,
        full_name=f"{user.first_name} {user.last_name}",
        role=user.role.value,
        company_email=user.company_email,
        temporary_password=temporary_password,
    )

    return user
