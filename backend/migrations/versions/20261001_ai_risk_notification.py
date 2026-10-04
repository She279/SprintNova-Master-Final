"""add AI risk notification type

Revision ID: 20261001_ai_risk_notification
Revises: 20260930_realtime_hardening
"""
from alembic import op
from sqlalchemy import text

revision = "20261001_ai_risk_notification"
down_revision = "20260930_realtime_hardening"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(text("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'AI_RISK_DETECTED'"))


def downgrade():
    # PostgreSQL enum values cannot be safely removed in-place. The application
    # can continue to read older rows; downgrade intentionally performs no DDL.
    pass
