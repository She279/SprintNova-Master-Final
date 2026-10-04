"""In-process realtime event hub for SprintNova.

The database remains the source of truth. WebSockets only deliver lightweight
invalidations/events so connected clients can refresh the affected API data
without polling every page.
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket


@dataclass(frozen=True)
class _Connection:
    websocket: WebSocket
    user_id: int
    role: str
    project_id: int | None
    allowed_project_ids: frozenset[int]


class RealtimeHub:
    def __init__(self) -> None:
        self._connections: set[_Connection] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, *, user_id: int, role: str, project_id: int | None = None, allowed_project_ids: set[int] | None = None) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(_Connection(websocket, user_id, role, project_id, frozenset(allowed_project_ids or set())))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections = {c for c in self._connections if c.websocket is not websocket}

    async def broadcast(self, event: dict[str, Any], *, user_ids: set[int] | None = None, project_id: int | None = None) -> None:
        async with self._lock:
            connections = list(self._connections)

        targets = []
        for connection in connections:
            if user_ids is not None:
                if connection.user_id not in user_ids:
                    continue
                # User-targeted events are safe on the user's personal stream.
                targets.append(connection)
                continue
            # Project events may reach a global workspace socket only when
            # the user is authorized for that project. A project socket is
            # still limited to its single project.
            if project_id is not None:
                if connection.project_id == project_id or (connection.project_id is None and project_id in connection.allowed_project_ids):
                    # Clients receive only project-progress events. Internal engineering/QA
                    # events must never cross the backend authorization boundary over WS.
                    if connection.role == "client":
                        event_type = str(event.get("type", ""))
                        safe = {"project.created", "project.updated", "sprint.created", "sprint.updated", "sprint.started", "sprint.completed", "milestone.updated"}
                        if event_type not in safe:
                            continue
                    targets.append(connection)
                continue
            if project_id is None and connection.project_id is None:
                targets.append(connection)

        if not targets:
            return

        results = await asyncio.gather(
            *(connection.websocket.send_json(event) for connection in targets),
            return_exceptions=True,
        )
        dead = [
            connection for connection, result in zip(targets, results)
            if isinstance(result, Exception)
        ]
        for connection in dead:
            await self.disconnect(connection.websocket)

    def publish_nowait(self, event: dict[str, Any], *, user_ids: set[int] | None = None, project_id: int | None = None) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        loop.create_task(self.broadcast(event, user_ids=user_ids, project_id=project_id))


hub = RealtimeHub()
