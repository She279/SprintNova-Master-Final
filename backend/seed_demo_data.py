"""
Seeds SprintNova with a realistic, fully-populated demo organisation so the
app looks and behaves like a real workspace immediately after setup.

Creates the "E-Commerce Web Application" scenario from the spec: a real
team across the core demo roles, a client, two projects, epics, a prioritised
backlog, one completed sprint and one active sprint, Kanban tasks spread
across all four columns, test cases with executions, bugs at various
lifecycle stages, code reviews, builds, milestones, availability, leave
requests, and project documents indexed for the AI assistant.

Everything goes through the real service layer where one exists, so the
seeded data is indistinguishable from data created through the UI --
including generated company emails, hashed passwords, notification
fan-out, and ChromaDB indexing.

Usage:
    python seed_demo_data.py          # refuses to run if data already exists
    python seed_demo_data.py --force  # wipes and reseeds

Demo credentials are printed at the end.
"""
import argparse
import sys
from datetime import date, datetime, timedelta

from app.core.database import SessionLocal
from app.core.security import hash_password
from app import models  # noqa: F401 -- registers all models

from app.models.role import RoleEnum
from app.models.user import User
from app.models.client import Client
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_enums import (
    ProjectStatus, ProjectPriority, ProjectMethodology, ProjectRole, MilestoneStatus,
)
from app.models.milestone import Milestone
from app.models.epic import Epic
from app.models.user_story import UserStory
from app.models.sprint import Sprint
from app.models.scrum_enums import StoryPriority, StoryStatus, SprintStatus
from app.models.task import Task
from app.models.task_enums import TaskStatus, TaskPriority
from app.models.task_comment import TaskComment
from app.models.test_case import TestCase
from app.models.test_execution import TestExecution
from app.models.testing_enums import (
    TestCaseStatus, TestPriority, ExecutionResult,
    BugSeverity, BugPriority, BugStatus, CodeReviewStatus, BuildStatus,
)
from app.models.bug import Bug
from app.models.bug_comment import BugComment
from app.models.code_review import CodeReview
from app.models.build import Build
from app.models.availability import Availability, AvailabilityStatus
from app.models.leave import LeaveRequest, LeaveType, LeaveStatus
from app.models.project_document import ProjectDocument, DocumentType

from app.utils.email_generator import generate_company_email
from app.services import rag_service

DEMO_PASSWORD = "SprintNova1!"

TEAM = [
    ("SprintNova", "Admin", "SN001", RoleEnum.OWNER_ADMIN, "Leadership", "24suca27@tcarts.in"),
    ("Dharsini", "M", "SN002", RoleEnum.PRODUCT_OWNER, "Product", "dharsini1229@gmail.com"),
    ("Rajilakshimi", "Team", "SN003", RoleEnum.SCRUM_MASTER, "Delivery", "rajilakshimi75@gmail.com"),
    ("Developer", "45", "SN004", RoleEnum.DEVELOPER, "Engineering", "24suca45@tcarts.in"),
    ("Tester", "38", "SN005", RoleEnum.TESTER, "Quality", "24suca38@tcarts.in"),
]


def _wipe(db):
    """Deletes in FK-safe order."""
    from app.models.daily_work_update import DailyWorkUpdate
    from app.models.daily_work_update_analysis import DailyWorkUpdateAnalysis
    from app.models.work_session import WorkSession
    from app.models.weekly_availability import WeeklyAvailability
    from app.models.project_attachment import ProjectAttachment
    from app.models.audit_log import AuditLog
    from app.models.task_history import TaskHistory
    from app.models.bug_history import BugHistory
    for model in (
        AuditLog, DailyWorkUpdateAnalysis, DailyWorkUpdate, WorkSession, WeeklyAvailability, ProjectAttachment,
        TaskHistory, BugHistory,
        BugComment, Bug, TestExecution, TestCase, CodeReview, Build,
        TaskComment, Task, UserStory, Sprint, Epic, Milestone,
        ProjectDocument, ProjectMember, Project, Client,
        Availability, LeaveRequest,
    ):
        db.query(model).delete()
    # Keep it simple: also clear derived/auth tables that reference users.
    from app.models.notification import Notification
    from app.models.login_history import LoginHistory
    from app.models.otp import OTP
    from app.models.project_template import ProjectTemplate
    for model in (Notification, LoginHistory, OTP, ProjectTemplate):
        db.query(model).delete()
    db.query(User).delete()
    db.commit()


def seed(force: bool = False) -> None:
    # Schema is owned by Alembic. Run `alembic upgrade head` before seeding.
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            if not force:
                print("Database already contains users. Re-run with --force to wipe and reseed.")
                sys.exit(1)
            print("Wiping existing data...")
            _wipe(db)

        today = date.today()
        now = datetime.utcnow()

        # --- People -------------------------------------------------
        users = {}
        for first, last, emp_id, role, dept, personal in TEAM:
            u = User(
                employee_id=emp_id, first_name=first, last_name=last,
                personal_email=personal,
                company_email=generate_company_email(db, first, last),
                role=role, department=dept,
                password_hash=hash_password(DEMO_PASSWORD),
                must_change_password=False, is_active=True,
                joining_date=today - timedelta(days=400),
            )
            db.add(u)
            db.flush()
            users[emp_id] = u
        db.commit()

        admin = users["SN001"]
        po = users["SN002"]
        sm = users["SN003"]
        dev = users["SN004"]
        tester = users["SN005"]
        # Reuse the single developer/tester in several demo records so the
        # requested five-person team can still demonstrate a complete flow.
        devs = [dev, dev, dev]
        testers = [tester, tester]
        client_user = None

        # --- Client -------------------------------------------------
        client = Client(
            name="Rohan Mehta", company_name="Northwind Retail",
            contact_email="rohan@northwindretail.example", contact_phone="+91 98765 43210",
        )
        db.add(client)
        db.flush()

        # --- Projects -----------------------------------------------
        ecom = Project(
            code="ECOM", name="E-Commerce Web Application",
            description="Customer-facing storefront with catalogue, cart, checkout and order tracking.",
            status=ProjectStatus.ACTIVE, priority=ProjectPriority.HIGH,
            methodology=ProjectMethodology.SCRUM, client_id=client.id,
            product_owner_id=po.id, created_by_id=admin.id,
            start_date=today - timedelta(days=60), end_date=today + timedelta(days=120),
        )
        db.add(ecom)
        db.flush()

        roster = [
            (ecom, po, ProjectRole.PRODUCT_OWNER),
            (ecom, sm, ProjectRole.SCRUM_MASTER),
            (ecom, dev, ProjectRole.TEAM_LEAD),
            (ecom, tester, ProjectRole.TESTER),
            (ecom, admin, ProjectRole.PROJECT_MANAGER),
        ]
        for project, user, prole in roster:
            db.add(ProjectMember(project_id=project.id, user_id=user.id, project_role=prole))
        db.flush()

        # --- Milestones / roadmap -----------------------------------
        milestones = [
            ("Discovery complete", "Discovery", -45, MilestoneStatus.COMPLETED, 0),
            ("Design sign-off", "Design", -20, MilestoneStatus.COMPLETED, 1),
            ("Catalogue & cart live", "Build", 20, MilestoneStatus.IN_PROGRESS, 2),
            ("Checkout & payments live", "Build", 60, MilestoneStatus.PENDING, 3),
            ("Public launch", "Delivery", 115, MilestoneStatus.PENDING, 4),
        ]
        for title, phase, offset, status, order in milestones:
            db.add(Milestone(
                project_id=ecom.id, title=title, phase=phase, sort_order=order,
                due_date=today + timedelta(days=offset), status=status,
            ))
        db.flush()

        # --- Epics + backlog ----------------------------------------
        epics = {}
        for name, desc in [
            ("Catalogue", "Browsing, search and product detail pages."),
            ("Cart & Checkout", "Cart management, payment and order confirmation."),
            ("Accounts", "Registration, login and order history."),
        ]:
            e = Epic(project_id=ecom.id, title=name, description=desc)
            db.add(e)
            db.flush()
            epics[name] = e

        # (title, epic, priority, points, status, sprint_slot)
        # sprint_slot: 0 = completed sprint, 1 = active sprint, None = backlog
        stories = [
            ("As a shopper, I want to browse products by category, so that I can find items quickly",
             "Catalogue", StoryPriority.HIGH, 8, StoryStatus.DONE, 0),
            ("As a shopper, I want to search products by keyword, so that I can find a specific item",
             "Catalogue", StoryPriority.HIGH, 5, StoryStatus.DONE, 0),
            ("As a shopper, I want to view product details and photos, so that I can decide what to buy",
             "Catalogue", StoryPriority.MEDIUM, 5, StoryStatus.DONE, 0),
            ("As a shopper, I want to add items to a cart, so that I can buy several things at once",
             "Cart & Checkout", StoryPriority.CRITICAL, 8, StoryStatus.IN_PROGRESS, 1),
            ("As a shopper, I want to check out and pay by card, so that I can complete my order",
             "Cart & Checkout", StoryPriority.CRITICAL, 13, StoryStatus.IN_SPRINT, 1),
            ("As a shopper, I want an order confirmation email, so that I know my order went through",
             "Cart & Checkout", StoryPriority.HIGH, 3, StoryStatus.IN_SPRINT, 1),
            ("As a shopper, I want to save my delivery address, so that checkout is faster next time",
             "Accounts", StoryPriority.MEDIUM, 5, StoryStatus.BACKLOG, None),
            ("As a shopper, I want to view my past orders, so that I can track deliveries",
             "Accounts", StoryPriority.MEDIUM, 8, StoryStatus.BACKLOG, None),
            ("As a shopper, I want to apply a discount code, so that I can use promotions",
             "Cart & Checkout", StoryPriority.LOW, 5, StoryStatus.BACKLOG, None),
            ("As a shopper, I want product reviews, so that I can judge quality before buying",
             "Catalogue", StoryPriority.LOW, None, StoryStatus.BACKLOG, None),
        ]

        # --- Sprints ------------------------------------------------
        sprint1 = Sprint(
            project_id=ecom.id, name="Sprint 1 — Catalogue foundations",
            goal="Shoppers can browse and search the full product catalogue.",
            start_date=today - timedelta(days=28), end_date=today - timedelta(days=14),
            status=SprintStatus.COMPLETED, created_by_id=sm.id,
        )
        sprint2 = Sprint(
            project_id=ecom.id, name="Sprint 2 — Cart & checkout",
            goal="A shopper can add items to a cart and complete a card payment.",
            start_date=today - timedelta(days=7), end_date=today + timedelta(days=7),
            status=SprintStatus.ACTIVE, created_by_id=sm.id,
        )
        db.add_all([sprint1, sprint2])
        db.flush()
        sprint_by_slot = {0: sprint1, 1: sprint2}

        story_objs = []
        for rank, (title, epic_name, prio, points, status, slot) in enumerate(stories):
            s = UserStory(
                project_id=ecom.id, key=f"ECOM-{rank + 1}",
                epic_id=epics[epic_name].id,
                sprint_id=sprint_by_slot[slot].id if slot is not None else None,
                title=title,
                acceptance_criteria="Given a shopper on the storefront, when they perform the action, then the expected result occurs.",
                priority=prio, story_points=points, status=status, backlog_rank=rank,
                assignee_id=devs[rank % 3].id if slot is not None else None,
                reporter_id=po.id,
            )
            # Completed-sprint stories were finished during that sprint.
            if slot == 0:
                s.updated_at = now - timedelta(days=16 + rank)
            db.add(s)
            db.flush()
            story_objs.append(s)

        # --- Kanban tasks -------------------------------------------
        tasks = [
            ("Build cart state management", TaskStatus.DONE, TaskPriority.HIGH, devs[0], 3, 8, 7.5, -3),
            ("Cart totals & tax calculation", TaskStatus.IN_PROGRESS, TaskPriority.CRITICAL, devs[1], 3, 12, 14.0, 2),
            ("Payment gateway integration", TaskStatus.IN_PROGRESS, TaskPriority.CRITICAL, devs[2], 4, 16, 9.0, 5),
            ("Checkout form validation", TaskStatus.TESTING, TaskPriority.HIGH, devs[0], 4, 6, 6.0, 1),
            ("Order confirmation email template", TaskStatus.TODO, TaskPriority.MEDIUM, devs[1], 5, 4, None, 6),
            ("Handle expired card errors", TaskStatus.TODO, TaskPriority.HIGH, devs[2], 4, 5, None, -1),
            ("Cart empty-state design polish", TaskStatus.DONE, TaskPriority.LOW, devs[0], 3, 2, 1.5, -5),
        ]
        task_objs = []
        for i, (title, status, prio, assignee, story_idx, est, act, due_offset) in enumerate(tasks):
            t = Task(
                project_id=ecom.id, key=f"ECOM-T{i + 1}", sprint_id=sprint2.id,
                user_story_id=story_objs[story_idx].id, title=title,
                priority=prio, status=status,
                due_date=today + timedelta(days=due_offset),
                estimated_hours=est, actual_hours=act,
                assignee_id=assignee.id, reporter_id=sm.id,
            )
            db.add(t)
            db.flush()
            task_objs.append(t)

        db.add(TaskComment(
            task_id=task_objs[2].id, author_id=devs[2].id,
            body="Gateway sandbox keys are in the shared vault. Blocked on their 3DS callback docs.",
        ))
        db.add(TaskComment(
            task_id=task_objs[1].id, author_id=sm.id,
            body="This has gone over estimate — let's split the tax rules into a follow-up task.",
        ))

        # --- Test cases + executions --------------------------------
        test_specs = [
            ("Browse catalogue by category", TestPriority.HIGH, ExecutionResult.PASS, 0),
            ("Search returns relevant products", TestPriority.HIGH, ExecutionResult.PASS, 1),
            ("Add item to cart updates totals", TestPriority.CRITICAL, ExecutionResult.PASS, 3),
            ("Checkout with valid card succeeds", TestPriority.CRITICAL, ExecutionResult.FAIL, 4),
            ("Checkout with expired card shows error", TestPriority.HIGH, ExecutionResult.FAIL, 4),
            ("Order confirmation email is sent", TestPriority.MEDIUM, None, 5),
        ]
        tc_objs = []
        for i, (title, prio, result, story_idx) in enumerate(test_specs):
            tc = TestCase(
                project_id=ecom.id, key=f"ECOM-TC{i + 1}",
                user_story_id=story_objs[story_idx].id, title=title,
                steps="1. Open the storefront\n2. Perform the action under test\n3. Observe the result",
                expected_result="The action completes and the UI reflects the new state.",
                priority=prio,
                status=(
                    TestCaseStatus.PASSED if result == ExecutionResult.PASS
                    else TestCaseStatus.FAILED if result == ExecutionResult.FAIL
                    else TestCaseStatus.READY
                ),
                tester_id=testers[i % 2].id, created_by_id=testers[i % 2].id,
            )
            db.add(tc)
            db.flush()
            tc_objs.append(tc)
            if result is not None:
                db.add(TestExecution(
                    test_case_id=tc.id, executed_by_id=testers[i % 2].id, result=result,
                    actual_result=("As expected." if result == ExecutionResult.PASS
                                   else "Payment call returned HTTP 500 from the gateway sandbox."),
                    executed_at=now - timedelta(days=2, hours=i),
                ))

        # --- Bugs ---------------------------------------------------
        bug_specs = [
            ("Checkout returns 500 when paying by card", BugSeverity.CRITICAL, BugPriority.CRITICAL,
             BugStatus.IN_PROGRESS, devs[2], 3, None),
            ("Expired card error message is blank", BugSeverity.MAJOR, BugPriority.HIGH,
             BugStatus.ASSIGNED, devs[2], 4, None),
            ("Cart badge count lags by one item", BugSeverity.MINOR, BugPriority.MEDIUM,
             BugStatus.FIXED, devs[1], None, None),
            ("Product image alt text missing on listing", BugSeverity.TRIVIAL, BugPriority.LOW,
             BugStatus.VERIFIED, devs[0], None, 6),
            ("Search ignores trailing whitespace", BugSeverity.MINOR, BugPriority.LOW,
             BugStatus.CLOSED, devs[0], 1, 9),
        ]
        bug_objs = []
        for i, (title, sev, prio, status, assignee, tc_idx, resolved_days_ago) in enumerate(bug_specs):
            b = Bug(
                project_id=ecom.id, key=f"ECOM-BUG{i + 1}", title=title,
                test_case_id=tc_objs[tc_idx].id if tc_idx is not None else None,
                steps_to_reproduce="1. Go to the affected screen\n2. Reproduce the described action",
                expected_result="The action succeeds cleanly.",
                actual_result="The described defect occurs.",
                environment="Staging / Chrome 120",
                severity=sev, priority=prio, status=status,
                reporter_id=testers[i % 2].id, assignee_id=assignee.id,
                resolved_at=(now - timedelta(days=resolved_days_ago)) if resolved_days_ago else None,
                created_at=now - timedelta(days=12 - i),
            )
            db.add(b)
            db.flush()
            bug_objs.append(b)

        db.add(BugComment(
            bug_id=bug_objs[0].id, author_id=devs[2].id,
            body="Reproduced locally. The gateway rejects our idempotency key format — fix in progress.",
        ))
        db.add(BugComment(
            bug_id=bug_objs[0].id, author_id=testers[0].id,
            body="Blocking the Sprint 2 goal, flagging to the Scrum Master.",
        ))

        # --- Code reviews + builds ----------------------------------
        db.add_all([
            CodeReview(project_id=ecom.id, title="Cart state management", status=CodeReviewStatus.APPROVED,
                       author_id=devs[0].id, reviewer_id=devs[1].id),
            CodeReview(project_id=ecom.id, title="Payment gateway client", status=CodeReviewStatus.CHANGES_REQUESTED,
                       author_id=devs[2].id, reviewer_id=sm.id),
            CodeReview(project_id=ecom.id, title="Checkout form validation", status=CodeReviewStatus.PENDING,
                       author_id=devs[0].id, reviewer_id=devs[2].id),
        ])
        for i, (label, status, mins_ago) in enumerate([
            ("build-142", BuildStatus.SUCCESSFUL, 2880),
            ("build-143", BuildStatus.FAILED, 1440),
            ("build-144", BuildStatus.SUCCESSFUL, 300),
            ("build-145", BuildStatus.RUNNING, 5),
        ]):
            db.add(Build(
                project_id=ecom.id, label=label, status=status, triggered_by_id=devs[i % 3].id,
                log_summary=("Test suite failed: 2 checkout tests red." if status == BuildStatus.FAILED else None),
                created_at=now - timedelta(minutes=mins_ago),
                finished_at=(now - timedelta(minutes=mins_ago - 4)) if status != BuildStatus.RUNNING else None,
            ))

        # --- Availability + leave -----------------------------------
        for offset in range(0, 10):
            d = today + timedelta(days=offset)
            if d.weekday() >= 5:
                continue
            for dev in [dev]:
                db.add(Availability(
                    user_id=dev.id, date=d, status=AvailabilityStatus.AVAILABLE, hours_available=8,
                ))
        db.add(LeaveRequest(
            user_id=dev.id, type=LeaveType.LEAVE,
            start_date=today + timedelta(days=12), end_date=today + timedelta(days=14),
            reason="Family function", status=LeaveStatus.PENDING,
        ))
        db.add(LeaveRequest(
            user_id=testers[0].id, type=LeaveType.PERMISSION,
            start_date=today + timedelta(days=3), end_date=today + timedelta(days=3),
            start_time="14:00", end_time="16:00", reason="Medical appointment",
            status=LeaveStatus.APPROVED, reviewed_by_id=sm.id, reviewed_at=now,
            review_note="Approved — please hand over the regression run.",
        ))

        # --- Weekly availability + daily updates + work sessions ----
        from app.models.weekly_availability import WeeklyAvailability, DayOfWeek
        from app.models.daily_work_update import DailyWorkUpdate
        from app.models.work_session import WorkSession, WorkSessionStatus
        from app.services.daily_work_update_analysis_service import analyze_daily_update
        from datetime import time as dt_time

        for u in [admin, po, sm, dev, tester]:
            for day in [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, DayOfWeek.THURSDAY, DayOfWeek.FRIDAY]:
                db.add(WeeklyAvailability(
                    user_id=u.id, day_of_week=day, start_time=dt_time(9, 0), end_time=dt_time(17, 0),
                    timezone="Asia/Kolkata", effective_from=now,
                ))
        db.flush()

        for u in [admin, po, sm, tester]:
            for offset in range(0, 15):
                d = today + timedelta(days=offset)
                if d.weekday() < 5:
                    db.merge(Availability(user_id=u.id, date=d, status=AvailabilityStatus.AVAILABLE, hours_available=8))

        demo_updates = [
            (dev, today, "Implemented cart totals and checkout validation.", "Checkout form validation", "Payment gateway integration", "Payment gateway sandbox intermittently returns HTTP 500.", 68),
            (po, today - timedelta(days=1), "Refined checkout acceptance criteria and prioritized the backlog.", "Checkout acceptance criteria", "Refund edge cases", "", 72),
            (sm, today - timedelta(days=1), "Reviewed sprint board, blockers and team capacity.", "Sprint risk review", "Dependency follow-up", "", 64),
            (tester, today - timedelta(days=1), "Executed checkout regression tests and raised the payment defect.", "Checkout regression", "3DS retest", "Payment gateway sandbox failure", 58),
        ]
        first_update = None
        for u, d, work, completed, pending, blockers, progress_value in demo_updates:
            item = DailyWorkUpdate(
                user_id=u.id, project_id=ecom.id, date=d, work_done=work,
                completed_work=completed, pending_work=pending, blockers=blockers,
                additional_notes="Seeded realistic demo update.", progress_percentage=progress_value,
                submitted_at=now - timedelta(hours=2),
            )
            db.add(item)
            db.flush()
            db.commit()
            analyze_daily_update(db, user_id=u.id, daily_update=item)
            if first_update is None:
                first_update = item

        db.add(WorkSession(
            user_id=dev.id, started_at=now - timedelta(hours=2, minutes=15),
            ended_at=now - timedelta(minutes=15), total_work_minutes=120, status=WorkSessionStatus.COMPLETED,
        ))
        db.commit()

        # --- Project documents (indexed for the AI assistant) -------
        docs = [
            ("Checkout requirements", DocumentType.REQUIREMENT,
             "The checkout flow must validate the shipping address before allowing payment. "
             "Card payments go through the Northwind gateway with 3D Secure enabled. "
             "International orders require a customs declaration form."),
            ("Payment refund policy", DocumentType.REQUIREMENT,
             "Refunds must be supported within 30 days of purchase. Partial refunds are required "
             "for split shipments. Refunds are issued to the original payment method only."),
            ("Sprint 1 retrospective", DocumentType.SPRINT_NOTE,
             "Catalogue work landed on time. The team agreed to move shared validation logic into a "
             "common library so both web and mobile checkout can reuse it. Search relevance tuning "
             "was deferred to a later sprint."),
            ("Testing guidelines", DocumentType.TESTING_DOC,
             "Every user story needs at least one critical-path test case before it can be marked Done. "
             "Failed executions must have a bug raised and linked to the test case."),
            ("Definition of Done", DocumentType.GUIDELINE,
             "A story is Done when: code is reviewed and approved, all linked test cases pass, "
             "no open critical or major bugs remain, and the build is green."),
        ]
        for title, dtype, content in docs:
            doc = ProjectDocument(
                project_id=ecom.id, title=title, doc_type=dtype, content=content, created_by_id=po.id,
            )
            db.add(doc)
            db.flush()
            rag_service.index_document(doc)

        # One real downloadable project attachment for the demo Files tab.
        from pathlib import Path
        from app.models.project_attachment import ProjectAttachment
        upload_root = Path(__file__).resolve().parent / "uploads" / "projects"
        upload_root.mkdir(parents=True, exist_ok=True)
        demo_name = "sprintnova_demo_requirements.txt"
        (upload_root / demo_name).write_text(
            "SprintNova Demo Requirements\n\nCheckout must validate shipping details before payment.\n",
            encoding="utf-8",
        )
        db.add(ProjectAttachment(
            project_id=ecom.id, uploaded_by_id=po.id, original_name=demo_name,
            stored_name=demo_name, content_type="text/plain",
            size_bytes=(upload_root / demo_name).stat().st_size,
        ))

        db.commit()

        # --- Summary ------------------------------------------------
        print("\nSprintNova demo data seeded.\n")
        print(f"{'Role':<16}{'Login (company email)':<38}Password")
        print("-" * 78)
        for _, _, emp_id, role, _, _ in TEAM:
            u = users[emp_id]
            print(f"{role.value:<16}{u.company_email:<38}{DEMO_PASSWORD}")
        print(
            "\nProject: ECOM (active, complete Scrum + Kanban + QA + AI demo data)\n"
            "Try: log in as the Scrum Master to see the burndown, or as the Product Owner to plan the backlog.\n"
            "Ask the ECOM project's Assistant tab about refunds.\n"
        )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed SprintNova with demo data.")
    parser.add_argument("--force", action="store_true", help="wipe existing data before seeding")
    seed(force=parser.parse_args().force)
