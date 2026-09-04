from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User
from app.cases.service import get_case_by_id
from app.timelines.schemas import SourceTimelineResponse, SourceTimelineEventResponse, CorrelatedTimelineEventResponse
from app.timelines.source import list_source_timelines_for_case, get_source_timeline_by_id
from app.timelines.correlator import correlate_case_timelines, get_correlated_timeline
from app.policy import Action, check_access
from app.audit import record_audit_log

router = APIRouter(tags=["Timelines"])

@router.get("/cases/{case_id}/timelines/sources", response_model=List[SourceTimelineResponse])
async def get_source_timelines(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_TIMELINE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await list_source_timelines_for_case(db, case_id)

@router.get("/cases/{case_id}/timelines/sources/{timeline_id}/events", response_model=List[SourceTimelineEventResponse])
async def get_source_timeline_events(
    case_id: str,
    timeline_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    st = await get_source_timeline_by_id(db, timeline_id)
    if not st or st.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source timeline not found")

    return st.events

@router.post("/cases/{case_id}/timelines/correlate", response_model=List[CorrelatedTimelineEventResponse])
async def correlate_timelines(
    case_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.MODIFY_TIMELINE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to correlate timelines")

    events = await correlate_case_timelines(db, case)
    await record_audit_log(
        db=db,
        action="TIMELINE_CORRELATED",
        case_id=case_id,
        user=current_user,
        target_type="CORRELATED_TIMELINE",
        after_state={"events_count": len(events)},
        ip_address=request.client.host if request.client else None
    )
    return events

@router.get("/cases/{case_id}/timelines/correlated", response_model=List[CorrelatedTimelineEventResponse])
async def get_correlated_events(
    case_id: str,
    window_start: Optional[datetime] = None,
    window_end: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_TIMELINE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await get_correlated_timeline(db, case_id, window_start, window_end)
