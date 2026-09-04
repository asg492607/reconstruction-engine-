import pytest
from httpx import AsyncClient
from sqlalchemy import select
from tests.helpers import get_auth_headers
from app.models.entities import AuditLog
from app.database import get_db

@pytest.mark.asyncio
async def test_audit_log_generation(client: AsyncClient, seed_users, db_session):
    lead = seed_users["lead"]
    headers = get_auth_headers(lead)

    # 1. Create a case
    case_res = await client.post(
        "/cases",
        json={"title": "Audited Theft Case", "case_type": "THEFT"},
        headers=headers
    )
    case_id = case_res.json()["id"]

    # 2. Query audit_log table directly in DB
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.case_id == case_id)
    )
    logs = result.scalars().all()
    actions = [log.action for log in logs]

    assert "CASE_CREATED" in actions
