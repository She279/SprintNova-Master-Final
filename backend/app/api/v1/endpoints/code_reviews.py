from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.models.user import User
from app.models.role import RoleEnum
from app.schemas.code_review import CodeReviewCreateRequest, CodeReviewUpdateRequest, CodeReviewResponse
from app.api.deps import require_password_already_set
from app.services import project_service, code_review_service

router = APIRouter(prefix="/projects/{project_id}/code-reviews", tags=["XP Quality"])


@router.post("", response_model=CodeReviewResponse, status_code=201)
def create_review(project_id: int, payload: CodeReviewCreateRequest, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    return code_review_service.create_review(db, project_id, payload, author=user)


@router.get("", response_model=list[CodeReviewResponse])
def list_reviews(project_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    return code_review_service.list_reviews(db, project_id)


@router.patch("/{review_id}", response_model=CodeReviewResponse)
def update_review(
    project_id: int, review_id: int, payload: CodeReviewUpdateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    review = code_review_service.get_review_or_404(db, project_id, review_id)
    return code_review_service.update_review(db, review, payload)
