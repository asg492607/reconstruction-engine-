from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.models.entities import (
    CorrelatedTimelineEvent, SourceTimeline, SourceTimelineEvent, Observation, Case, Evidence
)
from app.models.enums import Department, TimeConfidence
from app.timelines.source import list_source_timelines_for_case, build_source_timeline_for_evidence
from app.gap_conflict.detector import detect_case_gaps_and_conflicts

async def correlate_case_timelines(
    db: AsyncSession,
    case: Case
) -> List[CorrelatedTimelineEvent]:
    # 1. Fetch all evidence items and observations
    ev_stmt = select(Evidence).where(Evidence.case_id == case.id)
    evidence_items = (await db.execute(ev_stmt)).scalars().all()

    obs_stmt = select(Observation).where(Observation.case_id == case.id)
    all_obs = (await db.execute(obs_stmt)).scalars().all()

    # Ensure source timelines are built for all evidence items
    for ev in evidence_items:
        obs_for_ev = [o for o in all_obs if o.evidence_id == ev.id]
        if obs_for_ev:
            await build_source_timeline_for_evidence(db, case.id, ev, obs_for_ev)

    source_timelines = await list_source_timelines_for_case(db, case.id)

    # Check if correlated events already exist
    existing_stmt = (
        select(CorrelatedTimelineEvent)
        .where(CorrelatedTimelineEvent.case_id == case.id)
        .order_by(CorrelatedTimelineEvent.event_time)
    )
    existing_events = (await db.execute(existing_stmt)).scalars().all()
    if existing_events:
        return list(existing_events)

    # Flatten all source events
    source_events: List[SourceTimelineEvent] = []
    for st in source_timelines:
        source_events.extend(st.events)

    # Sort source events chronologically
    sorted_events = sorted(
        source_events,
        key=lambda e: e.event_time or datetime.min.replace(tzinfo=timezone.utc)
    )

    correlated_events = []
    for se in sorted_events:
        # Find corresponding evidence
        obs = next((o for o in all_obs if o.id == se.observation_id), None)
        ev_id = obs.evidence_id if obs else None

        corr_event = CorrelatedTimelineEvent(
            case_id=case.id,
            event_time=se.event_time,
            time_confidence=se.time_confidence,
            time_window_min=se.time_window_min,
            time_window_max=se.time_window_max,
            description=se.description,
            source_event_ids=[se.id],
            supporting_evidence_ids=[ev_id] if ev_id else [],
            entity_ids=se.entity_ids or [],
            department=Department.CORRELATED,
            is_disputed=False,
            is_verified=False
        )
        db.add(corr_event)
        correlated_events.append(corr_event)

    await db.commit()

    # Automatically trigger gap and conflict detection on the correlated timeline
    await detect_case_gaps_and_conflicts(db, case, correlated_events, all_obs)

    # Re-fetch in order
    result = await db.execute(existing_stmt)
    return list(result.scalars().all())

async def get_correlated_timeline(
    db: AsyncSession,
    case_id: str,
    window_start: Optional[datetime] = None,
    window_end: Optional[datetime] = None
) -> List[CorrelatedTimelineEvent]:
    stmt = (
        select(CorrelatedTimelineEvent)
        .where(CorrelatedTimelineEvent.case_id == case_id)
        .order_by(CorrelatedTimelineEvent.event_time)
    )
    if window_start:
        stmt = stmt.where(CorrelatedTimelineEvent.event_time >= window_start)
    if window_end:
        stmt = stmt.where(CorrelatedTimelineEvent.event_time <= window_end)

    return list((await db.execute(stmt)).scalars().all())
