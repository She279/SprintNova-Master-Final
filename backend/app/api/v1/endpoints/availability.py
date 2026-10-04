from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.availability import (
    AvailabilitySetRequest,
    AvailabilityResponse,
    TeamAvailabilityDay,
    WeeklyAvailabilitySetupRequest,
)
from app.schemas.availability import AvailabilitySetRequest, AvailabilityResponse, TeamAvailabilityDay
from app.api.deps import require_password_already_set, require_role
from app.services import availability_service

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.put("/me", response_model=AvailabilityResponse)
def set_my_availability(
    payload: AvailabilitySetRequest, db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    return availability_service.set_availability(db, user.id, payload)


@router.get("/me", response_model=list[AvailabilityResponse])
def my_availability(
    start: date = Query(...), end: date = Query(...),
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    return availability_service.list_own_availability(db, user.id, start, end)


@router.get("/team", response_model=list[TeamAvailabilityDay])
def team_availability(
    start: date = Query(...), end: date = Query(...), user_ids: str = Query(..., description="Comma-separated user IDs"),
    db=Depends(get_db), _user: User = Depends(require_role(RoleEnum.OWNER_ADMIN, RoleEnum.PRODUCT_OWNER, RoleEnum.SCRUM_MASTER, RoleEnum.PROJECT_MANAGER, RoleEnum.TEAM_LEAD)),
):
    ids = [int(x) for x in user_ids.split(",") if x.strip()]
    return availability_service.team_availability(db, ids, start, end)
