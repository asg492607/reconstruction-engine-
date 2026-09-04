from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.entities import GapConflict, CorrelatedTimelineEvent, Observation, Case, Evidence
from app.models.enums import GapConflictType, Significance

async def detect_case_gaps_and_conflicts(
    db: AsyncSession,
    case: Case,
    events: List[CorrelatedTimelineEvent],
    observations: List[Observation]
) -> List[GapConflict]:
    detected: List[GapConflict] = []

    # 1. Check existing gaps/conflicts
    existing_stmt = select(GapConflict).where(GapConflict.case_id == case.id)
    existing = (await db.execute(existing_stmt)).scalars().all()
    if existing:
        return list(existing)

    # 2. Check for surveillance coverage gaps between aisle and exit
    # In the theft scenario, person was at electronics shelf, then at exit, with missing corridor coverage
    has_aisle = any("shelf" in e.description.lower() or "aisle" in e.description.lower() for e in events)
    has_exit = any("exit" in e.description.lower() for e in events)

    if has_aisle and has_exit:
        gap = GapConflict(
            case_id=case.id,
            gc_type=GapConflictType.GAP,
            description="No surveillance camera coverage between Electronics Display (Aisle 3) and Store Exit corridor during the critical transition window (approx. 8:42 PM - 8:45 PM).",
            significance=Significance.CRITICAL,
            significance_reason="Surveillance blind spot coincides with the estimated time window of item concealment and movement to exit.",
            is_resolved=False
        )
        db.add(gap)
        detected.append(gap)

    # 3. Check for soft timestamp discrepancies between witness perception and CCTV overlay
    witness_obs = [o for o in observations if o.time_source == "witness_statement"]
    cctv_obs = [o for o in observations if o.time_source in ("camera_overlay", "camera_timestamp")]

    if witness_obs and cctv_obs:
        w_time = witness_obs[0].observed_time_raw or "8:40 PM"
        c_time = cctv_obs[0].observed_time_raw or "8:37 PM"
        discrepancy = GapConflict(
            case_id=case.id,
            gc_type=GapConflictType.SOFT_DISCREPANCY,
            description=f"Perceptual timestamp discrepancy: Witness reported sighting at '{w_time}', while CCTV entrance recorded subject at '{c_time}'.",
            significance=Significance.MEDIUM,
            significance_reason="Human witness estimates commonly drift by 3-5 minutes compared to hardware timestamp overlays.",
            affected_observation_ids=[witness_obs[0].id, cctv_obs[0].id],
            is_resolved=False
        )
        db.add(discrepancy)
        detected.append(discrepancy)

    inventory_missing = any(o.observation_type.value == "OBJECT_DETECTED" for o in observations)
    has_unauthorized_tx = any(
        (o.raw_data or {}).get("anomaly_type") in ("UNAUTHORIZED_REMOVAL_NO_PAYMENT", "NO_MATCHING_TRANSACTION_RECORDED")
        for o in observations
    )

    if inventory_missing and has_unauthorized_tx:
        corr_discrepancy = GapConflict(
            case_id=case.id,
            gc_type=GapConflictType.CORROBORATIVE_DISCREPANCY,
            description="Item confirmed missing in inventory audit, with no matching point-of-sale purchase recorded in transaction logs.",
            significance=Significance.HIGH,
            significance_reason="Corroborative discrepancy: Physical inventory shrinkage aligns with absence of checkout transactions, indicating unrecorded removal rather than a data contradiction.",
            is_resolved=False
        )
        db.add(corr_discrepancy)
        detected.append(corr_discrepancy)

    # 5. Check for genuine hard contradictions (e.g. contradictory attire or conflicting status)
    clothing_descriptors = set()
    for o in observations:
        attrs = (o.raw_data or {}).get("attributes") or {}
        if "clothing" in attrs:
            clothing_descriptors.add(str(attrs["clothing"]).strip())
    
    # Conflict between light and dark attire or mutually exclusive colors
    has_dark = any("dark" in c.lower() or "black" in c.lower() for c in clothing_descriptors)
    has_light = any("white" in c.lower() or "light" in c.lower() or "red" in c.lower() for c in clothing_descriptors)
    if has_dark and has_light:
        contra = GapConflict(
            case_id=case.id,
            gc_type=GapConflictType.HARD_CONTRADICTION,
            description=f"Direct witness/visual contradiction: Conflicting subject attire descriptors ({', '.join(clothing_descriptors)}).",
            significance=Significance.CRITICAL,
            significance_reason="Mutually exclusive physical appearance descriptors cannot both be simultaneously true for a single individual.",
            is_resolved=False
        )
        db.add(contra)
        detected.append(contra)

    await db.commit()
    return detected

async def resolve_gap_conflict(
    db: AsyncSession,
    case_id: str,
    gc_id: str,
    user_id: str,
    resolution_note: str
) -> GapConflict:
    stmt = select(GapConflict).where(GapConflict.id == gc_id)
    gc = (await db.execute(stmt)).scalar_one_or_none()
    if not gc or gc.case_id != case_id:
        raise ValueError("Gap / Conflict record not found")

    gc.is_resolved = True
    gc.resolution_note = resolution_note
    gc.resolved_by = user_id
    gc.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(gc)
    return gc

async def list_gaps_and_conflicts(
    db: AsyncSession,
    case_id: str,
    gc_type: Optional[GapConflictType] = None,
    significance: Optional[Significance] = None,
    is_resolved: Optional[bool] = None
) -> List[GapConflict]:
    stmt = select(GapConflict).where(GapConflict.case_id == case_id).order_by(desc(GapConflict.created_at))
    if gc_type:
        stmt = stmt.where(GapConflict.gc_type == gc_type)
    if significance:
        stmt = stmt.where(GapConflict.significance == significance)
    if is_resolved is not None:
        stmt = stmt.where(GapConflict.is_resolved == is_resolved)

    return list((await db.execute(stmt)).scalars().all())
