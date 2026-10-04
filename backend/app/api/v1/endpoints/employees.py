from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.role import RoleEnum
from app.models.user import User
from app.models.login_history import LoginHistory
from app.schemas.user import (
    EmployeeCreateRequest, EmployeeCreateResponse, EmployeeListItem,
    GeneratedEmailPreview, EmployeeStatusUpdate,
)
from app.api.deps import require_role
from app.services import employee_service

router = APIRouter(prefix="/employees", tags=["Employee Management"])

_ADMIN_ONLY = require_role(RoleEnum.OWNER_ADMIN)


@router.get("/preview-company-email", response_model=GeneratedEmailPreview)
def preview_company_email(
    first_name: str = Query(...),
    last_name: str = Query(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(_ADMIN_ONLY),
):
    """Lets the Admin see the generated company email before confirming
    creation (spec §18) without persisting anything."""
    return GeneratedEmailPreview(company_email=employee_service.preview_company_email(db, first_name, last_name))


@router.post("", response_model=EmployeeCreateResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(_ADMIN_ONLY),
):
    return employee_service.create_employee(db, payload)


@router.get("", response_model=list[EmployeeListItem])
def list_employees(db: Session = Depends(get_db), _admin: User = Depends(_ADMIN_ONLY)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get("/{employee_pk}", response_model=EmployeeListItem)
def get_employee(employee_pk: int, db: Session = Depends(get_db), _admin: User = Depends(_ADMIN_ONLY)):
    user = db.get(User, employee_pk)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
    return user


@router.patch("/{employee_pk}/status", response_model=EmployeeListItem)
def set_employee_status(
    employee_pk: int, payload: EmployeeStatusUpdate,
    db: Session = Depends(get_db), _admin: User = Depends(_ADMIN_ONLY),
):
    user = db.get(User, employee_pk)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/{employee_pk}/login-history")
def get_login_history(employee_pk: int, db: Session = Depends(get_db), _admin: User = Depends(_ADMIN_ONLY)):
    user = db.get(User, employee_pk)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
    records = (
        db.query(LoginHistory)
        .filter(LoginHistory.user_id == employee_pk)
        .order_by(LoginHistory.login_at.desc())
        .all()
    )
    return [
        {
            "company_email": user.company_email,
            "success": r.success,
            "failure_reason": r.failure_reason,
            "login_at": r.login_at,
            "ip_address": r.ip_address,
            "user_agent": r.user_agent,
        }
        for r in records
    ]
