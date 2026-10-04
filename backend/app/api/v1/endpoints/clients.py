from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.client import ClientCreateRequest, ClientUpdateRequest, ClientResponse
from app.api.deps import require_role
from app.services import client_service

router = APIRouter(prefix="/clients", tags=["Clients"])

_MANAGE_CLIENTS = require_role(RoleEnum.OWNER_ADMIN, RoleEnum.PRODUCT_OWNER)


@router.post("", response_model=ClientResponse, status_code=201)
def create_client(payload: ClientCreateRequest, db=Depends(get_db), _user: User = Depends(_MANAGE_CLIENTS)):
    return client_service.create_client(db, payload)


@router.get("", response_model=list[ClientResponse])
def list_clients(db=Depends(get_db), _user: User = Depends(_MANAGE_CLIENTS)):
    return client_service.list_clients(db)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, db=Depends(get_db), _user: User = Depends(_MANAGE_CLIENTS)):
    return client_service.get_client_or_404(db, client_id)


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, payload: ClientUpdateRequest, db=Depends(get_db), _user: User = Depends(_MANAGE_CLIENTS)):
    return client_service.update_client(db, client_id, payload)
