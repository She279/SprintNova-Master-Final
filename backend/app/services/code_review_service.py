from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.code_review import CodeReview
from app.schemas.code_review import CodeReviewCreateRequest, CodeReviewUpdateRequest


def create_review(db: Session, project_id: int, payload: CodeReviewCreateRequest, author) -> CodeReview:
    review = CodeReview(project_id=project_id, author_id=author.id, **payload.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def list_reviews(db: Session, project_id: int) -> list[CodeReview]:
    return db.query(CodeReview).filter(CodeReview.project_id == project_id).order_by(CodeReview.created_at.desc()).all()


def get_review_or_404(db: Session, project_id: int, review_id: int) -> CodeReview:
    review = db.query(CodeReview).filter(CodeReview.id == review_id, CodeReview.project_id == project_id).first()
    if not review:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Code review not found")
    return review


def update_review(db: Session, review: CodeReview, payload: CodeReviewUpdateRequest) -> CodeReview:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(review, field, value)
    db.commit()
    db.refresh(review)
    return review
