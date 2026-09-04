from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.models.entities import Observation, Evidence, CandidateEntityLink, Finding, Claim, User
from app.models.enums import Department, ObservationType, VerificationStatus
from app.observations.schemas import ObservationCreate

async def create_observation(
    db: AsyncSession,
    case_id: str,
    obs_in: ObservationCreate,
    processing_job_id: Optional[str] = None
) -> Observation:
    obs = Observation(
        case_id=case_id,
        evidence_id=obs_in.evidence_id,
        department=obs_in.department,
        observation_type=obs_in.observation_type,
        raw_data=obs_in.raw_data,
        observed_time_raw=obs_in.observed_time_raw,
        observed_time_parsed=obs_in.observed_time_parsed,
        time_confidence=obs_in.time_confidence,
        time_source=obs_in.time_source,
        time_reliability=obs_in.time_reliability,
        estimated_clock_offset=obs_in.estimated_clock_offset,
        time_window_min=obs_in.time_window_min,
        time_window_max=obs_in.time_window_max,
        location_label=obs_in.location_label,
        bounding_box=obs_in.bounding_box,
        frame_reference=obs_in.frame_reference,
        observation_confidence=obs_in.observation_confidence,
        evidence_quality=obs_in.evidence_quality,
        model_name=obs_in.model_name,
        model_version=obs_in.model_version,
        processing_job_id=processing_job_id,
        derived_from_observation_id=obs_in.derived_from_observation_id,
        verification_status=VerificationStatus.PENDING,
    )
    db.add(obs)
    await db.commit()
    await db.refresh(obs)
    return obs

async def get_observation_by_id(db: AsyncSession, observation_id: str) -> Optional[Observation]:
    stmt = select(Observation).where(Observation.id == observation_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_observations_for_case(
    db: AsyncSession,
    case_id: str,
    department: Optional[Department] = None,
    observation_type: Optional[ObservationType] = None,
    verification_status: Optional[VerificationStatus] = None,
    evidence_id: Optional[str] = None
) -> List[Observation]:
    stmt = select(Observation).where(Observation.case_id == case_id).order_by(desc(Observation.created_at))
    if department:
        stmt = stmt.where(Observation.department == department)
    if observation_type:
        stmt = stmt.where(Observation.observation_type == observation_type)
    if verification_status:
        stmt = stmt.where(Observation.verification_status == verification_status)
    if evidence_id:
        stmt = stmt.where(Observation.evidence_id == evidence_id)

    res = await db.execute(stmt)
    return list(res.scalars().all())

async def get_observation_provenance_chain(db: AsyncSession, observation_id: str) -> Dict[str, Any]:
    obs = await get_observation_by_id(db, observation_id)
    if not obs:
        return {}

    ev_stmt = select(Evidence).where(Evidence.id == obs.evidence_id)
    ev_res = await db.execute(ev_stmt)
    evidence = ev_res.scalar_one_or_none()

    links_stmt = select(CandidateEntityLink).where(CandidateEntityLink.observation_id == observation_id)
    links_res = await db.execute(links_stmt)
    links = links_res.scalars().all()

    chain = {
        "observation": {
            "id": obs.id,
            "type": obs.observation_type.value,
            "department": obs.department.value,
            "model_name": obs.model_name,
            "model_version": obs.model_version,
            "confidence": obs.observation_confidence,
            "verification_status": obs.verification_status.value,
            "time_raw": obs.observed_time_raw,
            "time_parsed": obs.observed_time_parsed.isoformat() if obs.observed_time_parsed else None,
        },
        "source_evidence": {
            "id": evidence.id,
            "filename": evidence.original_filename,
            "sha256_hash": evidence.sha256_hash,
            "type": evidence.evidence_type.value,
        } if evidence else None,
        "candidate_entity_links": [
            {
                "id": link.id,
                "candidate_entity_id": link.candidate_entity_id,
                "confidence": link.link_confidence,
                "is_human_confirmed": link.is_human_confirmed,
                "method": link.link_method
            }
            for link in links
        ]
    }
    return chain
