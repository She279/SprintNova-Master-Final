from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project_template import ProjectTemplate
from app.models.project import Project
from app.models.milestone import Milestone
from app.models.user import User
from app.schemas.project_template import ProjectTemplateCreateRequest, ApplyTemplateRequest
from app.services import project_service


def create_template(db: Session, payload: ProjectTemplateCreateRequest, created_by: User) -> ProjectTemplate:
    if db.query(ProjectTemplate).filter(ProjectTemplate.name == payload.name).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "A template with this name already exists")

    template = ProjectTemplate(
        name=payload.name,
        description=payload.description,
        default_milestones=[m.model_dump() for m in payload.default_milestones],
        default_project_roles=[r.value for r in payload.default_project_roles],
        created_by_id=created_by.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def list_templates(db: Session) -> list[ProjectTemplate]:
    return db.query(ProjectTemplate).order_by(ProjectTemplate.name).all()


def get_template_or_404(db: Session, template_id: int) -> ProjectTemplate:
    template = db.get(ProjectTemplate, template_id)
    if not template:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")
    return template


def apply_template(
    db: Session, template: ProjectTemplate, payload: ApplyTemplateRequest, created_by: User,
) -> Project:
    """Creates a new project and pre-populates its milestones from the
    template's `default_milestones`, resolving each `offset_days` against
    the project's start date."""
    start = date.fromisoformat(payload.start_date)

    from app.schemas.project import ProjectCreateRequest
    project = project_service.create_project(
        db,
        ProjectCreateRequest(
            code=payload.code, name=payload.name, description=payload.description,
            client_id=payload.client_id, product_owner_id=payload.product_owner_id,
            start_date=start,
        ),
        created_by=created_by,
    )

    for i, spec in enumerate(template.default_milestones):
        db.add(Milestone(
            project_id=project.id,
            title=spec["title"],
            phase=spec.get("phase"),
            due_date=start + timedelta(days=spec.get("offset_days", 0)),
            sort_order=i,
        ))
    db.commit()

    return project
