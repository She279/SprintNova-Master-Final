"""Realtime infrastructure and active work-session uniqueness."""
from alembic import op
import sqlalchemy as sa

revision = "20260930_realtime_hardening"
down_revision = "20260929_workspace_hardening"
branch_labels = None
depends_on = None


def upgrade():
    # One active session per user is a business invariant. Both PostgreSQL and
    # modern SQLite support partial unique indexes, which lets completed rows
    # coexist while preventing duplicate active sessions at the DB boundary.
    op.create_index(
        "uq_work_sessions_one_active_per_user",
        "work_sessions",
        ["user_id"],
        unique=True,
        sqlite_where=sa.text("status = 'active' AND ended_at IS NULL"),
        postgresql_where=sa.text("status = 'active' AND ended_at IS NULL"),
    )


def downgrade():
    op.drop_index("uq_work_sessions_one_active_per_user", table_name="work_sessions")
