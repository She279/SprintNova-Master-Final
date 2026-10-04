from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_db
from app.models.user import User
from app.models.role import RoleEnum
from app.models.testing_enums import TestCaseStatus
from app.schemas.test_case import (
    TestCaseCreateRequest, TestCaseUpdateRequest, TestCaseResponse,
    TestExecutionCreateRequest, TestExecutionResponse,
)
from app.api.deps import require_password_already_set
from app.services import project_service, testcase_service

router = APIRouter(prefix="/projects/{project_id}/test-cases", tags=["Testing"])


def _require_test_manage(db, project, user):
    is_privileged = (
        project_service.is_tester_on_project(db, project, user)
        or project_service.is_product_owner_on_project(db, project, user)
        or project_service.is_scrum_master_on_project(db, project, user)
    )
    if not is_privileged:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only a Tester, Product Owner, Scrum Master, or Admin can manage test cases")


@router.post("", response_model=TestCaseResponse, status_code=201)
def create_test_case(project_id: int, payload: TestCaseCreateRequest, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    _require_test_manage(db, project, user)
    return testcase_service.create_test_case(db, project, payload, created_by=user)


@router.get("", response_model=list[TestCaseResponse])
def list_test_cases(
    project_id: int, status: TestCaseStatus | None = Query(None),
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    return testcase_service.list_test_cases(db, project_id, status_filter=status)


@router.patch("/{test_case_id}", response_model=TestCaseResponse)
def update_test_case(
    project_id: int, test_case_id: int, payload: TestCaseUpdateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    _require_test_manage(db, project, user)
    tc = testcase_service.get_test_case_or_404(db, project_id, test_case_id)
    return testcase_service.update_test_case(db, tc, payload)


@router.delete("/{test_case_id}", status_code=204)
def delete_test_case(project_id: int, test_case_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    _require_test_manage(db, project, user)
    tc = testcase_service.get_test_case_or_404(db, project_id, test_case_id)
    testcase_service.delete_test_case(db, tc)


@router.post("/{test_case_id}/executions", response_model=TestExecutionResponse, status_code=201)
def execute_test_case(
    project_id: int, test_case_id: int, payload: TestExecutionCreateRequest,
    db=Depends(get_db), user: User = Depends(require_password_already_set),
):
    project = project_service.get_project_or_404(db, project_id)
    _require_test_manage(db, project, user)
    tc = testcase_service.get_test_case_or_404(db, project_id, test_case_id)
    return testcase_service.execute_test_case(db, tc, payload, executed_by=user)


@router.get("/{test_case_id}/executions", response_model=list[TestExecutionResponse])
def list_executions(project_id: int, test_case_id: int, db=Depends(get_db), user: User = Depends(require_password_already_set)):
    project = project_service.get_project_or_404(db, project_id)
    project_service.require_view_access(db, project, user)
    if user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client accounts cannot access internal engineering data")
    testcase_service.get_test_case_or_404(db, project_id, test_case_id)
    return testcase_service.list_executions(db, test_case_id)
