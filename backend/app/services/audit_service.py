"""
Audit logging service.

Records important system actions for compliance, debugging, and analysis.
"""
import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def audit_log(
    db: Session,
    *,
    user_id: int,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    changes: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """
    Record an audit log entry.
    
    Args:
        db: Database session
        user_id: User who performed the action
        action: What action was performed (e.g., "work_session_started")
        entity_type: Type of entity affected (e.g., "work_session")
        entity_id: ID of the entity affected
        changes: Dictionary of before/after values (serialized to JSON)
        ip_address: IP address of the request (optional)
        user_agent: User agent of the request (optional)
    
    Returns:
        The created AuditLog record
    """
    changes_str = None
    if changes:
        try:
            changes_str = json.dumps(changes)
        except (TypeError, ValueError):
            changes_str = str(changes)

    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=changes_str,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.utcnow(),
    )

    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return log_entry


def get_audit_logs(
    db: Session,
    *,
    user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    limit: int = 100,
    skip: int = 0,
) -> tuple[list[AuditLog], int]:
    """
    Retrieve audit logs with optional filtering.
    
    Returns:
        Tuple of (logs, total_count)
    """
    query = db.query(AuditLog)

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if action is not None:
        query = query.filter(AuditLog.action == action)
    if entity_type is not None:
        query = query.filter(AuditLog.entity_type == entity_type)

    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    return logs, total
