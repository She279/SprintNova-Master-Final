from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_enums import ProjectRole
from app.models.role import RoleEnum
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.project import ProjectCreateRequest, ProjectUpdateRequest
from app.services import notification_service
from app.services.realtime_service import hub


def create_project(db: Session, payload: ProjectCreateRequest, created_by: User) -> Project:
    if db.query(Project).filter(Project.code == payload.code).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Project code already exists")

    project = Project(**payload.model_dump(), created_by_id=created_by.id)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Product Owner is automatically added to the team roster.
    if project.product_owner_id:
        db.add(ProjectMember(
            project_id=project.id, user_id=project.product_owner_id, project_role=ProjectRole.PRODUCT_OWNER,
        ))
        db.commit()

        po = db.get(User, project.product_owner_id)
        if po:
            notification_service.notify(
                db, user=po, type=NotificationType.PROJECT_CREATED,
                title=f"You're the Product Owner for {project.name}",
                body=f"Project {project.code} — {project.name} has been created and you've been assigned as Product Owner.",
                related_project_id=project.id,
            )

    hub.publish_nowait({"type": "project.created", "project_id": project.id, "code": project.code, "name": project.name}, project_id=project.id)
    return project


def get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


def _membership(db: Session, project_id: int, user_id: int) -> ProjectMember | None:
    return (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )


def can_view_project(db: Session, project: Project, user: User) -> bool:
    if user.role == RoleEnum.OWNER_ADMIN:
        return True
    return _membership(db, project.id, user.id) is not None


def can_manage_project(db: Session, project: Project, user: User) -> bool:
    if user.role == RoleEnum.OWNER_ADMIN:
        return True
    membership = _membership(db, project.id, user.id)
    return membership is not None and membership.project_role in (
        ProjectRole.PRODUCT_OWNER, ProjectRole.SCRUM_MASTER,
        ProjectRole.PROJECT_MANAGER, ProjectRole.TEAM_LEAD,
    )


def require_view_access(db: Session, project: Project, user: User) -> None:
    if not can_view_project(db, project, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not on this project's team")


def require_manage_access(db: Session, project: Project, user: User) -> None:
    if not can_manage_project(db, project, user):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only an authorized project manager, product owner, scrum master, team lead, or admin can manage this project",
        )


def is_product_owner_on_project(db: Session, project: Project, user: User) -> bool:
    if user.role == RoleEnum.OWNER_ADMIN:
        return True
    membership = _membership(db, project.id, user.id)
    return membership is not None and membership.project_role == ProjectRole.PRODUCT_OWNER


def is_scrum_master_on_project(db: Session, project: Project, user: User) -> bool:
    if user.role == RoleEnum.OWNER_ADMIN:
        return True
    membership = _membership(db, project.id, user.id)
    return membership is not None and membership.project_role == ProjectRole.SCRUM_MASTER


def is_tester_on_project(db: Session, project: Project, user: User) -> bool:
    if user.role == RoleEnum.OWNER_ADMIN:
        return True
    membership = _membership(db, project.id, user.id)
    return membership is not None and membership.project_role == ProjectRole.TESTER


def require_backlog_manage_access(db: Session, project: Project, user: User) -> None:
    """Backlog refinement (create/edit stories, prioritize, epics) is the
    Product Owner's job, per Module 3's spec."""
    if not is_product_owner_on_project(db, project, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the Product Owner or an Admin can manage the backlog")


def require_sprint_manage_access(db: Session, project: Project, user: User) -> None:
    """Sprint lifecycle (create/start/close/cancel) is the Scrum Master's job."""
    if not is_scrum_master_on_project(db, project, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the Scrum Master or an Admin can manage sprints")


def list_visible_projects(db: Session, user: User) -> list[Project]:
    if user.role == RoleEnum.OWNER_ADMIN:
        return db.query(Project).order_by(Project.created_at.desc()).all()

    member_project_ids = [
        m.project_id for m in db.query(ProjectMember).filter(ProjectMember.user_id == user.id).all()
    ]
    if not member_project_ids:
        return []
    return (
        db.query(Project)
        .filter(Project.id.in_(member_project_ids))
        .order_by(Project.created_at.desc())
        .all()
    )


def update_project(db: Session, project: Project, payload: ProjectUpdateRequest) -> Project:
    changes = payload.model_dump(exclude_unset=True)
    status_changed = "status" in changes and changes["status"] != project.status

    for field, value in changes.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)

    if status_changed:
        hub.publish_nowait({"type": "project.updated", "project_id": project.id, "code": project.code, "status": project.status.value}, project_id=project.id)
        members = db.query(ProjectMember).filter(ProjectMember.project_id == project.id).all()
        recipients = [db.get(User, m.user_id) for m in members]
        notification_service.notify_many(
            db, users=[u for u in recipients if u],
            type=NotificationType.PROJECT_STATUS_CHANGED,
            title=f"{project.name} is now {project.status.value.replace('_', ' ')}",
            body=f"Project {project.code} status changed to {project.status.value.replace('_', ' ')}.",
            related_project_id=project.id,
        )

    return project
