"""Focused regression tests for the employee workspace security contract.
Run with pytest after installing backend/requirements.txt.
"""

import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("EMAIL_PROVIDER", "console")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.role import RoleEnum
from app.models.project import Project
from app.models.project_enums import ProjectRole, ProjectStatus, ProjectPriority, ProjectMethodology
from app.models.project_member import ProjectMember

engine=create_engine("sqlite:///:memory:",connect_args={"check_same_thread":False},poolclass=StaticPool)
SessionLocal=sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)
app.dependency_overrides[get_db]=lambda: (db for db in [SessionLocal()])
client=TestClient(app)

def seed(role):
 db=SessionLocal(); u=User(employee_id=f"E{role.value}",first_name="Test",last_name="User",personal_email=f"{role.value}@example.com",company_email=f"{role.value}@sprintnova.com",role=role,password_hash=hash_password("Pass123!"),must_change_password=False,is_active=True); db.add(u); db.commit(); db.refresh(u); db.close(); return u.id

def token(uid,role): return create_access_token(subject=str(uid),extra_claims={"role":role.value})

def test_client_cannot_read_internal_task_data():
 cid=seed(RoleEnum.CLIENT); aid=seed(RoleEnum.OWNER_ADMIN); db=SessionLocal(); p=Project(code="SN-SEC",name="Security",created_by_id=aid,status=ProjectStatus.ACTIVE,priority=ProjectPriority.MEDIUM,methodology=ProjectMethodology.SCRUM); db.add(p); db.commit(); db.add(ProjectMember(project_id=p.id,user_id=cid,project_role=ProjectRole.CLIENT_VIEWER)); db.commit(); db.close();
 r=client.get(f"/api/v1/projects/{p.id}/tasks",headers={"Authorization":f"Bearer {token(cid,RoleEnum.CLIENT)}"}); assert r.status_code==403

def test_duplicate_daily_update_is_rejected():
 uid=seed(RoleEnum.DEVELOPER); h={"Authorization":f"Bearer {token(uid,RoleEnum.DEVELOPER)}"};
 # no project required; first succeeds, second is 409
 body={"work_done":"Implemented API","completed_work":"Login","progress_percentage":50}
 assert client.post("/api/v1/daily-updates",json=body,headers=h).status_code==200
 assert client.post("/api/v1/daily-updates",json=body,headers=h).status_code==409
