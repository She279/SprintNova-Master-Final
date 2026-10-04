"""Add employee workspace tables: work sessions, weekly availability, daily updates, analysis, and audit logs.

Revision ID: add_employee_workspace
Revises: a4e2c21583dc
Create Date: 2024-09-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_employee_workspace'
down_revision = 'a4e2c21583dc'
branch_labels = None
depends_on = None


def upgrade():
    # Create work_sessions table
    op.create_table('work_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('total_work_minutes', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_work_sessions_started_at'), 'work_sessions', ['started_at'], unique=False)
    op.create_index(op.f('ix_work_sessions_user_id'), 'work_sessions', ['user_id'], unique=False)

    # Create weekly_availability table
    op.create_table('weekly_availability',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('effective_from', sa.DateTime(), nullable=False),
        sa.Column('effective_to', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'day_of_week', name='uq_weekly_availability_user_day')
    )
    op.create_index(op.f('ix_weekly_availability_user_id'), 'weekly_availability', ['user_id'], unique=False)

    # Create daily_work_updates table
    op.create_table('daily_work_updates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('work_done', sa.Text(), nullable=True),
        sa.Column('completed_work', sa.Text(), nullable=True),
        sa.Column('pending_work', sa.Text(), nullable=True),
        sa.Column('blockers', sa.Text(), nullable=True),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_work_updates_date'), 'daily_work_updates', ['date'], unique=False)
    op.create_index(op.f('ix_daily_work_updates_project_id'), 'daily_work_updates', ['project_id'], unique=False)
    op.create_index(op.f('ix_daily_work_updates_user_id'), 'daily_work_updates', ['user_id'], unique=False)

    # Create daily_work_update_analysis table
    op.create_table('daily_work_update_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_update_id', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('completed_items', sa.Text(), nullable=True),
        sa.Column('pending_items', sa.Text(), nullable=True),
        sa.Column('detected_blockers', sa.Text(), nullable=True),
        sa.Column('risk_level', sa.String(length=50), nullable=False),
        sa.Column('risk_reason', sa.Text(), nullable=True),
        sa.Column('suggested_progress', sa.Integer(), nullable=True),
        sa.Column('suggested_actions', sa.Text(), nullable=True),
        sa.Column('task_suggestions', sa.Text(), nullable=True),
        sa.Column('ai_provider', sa.String(length=50), nullable=False),
        sa.Column('model_version', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['daily_update_id'], ['daily_work_updates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_work_update_analysis_daily_update_id'), 'daily_work_update_analysis', ['daily_update_id'], unique=False)

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('changes', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index(op.f('ix_daily_work_update_analysis_daily_update_id'), table_name='daily_work_update_analysis')
    op.drop_table('daily_work_update_analysis')
    
    op.drop_index(op.f('ix_daily_work_updates_user_id'), table_name='daily_work_updates')
    op.drop_index(op.f('ix_daily_work_updates_project_id'), table_name='daily_work_updates')
    op.drop_index(op.f('ix_daily_work_updates_date'), table_name='daily_work_updates')
    op.drop_table('daily_work_updates')
    
    op.drop_index(op.f('ix_weekly_availability_user_id'), table_name='weekly_availability')
    op.drop_table('weekly_availability')
    
    op.drop_index(op.f('ix_work_sessions_user_id'), table_name='work_sessions')
    op.drop_index(op.f('ix_work_sessions_started_at'), table_name='work_sessions')
    op.drop_table('work_sessions')
