from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.services.realtime_service import hub

router = APIRouter(tags=["Realtime"])


def _authenticate(token: str | None, db: Session) -> User | None:
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    try:
        user = db.get(User, int(payload["sub"]))
    except (TypeError, ValueError):
        return None
    return user if user and user.is_active else None


@router.websocket("/realtime/ws")
async def realtime_socket(websocket: WebSocket, token: str | None = None, project_id: int | None = None):
    """Authenticated realtime stream.

    Clients may subscribe to their personal stream or a project stream. Project
    subscriptions are allowed only when the user can see that project.
    """
    db = SessionLocal()
    try:
        user = _authenticate(token, db)
        if not user:
            await websocket.close(code=1008)
            return

        if project_id is not None and user.role.value != "owner_admin":
            member = (
                db.query(ProjectMember)
                .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user.id)
                .first()
            )
            if not member:
                await websocket.close(code=1008)
                return
        elif project_id is not None and not db.get(Project, project_id):
            await websocket.close(code=1008)
            return

        allowed_project_ids = set()
        if project_id is None:
            if user.role.value == "owner_admin":
                allowed_project_ids = {p.id for p in db.query(Project.id).all()}
            else:
                allowed_project_ids = {row.project_id for row in db.query(ProjectMember.project_id).filter(ProjectMember.user_id == user.id).all()}
        await hub.connect(
            websocket, user_id=user.id, role=user.role.value, project_id=project_id,
            allowed_project_ids=allowed_project_ids,
        )
        await websocket.send_json({"type": "connection.ready", "message": "SprintNova realtime connected"})
        while True:
            # Client messages are optional keep-alives; server events are pushed automatically.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await hub.disconnect(websocket)
        db.close()
