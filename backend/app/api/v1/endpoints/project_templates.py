from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.project_template import (
    ProjectTemplateCreateRequest, ProjectTemplateResponse, ApplyTemplateRequest,
)
from app.schemas.project import ProjectResponse
from app.api.deps import require_role
from app.services import project_template_service

router = APIRouter(prefix="/project-templates", tags=["Project Templates"])

_MANAGE = require_role(RoleEnum.OWNER_ADMIN, RoleEnum.PRODUCT_OWNER)


@router.post("", response_model=ProjectTemplateResponse, status_code=201)
def create_template(payload: ProjectTemplateCreateRequest, db=Depends(get_db), user: User = Depends(_MANAGE)):
    return project_template_service.create_template(db, payload, created_by=user)


@router.get("", response_model=list[ProjectTemplateResponse])
def list_templates(db=Depends(get_db), _user: User = Depends(_MANAGE)):
    return project_template_service.list_templates(db)


@router.get("/{template_id}", response_model=ProjectTemplateResponse)
def get_template(template_id: int, db=Depends(get_db), _user: User = Depends(_MANAGE)):
    return project_template_service.get_template_or_404(db, template_id)


@router.post("/{template_id}/apply", response_model=ProjectResponse, status_code=201)
def apply_template(
    template_id: int, payload: ApplyTemplateRequest, db=Depends(get_db), user: User = Depends(_MANAGE),
):
    template = project_template_service.get_template_or_404(db, template_id)
    return project_template_service.apply_template(db, template, payload, created_by=user)
