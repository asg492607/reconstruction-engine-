from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import Observation, Finding, Claim, CandidateEntityLink, Verification, User
from app.models.enums import VerificationStatus, TargetType, VerificationAction

async def get_pending_verifications_for_case(db: AsyncSession, case_id: str) -> Dict[str, Any]:
    obs_res = await db.execute(
        select(Observation).where(
            Observation.case_id == case_id,
            Observation.verification_status == VerificationStatus.PENDING
        )
    )
    pending_obs = obs_res.scalars().all()

    find_res = await db.execute(
        select(Finding).where(
            Finding.case_id == case_id,
            Finding.verification_status == VerificationStatus.PENDING
        )
    )
    pending_findings = find_res.scalars().all()

    link_res = await db.execute(
        select(CandidateEntityLink).where(
            CandidateEntityLink.case_id == case_id,
            CandidateEntityLink.is_human_confirmed == False
        )
    )
    pending_links = link_res.scalars().all()

    return {
        "pending_observations": [
            {
                "id": o.id,
                "type": o.observation_type.value,
                "department": o.department.value,
                "confidence": o.observation_confidence,
                "raw_data": o.raw_data
            }
            for o in pending_obs
        ],
        "pending_findings": [
            {"id": f.id, "type": f.finding_type, "description": f.description}
            for f in pending_findings
        ],
        "pending_entity_links": [
            {
                "id": l.id,
                "candidate_entity_id": l.candidate_entity_id,
                "observation_id": l.observation_id,
                "confidence": l.link_confidence
            }
            for l in pending_links
        ]
    }

async def verify_observation(
    db: AsyncSession,
    case_id: str,
    obs_id: str,
    action: VerificationAction,
    user: User,
    note: Optional[str] = None,
    corrected_data: Optional[Dict[str, Any]] = None
) -> Verification:
    obs_res = await db.execute(select(Observation).where(Observation.id == obs_id))
    obs = obs_res.scalar_one_or_none()
    if not obs or obs.case_id != case_id:
        raise ValueError("Observation not found")

    # Update observation status
    if action == VerificationAction.ACCEPTED:
        obs.verification_status = VerificationStatus.ACCEPTED
    elif action == VerificationAction.CORRECTED:
        obs.verification_status = VerificationStatus.CORRECTED
        if corrected_data:
            obs.raw_data.update(corrected_data)
    else:
        obs.verification_status = VerificationStatus.REJECTED

    obs.verified_by = user.id
    obs.verified_at = datetime.now(timezone.utc)

    ver = Verification(
        case_id=case_id,
        target_type=TargetType.OBSERVATION,
        target_id=obs.id,
        action=action,
        note=note,
        corrected_data=corrected_data,
        verified_by=user.id,
        verified_at=datetime.now(timezone.utc)
    )
    db.add(ver)
    await db.commit()
    await db.refresh(ver)
    return ver

async def verify_finding(
    db: AsyncSession,
    case_id: str,
    finding_id: str,
    action: VerificationAction,
    user: User,
    note: Optional[str] = None
) -> Verification:
    stmt = select(Finding).where(Finding.id == finding_id)
    finding = (await db.execute(stmt)).scalar_one_or_none()
    if not finding or finding.case_id != case_id:
        raise ValueError("Finding not found")

    if action == VerificationAction.ACCEPTED:
        finding.verification_status = VerificationStatus.ACCEPTED
    elif action == VerificationAction.CORRECTED:
        finding.verification_status = VerificationStatus.CORRECTED
    else:
        finding.verification_status = VerificationStatus.REJECTED

    finding.verified_by = user.id
    finding.verified_at = datetime.now(timezone.utc)
    if note:
        finding.correction_note = note

    ver = Verification(
        case_id=case_id,
        target_type=TargetType.FINDING,
        target_id=finding.id,
        action=action,
        note=note,
        verified_by=user.id,
        verified_at=datetime.now(timezone.utc)
    )
    db.add(ver)
    await db.commit()
    await db.refresh(ver)
    return ver
