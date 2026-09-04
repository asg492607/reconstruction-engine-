from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User, CorrelatedTimelineEvent, Observation
from app.models.enums import GapConflictType, Significance
from app.cases.service import get_case_by_id
from app.gap_conflict.schemas import GapConflictResponse, GapConflictResolveRequest
from app.gap_conflict.detector import detect_case_gaps_and_conflicts, resolve_gap_conflict, list_gaps_and_conflicts
from app.policy import Action, check_access
from app.audit import record_audit_log

router = APIRouter(tags=["Gaps & Conflicts"])

@router.post("/cases/{case_id}/gaps-conflicts/detect", response_model=List[GapConflictResponse])
async def detect_gaps(
    case_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.DETECT_GAP_CONFLICT, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    events = (await db.execute(select(CorrelatedTimelineEvent).where(CorrelatedTimelineEvent.case_id == case_id))).scalars().all()
    obs = (await db.execute(select(Observation).where(Observation.case_id == case_id))).scalars().all()

    gcs = await detect_case_gaps_and_conflicts(db, case, list(events), list(obs))
    await record_audit_log(
        db=db,
        action="GAP_CONFLICT_DETECTED",
        case_id=case_id,
        user=current_user,
        target_type="GAP_CONFLICT",
        after_state={"detected_count": len(gcs)},
        ip_address=request.client.host if request.client else None
    )
    return gcs

@router.get("/cases/{case_id}/gaps-conflicts", response_model=List[GapConflictResponse])
async def get_gaps(
    case_id: str,
    gc_type: Optional[GapConflictType] = None,
    significance: Optional[Significance] = None,
    is_resolved: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_GAP_CONFLICT, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await list_gaps_and_conflicts(db, case_id, gc_type, significance, is_resolved)

@router.patch("/cases/{case_id}/gaps-conflicts/{gc_id}/resolve", response_model=GapConflictResponse)
async def resolve_gap(
    case_id: str,
    gc_id: str,
    body: GapConflictResolveRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.RESOLVE_GAP_CONFLICT, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to resolve gaps/conflicts")

    resolved = await resolve_gap_conflict(db, case_id, gc_id, current_user.id, body.resolution_note)
    await record_audit_log(
        db=db,
        action="GAP_RESOLVED",
        case_id=case_id,
        user=current_user,
        target_type="GAP_CONFLICT",
        target_id=resolved.id,
        after_state={"is_resolved": True, "note": body.resolution_note},
        ip_address=request.client.host if request.client else None
    )
    return resolved
