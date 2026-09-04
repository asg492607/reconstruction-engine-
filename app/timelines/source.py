from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.models.entities import SourceTimeline, SourceTimelineEvent, Evidence, Observation
from app.models.enums import Department, TimeConfidence

async def build_source_timeline_for_evidence(
    db: AsyncSession,
    case_id: str,
    evidence: Evidence,
    observations: List[Observation]
) -> SourceTimeline:
    # Check if timeline already exists
    stmt = (
        select(SourceTimeline)
        .where(SourceTimeline.evidence_id == evidence.id)
        .options(selectinload(SourceTimeline.events))
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing

    timeline = SourceTimeline(
        case_id=case_id,
        source_label=evidence.original_filename.split(".")[0].upper(),
        evidence_id=evidence.id,
        department=evidence.authorized_departments[0] if evidence.authorized_departments else Department.INVESTIGATION
    )
    db.add(timeline)
    await db.flush()

    # Sort observations chronologically
    sorted_obs = sorted(
        observations,
        key=lambda o: o.observed_time_parsed or datetime.min.replace(tzinfo=timezone.utc)
    )

    for idx, obs in enumerate(sorted_obs):
        # Format human-readable event description from observation
        desc = f"Observed {obs.observation_type.value.lower().replace('_', ' ')} at {obs.location_label or 'scene'}"
        if obs.raw_data.get("clothing"):
            desc += f" ({obs.raw_data['clothing']})"
        elif obs.raw_data.get("item_name"):
            desc += f" ({obs.raw_data['item_name']})"
        elif obs.raw_data.get("vehicle_type"):
            desc += f" ({obs.raw_data['vehicle_type']}, {obs.raw_data.get('license_plate', '')})"

        event = SourceTimelineEvent(
            source_timeline_id=timeline.id,
            observation_id=obs.id,
            event_type=obs.observation_type.value,
            description=desc,
            observed_time_raw=obs.observed_time_raw,
            event_time=obs.observed_time_parsed,
            time_confidence=obs.time_confidence,
            time_window_min=obs.time_window_min,
            time_window_max=obs.time_window_max,
            entity_ids=[],
            sequence_order=idx + 1
        )
        db.add(event)

    await db.commit()
    return await get_source_timeline_by_id(db, timeline.id)

async def get_source_timeline_by_id(db: AsyncSession, timeline_id: str) -> Optional[SourceTimeline]:
    stmt = (
        select(SourceTimeline)
        .where(SourceTimeline.id == timeline_id)
        .options(selectinload(SourceTimeline.events))
    )
    return (await db.execute(stmt)).scalar_one_or_none()

async def list_source_timelines_for_case(db: AsyncSession, case_id: str) -> List[SourceTimeline]:
    stmt = (
        select(SourceTimeline)
        .where(SourceTimeline.case_id == case_id)
        .options(selectinload(SourceTimeline.events))
        .order_by(SourceTimeline.created_at)
    )
    return list((await db.execute(stmt)).scalars().all())
