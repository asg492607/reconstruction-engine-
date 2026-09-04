from datetime import datetime, timezone
from typing import Optional, Any, Dict
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import AuditLog, User

async def record_audit_log(
    db: AsyncSession,
    action: str,
    case_id: Optional[str] = None,
    user: Optional[User] = None,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None,
    organization: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    session_id: Optional[str] = None,
) -> AuditLog:
    """
    Creates an immutable audit log record.
    """
    resolved_user_id = user.id if user else user_id
    resolved_user_role = (user.role.value if hasattr(user.role, "value") else str(user.role)) if user else user_role
    resolved_org = organization or (getattr(user, "organization_id", None) if user else None)

    log_entry = AuditLog(
        case_id=case_id,
        user_id=resolved_user_id,
        user_role=resolved_user_role,
        organization=resolved_org,
        action=action,
        target_type=target_type,
        target_id=target_id,
        before_state=before_state,
        after_state=after_state,
        ip_address=ip_address,
        session_id=session_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    return log_entry
