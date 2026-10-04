from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.task import Task
from app.models.task_comment import TaskComment
from app.models.task_history import TaskHistory
from app.models.task_enums import TaskStatus
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.task import TaskCreateRequest, TaskUpdateRequest, TaskCommentCreateRequest
from app.services import notification_service
from app.services.realtime_service import hub

_TRACKED_FIELDS = {"status", "assignee_id", "priority"}


def _validate_project_links(db: Session, project: Project, *, assignee_id: int | None, sprint_id: int | None, user_story_id: int | None) -> None:
    from app.models.project_member import ProjectMember
    from app.models.sprint import Sprint
    from app.models.user_story import UserStory
    if assignee_id is not None and not db.query(ProjectMember).filter(ProjectMember.project_id == project.id, ProjectMember.user_id == assignee_id).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Task assignee must be a member of this project")
    if sprint_id is not None and not db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project.id).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sprint does not belong to this project")
    if user_story_id is not None and not db.query(UserStory).filter(UserStory.id == user_story_id, UserStory.project_id == project.id).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User story does not belong to this project")


def _next_key(db: Session, project: Project) -> str:
    count = db.query(Task).filter(Task.project_id == project.id).count()
    return f"{project.code}-T{count + 1}"


def create_task(db: Session, project: Project, payload: TaskCreateRequest, reporter: User) -> Task:
    _validate_project_links(db, project, assignee_id=payload.assignee_id, sprint_id=payload.sprint_id, user_story_id=payload.user_story_id)
    task = Task(project_id=project.id, key=_next_key(db, project), reporter_id=reporter.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)

    if task.assignee_id:
        _notify_assignment(db, task, project)
    hub.publish_nowait({
        "type": "task.created",
        "project_id": project.id,
        "task": {"id": task.id, "key": task.key, "title": task.title, "status": task.status.value, "assignee_id": task.assignee_id},
    }, project_id=project.id)
    return task


def list_tasks(
    db: Session, project_id: int, status_filter: TaskStatus | None = None,
    sprint_id: int | None = None, assignee_id: int | None = None,
) -> list[Task]:
    query = db.query(Task).filter(Task.project_id == project_id)
    if status_filter:
        query = query.filter(Task.status == status_filter)
    if sprint_id is not None:
        query = query.filter(Task.sprint_id == sprint_id)
    if assignee_id is not None:
        query = query.filter(Task.assignee_id == assignee_id)
    return query.order_by(Task.created_at).all()


def get_task_or_404(db: Session, project_id: int, task_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


def _stringify(value):
    if value is None:
        return None
    if hasattr(value, "value"):  # enum member -> its string value, not the repr
        return str(value.value)
    return str(value)


def update_task(db: Session, task: Task, payload: TaskUpdateRequest, changed_by: User) -> Task:
    changes = payload.model_dump(exclude_unset=True)
    _validate_project_links(db, db.get(Project, task.project_id), assignee_id=changes.get("assignee_id", task.assignee_id), sprint_id=changes.get("sprint_id", task.sprint_id), user_story_id=changes.get("user_story_id", task.user_story_id))

    for field, new_value in changes.items():
        old_value = getattr(task, field)
        if field in _TRACKED_FIELDS and old_value != new_value:
            db.add(TaskHistory(
                task_id=task.id, user_id=changed_by.id, field_changed=field,
                old_value=_stringify(old_value), new_value=_stringify(new_value),
            ))
        setattr(task, field, new_value)

    db.commit()
    db.refresh(task)

    project = db.get(Project, task.project_id)

    if "assignee_id" in changes and task.assignee_id:
        _notify_assignment(db, task, project)

    if "status" in changes and task.assignee_id:
        assignee = db.get(User, task.assignee_id)
        if assignee and assignee.id != changed_by.id:
            notification_service.notify(
                db, user=assignee, type=NotificationType.TASK_STATUS_CHANGED,
                title=f"{task.key} moved to {task.status.value.replace('_', ' ')}",
                body=f"\"{task.title}\" in {project.code if project else ''} is now {task.status.value.replace('_', ' ')}.",
                related_project_id=task.project_id, also_email=False,
            )

    hub.publish_nowait({
        "type": "task.updated",
        "project_id": task.project_id,
        "task": {"id": task.id, "key": task.key, "title": task.title, "status": task.status.value, "assignee_id": task.assignee_id},
        "changed_by": changed_by.id,
        "changes": list(changes.keys()),
    }, project_id=task.project_id)
    return task


def _notify_assignment(db: Session, task: Task, project: Project) -> None:
    assignee = db.get(User, task.assignee_id)
    if assignee:
        notification_service.notify(
            db, user=assignee, type=NotificationType.TASK_ASSIGNED,
            title=f"You've been assigned {task.key}",
            body=f"\"{task.title}\" in {project.code} — {project.name} is now assigned to you.",
            related_project_id=project.id,
        )


def delete_task(db: Session, task: Task) -> None:
    db.query(TaskComment).filter(TaskComment.task_id == task.id).delete()
    db.query(TaskHistory).filter(TaskHistory.task_id == task.id).delete()
    project_id = task.project_id
    task_id = task.id
    db.delete(task)
    db.commit()
    hub.publish_nowait({"type": "task.deleted", "project_id": project_id, "task_id": task_id}, project_id=project_id)


def add_comment(db: Session, task: Task, payload: TaskCommentCreateRequest, author: User) -> TaskComment:
    comment = TaskComment(task_id=task.id, author_id=author.id, body=payload.body)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    if task.assignee_id and task.assignee_id != author.id:
        project = db.get(Project, task.project_id)
        assignee = db.get(User, task.assignee_id)
        if assignee:
            notification_service.notify(
                db, user=assignee, type=NotificationType.TASK_COMMENT_ADDED,
                title=f"New comment on {task.key}",
                body=f"{author.first_name} {author.last_name} commented on \"{task.title}\".",
                related_project_id=task.project_id, also_email=False,
            )

    hub.publish_nowait({
        "type": "task.comment.created", "project_id": task.project_id, "task_id": task.id,
        "comment_id": comment.id, "author_id": author.id,
    }, project_id=task.project_id)
    return comment


def list_comments(db: Session, task_id: int) -> list[TaskComment]:
    return db.query(TaskComment).filter(TaskComment.task_id == task_id).order_by(TaskComment.created_at).all()


def list_history(db: Session, task_id: int) -> list[TaskHistory]:
    return db.query(TaskHistory).filter(TaskHistory.task_id == task_id).order_by(TaskHistory.created_at.desc()).all()
