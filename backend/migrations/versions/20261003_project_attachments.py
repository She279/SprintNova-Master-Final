from alembic import op
import sqlalchemy as sa

revision = "20261003_project_attachments"
down_revision = "20261001_ai_risk_notification"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "project_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("content_type", sa.String(length=150), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_project_attachments_project_id", "project_attachments", ["project_id"])

def downgrade():
    op.drop_index("ix_project_attachments_project_id", table_name="project_attachments")
    op.drop_table("project_attachments")
