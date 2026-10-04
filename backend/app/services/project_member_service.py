from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.project import AddProjectMemberRequest, ProjectMemberBrief
from app.services import notification_service


def list_members(db: Session, project_id: int) -> list[ProjectMemberBrief]:
    rows = (
        db.query(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .filter(ProjectMember.project_id == project_id)
        .all()
    )
    return [
        ProjectMemberBrief(
            id=pm.id, user_id=pm.user_id, project_role=pm.project_role,
            full_name=f"{u.first_name} {u.last_name}", company_email=u.company_email,
        )
        for pm, u in rows
    ]


def add_member(db: Session, project: Project, payload: AddProjectMemberRequest) -> ProjectMember:
    user = db.get(User, payload.user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found or inactive")

    member = ProjectMember(project_id=project.id, user_id=payload.user_id, project_role=payload.project_role)
    db.add(member)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "This employee is already on the project team")
    db.refresh(member)

    notification_service.notify(
        db, user=user, type=NotificationType.TEAM_MEMBER_ADDED,
        title=f"You've been added to {project.name}",
        body=f"You've joined the team for {project.code} — {project.name} as {payload.project_role.value.replace('_', ' ')}.",
        related_project_id=project.id,
    )

    return member


def remove_member(db: Session, project_id: int, member_id: int) -> None:
    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.id == member_id, ProjectMember.project_id == project_id)
        .first()
    )
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Team member not found on this project")

    user = db.get(User, member.user_id)
    project = db.get(Project, project_id)
    db.delete(member)
    db.commit()

    if user and project:
        notification_service.notify(
            db, user=user, type=NotificationType.TEAM_MEMBER_REMOVED,
            title=f"You've been removed from {project.name}",
            body=f"You're no longer on the team for {project.code} — {project.name}.",
            related_project_id=project.id,
        )
