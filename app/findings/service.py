from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.entities import Finding, Claim
from app.models.enums import Department, VerificationStatus, GeneratedBy, ClaimStrength
from app.findings.schemas import FindingCreate, ClaimCreate

async def create_finding(db: AsyncSession, case_id: str, finding_in: FindingCreate) -> Finding:
    finding = Finding(
        case_id=case_id,
        department=finding_in.department,
        finding_type=finding_in.finding_type,
        description=finding_in.description,
        observation_ids=finding_in.observation_ids,
        entity_ids=finding_in.entity_ids,
        time_start=finding_in.time_start,
        time_end=finding_in.time_end,
        detection_confidence=finding_in.detection_confidence,
        corroboration_count=finding_in.corroboration_count,
        corroboration_sources=finding_in.corroboration_sources,
        generated_by=finding_in.generated_by,
        verification_status=VerificationStatus.PENDING
    )
    db.add(finding)
    await db.commit()
    await db.refresh(finding)
    return finding

async def list_findings_for_case(
    db: AsyncSession,
    case_id: str,
    department: Optional[Department] = None
) -> List[Finding]:
    stmt = select(Finding).where(Finding.case_id == case_id).order_by(desc(Finding.created_at))
    if department:
        stmt = stmt.where(Finding.department == department)
    return list((await db.execute(stmt)).scalars().all())

async def create_claim(db: AsyncSession, case_id: str, claim_in: ClaimCreate) -> Claim:
    claim = Claim(
        case_id=case_id,
        claim_text=claim_in.claim_text,
        finding_ids=claim_in.finding_ids,
        claim_strength=claim_in.claim_strength,
        is_verified=False
    )
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    return claim

async def list_claims_for_case(db: AsyncSession, case_id: str) -> List[Claim]:
    stmt = select(Claim).where(Claim.case_id == case_id).order_by(desc(Claim.created_at))
    return list((await db.execute(stmt)).scalars().all())
