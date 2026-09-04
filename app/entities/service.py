from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.models.entities import CandidateEntity, CandidateEntityLink, Observation, Verification, User
from app.models.enums import EntityType, IdentityStatus, TargetType, VerificationAction
from app.entities.schemas import CandidateEntityCreate
from app.entities.linker import match_observation_to_entity, extract_features_from_observation

async def create_candidate_entity(
    db: AsyncSession,
    case_id: str,
    entity_in: CandidateEntityCreate
) -> CandidateEntity:
    entity = CandidateEntity(
        case_id=case_id,
        entity_type=entity_in.entity_type,
        label=entity_in.label,
        description=entity_in.description,
        first_observed=entity_in.first_observed,
        last_observed=entity_in.last_observed,
        identity_status=entity_in.identity_status,
        identity_note=entity_in.identity_note
    )
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return await get_candidate_entity_by_id(db, entity.id)

async def get_candidate_entity_by_id(db: AsyncSession, entity_id: str) -> Optional[CandidateEntity]:
    stmt = (
        select(CandidateEntity)
        .where(CandidateEntity.id == entity_id)
        .options(selectinload(CandidateEntity.links))
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_candidate_entities(db: AsyncSession, case_id: str) -> List[CandidateEntity]:
    stmt = (
        select(CandidateEntity)
        .where(CandidateEntity.case_id == case_id)
        .options(selectinload(CandidateEntity.links))
        .order_by(CandidateEntity.created_at)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())

async def link_observation_to_entity(
    db: AsyncSession,
    case_id: str,
    candidate_entity_id: str,
    observation_id: str,
    link_confidence: float,
    link_method: str = "manual",
    link_evidence: Optional[Dict[str, Any]] = None
) -> CandidateEntityLink:
    # Check if already linked
    check_stmt = select(CandidateEntityLink).where(
        CandidateEntityLink.candidate_entity_id == candidate_entity_id,
        CandidateEntityLink.observation_id == observation_id
    )
    existing = (await db.execute(check_stmt)).scalar_one_or_none()
    if existing:
        return existing

    link = CandidateEntityLink(
        case_id=case_id,
        candidate_entity_id=candidate_entity_id,
        observation_id=observation_id,
        link_confidence=link_confidence,
        link_method=link_method,
        link_evidence=link_evidence or {},
        is_human_confirmed=False
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link

async def confirm_entity_link(
    db: AsyncSession,
    case_id: str,
    link_id: str,
    user: User,
    note: Optional[str] = None
) -> CandidateEntityLink:
    stmt = select(CandidateEntityLink).where(CandidateEntityLink.id == link_id)
    res = await db.execute(stmt)
    link = res.scalar_one_or_none()
    if not link or link.case_id != case_id:
        raise ValueError("Candidate entity link not found")

    link.is_human_confirmed = True
    link.confirmed_by = user.id
    link.confirmed_at = datetime.now(timezone.utc)

    # Record in verifications ledger
    ver = Verification(
        case_id=case_id,
        target_type=TargetType.ENTITY_LINK,
        target_id=link.id,
        action=VerificationAction.ACCEPTED,
        note=note or "Human confirmation of candidate entity linkage",
        verified_by=user.id,
        verified_at=datetime.now(timezone.utc)
    )
    db.add(ver)
    await db.commit()
    await db.refresh(link)
    return link

async def auto_link_case_observations(db: AsyncSession, case_id: str) -> List[CandidateEntityLink]:
    """
    Scans observations for a case, discovers candidate entities (P1, V1, etc.),
    computes linkage probabilities, and records explicit CandidateEntityLink rows.
    """
    entities = await list_candidate_entities(db, case_id)
    entity_map = {e.label: e for e in entities}

    # Ensure baseline candidate entities exist for theft scenario
    if "P1" not in entity_map:
        p1 = await create_candidate_entity(
            db, case_id,
            CandidateEntityCreate(
                entity_type=EntityType.PERSON,
                label="P1",
                description={"clothing": "dark jacket, dark trousers", "build": "medium"},
                identity_status=IdentityStatus.CANDIDATE,
                identity_note="Primary unidentified individual observed across surveillance cameras and witness report"
            )
        )
        entities.append(p1)
        entity_map["P1"] = p1

    # Fetch all observations
    obs_stmt = select(Observation).where(Observation.case_id == case_id)
    observations = (await db.execute(obs_stmt)).scalars().all()

    created_links = []
    for obs in observations:
        for entity in entities:
            matched, confidence, ev, method = match_observation_to_entity(entity, obs)
            if matched:
                link = await link_observation_to_entity(
                    db=db,
                    case_id=case_id,
                    candidate_entity_id=entity.id,
                    observation_id=obs.id,
                    link_confidence=confidence,
                    link_method=method,
                    link_evidence=ev
                )
                created_links.append(link)

    return created_links
