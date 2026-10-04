from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.test_case import TestCase
from app.models.test_execution import TestExecution
from app.models.testing_enums import TestCaseStatus, ExecutionResult
from app.schemas.test_case import TestCaseCreateRequest, TestCaseUpdateRequest, TestExecutionCreateRequest
from app.services.realtime_service import hub


def _next_key(db: Session, project: Project) -> str:
    count = db.query(TestCase).filter(TestCase.project_id == project.id).count()
    return f"{project.code}-TC{count + 1}"


def create_test_case(db: Session, project: Project, payload: TestCaseCreateRequest, created_by) -> TestCase:
    tc = TestCase(project_id=project.id, key=_next_key(db, project), created_by_id=created_by.id, **payload.model_dump())
    db.add(tc)
    db.commit()
    db.refresh(tc)
    hub.publish_nowait({"type": "test_case.created", "project_id": project.id, "test_case_id": tc.id, "key": tc.key, "status": tc.status.value}, project_id=project.id)
    return tc


def list_test_cases(db: Session, project_id: int, status_filter: TestCaseStatus | None = None) -> list[TestCase]:
    query = db.query(TestCase).filter(TestCase.project_id == project_id)
    if status_filter:
        query = query.filter(TestCase.status == status_filter)
    return query.order_by(TestCase.created_at).all()


def get_test_case_or_404(db: Session, project_id: int, test_case_id: int) -> TestCase:
    tc = db.query(TestCase).filter(TestCase.id == test_case_id, TestCase.project_id == project_id).first()
    if not tc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test case not found")
    return tc


def update_test_case(db: Session, tc: TestCase, payload: TestCaseUpdateRequest) -> TestCase:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tc, field, value)
    db.commit()
    db.refresh(tc)
    hub.publish_nowait({"type": "test_case.updated", "project_id": tc.project_id, "test_case_id": tc.id, "status": tc.status.value}, project_id=tc.project_id)
    return tc


def delete_test_case(db: Session, tc: TestCase) -> None:
    db.query(TestExecution).filter(TestExecution.test_case_id == tc.id).delete()
    db.delete(tc)
    db.commit()


_RESULT_TO_STATUS = {
    ExecutionResult.PASS: TestCaseStatus.PASSED,
    ExecutionResult.FAIL: TestCaseStatus.FAILED,
    ExecutionResult.BLOCKED: TestCaseStatus.BLOCKED,
}


def execute_test_case(db: Session, tc: TestCase, payload: TestExecutionCreateRequest, executed_by) -> TestExecution:
    execution = TestExecution(test_case_id=tc.id, executed_by_id=executed_by.id, **payload.model_dump())
    db.add(execution)

    # The test case's own status always reflects its most recent run.
    tc.status = _RESULT_TO_STATUS[payload.result]

    db.commit()
    db.refresh(execution)
    hub.publish_nowait({"type": "test_case.executed", "project_id": tc.project_id, "test_case_id": tc.id, "status": tc.status.value}, project_id=tc.project_id)
    return execution


def list_executions(db: Session, test_case_id: int) -> list[TestExecution]:
    return (
        db.query(TestExecution)
        .filter(TestExecution.test_case_id == test_case_id)
        .order_by(TestExecution.executed_at.desc())
        .all()
    )
