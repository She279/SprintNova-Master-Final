from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.models.role import RoleEnum
from app.models.leave import LeaveStatus
from app.models.user import User
from app.schemas.leave import LeaveRequestCreateRequest, LeaveDecisionRequest, LeaveRequestResponse, LeaveRequestWithEmployee
from app.api.deps import require_password_already_set, require_role
from app.services import leave_service

router = APIRouter(prefix="/leave-requests", tags=["Leave & Permission"])

_REVIEW = require_role(RoleEnum.OWNER_ADMIN, RoleEnum.SCRUM_MASTER)


@router.post("", response_model=LeaveRequestResponse, status_code=201)
def create_request(
    payload: LeaveRequestCreateRequest, db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    return leave_service.create_request(db, user, payload)


@router.get("/me", response_model=list[LeaveRequestResponse])
def my_requests(db=Depends(get_db), user: User = Depends(require_password_already_set)):
    return leave_service.list_own(db, user.id)


@router.get("", response_model=list[LeaveRequestWithEmployee])
def all_requests(status: LeaveStatus | None = Query(None), db=Depends(get_db), _user: User = Depends(_REVIEW)):
    requests = leave_service.list_all(db, status)
    result = []
    for r in requests:
        employee = db.get(User, r.user_id)
        result.append(LeaveRequestWithEmployee(
            **LeaveRequestResponse.model_validate(r).model_dump(),
            full_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
            company_email=employee.company_email if employee else "",
        ))
    return result


@router.patch("/{request_id}/decide", response_model=LeaveRequestResponse)
def decide_request(
    request_id: int, payload: LeaveDecisionRequest, db=Depends(get_db), user: User = Depends(_REVIEW),
):
    request = leave_service.get_or_404(db, request_id)
    return leave_service.decide(db, request, user, payload)
