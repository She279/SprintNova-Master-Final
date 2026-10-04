from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models.user import User
from app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse
from app.api.deps import require_password_already_set
from app.services import project_service, assistant_service

router = APIRouter(prefix="/projects/{project_id}/assistant", tags=["AI Assistant"])


@router.post("/ask", response_model=AssistantQueryResponse)
def ask(
    project_id: int, payload: AssistantQueryRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    return assistant_service.answer_question(db, project, payload.question, client_safe=user.role.value == "client")
