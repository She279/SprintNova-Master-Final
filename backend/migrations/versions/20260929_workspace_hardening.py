"""Harden employee workspace: roles, project roles, update uniqueness, availability history."""
from alembic import op
import sqlalchemy as sa

revision = "20260929_workspace_hardening"
down_revision = "add_employee_workspace"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE roleenum ADD VALUE IF NOT EXISTS 'PROJECT_MANAGER'")
        op.execute("ALTER TYPE roleenum ADD VALUE IF NOT EXISTS 'TEAM_LEAD'")
        op.execute("ALTER TYPE projectrole ADD VALUE IF NOT EXISTS 'PROJECT_MANAGER'")
        op.execute("ALTER TYPE projectrole ADD VALUE IF NOT EXISTS 'TEAM_LEAD'")
        op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'DAILY_UPDATE_PENDING'")
        op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'AVAILABILITY_REQUIRED'")
    else:
        # SQLite stores these enums as VARCHAR and requires no schema change.
        pass
    try:
        op.drop_constraint("uq_weekly_availability_user_day", "weekly_availability", type_="unique")
    except Exception:
        pass
    try:
        op.create_unique_constraint("uq_daily_work_update_user_date", "daily_work_updates", ["user_id", "date"])
    except Exception:
        pass

def downgrade():
    try:
        op.drop_constraint("uq_daily_work_update_user_date", "daily_work_updates", type_="unique")
    except Exception:
        pass
