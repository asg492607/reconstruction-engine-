from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User
from app.cases.service import get_case_by_id
from app.verification.schemas import VerificationResponse, VerificationActionRequest, PendingVerificationsResponse
from app.verification.service import get_pending_verifications_for_case, verify_observation, verify_finding
from app.policy import Action, check_access
from app.audit import record_audit_log

router = APIRouter(tags=["Verification"])

@router.get("/cases/{case_id}/verifications/pending", response_model=PendingVerificationsResponse)
async def get_pending(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_CASE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await get_pending_verifications_for_case(db, case_id)

@router.post("/cases/{case_id}/verifications/observations/{obs_id}", response_model=VerificationResponse)
async def submit_observation_verification(
    case_id: str,
    obs_id: str,
    action_in: VerificationActionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VERIFY_OBSERVATION, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to verify observation")

    ver = await verify_observation(
        db=db,
        case_id=case_id,
        obs_id=obs_id,
        action=action_in.action,
        user=current_user,
        note=action_in.note,
        corrected_data=action_in.corrected_data
    )
    await record_audit_log(
        db=db,
        action=f"OBSERVATION_{action_in.action.value}",
        case_id=case_id,
        user=current_user,
        target_type="OBSERVATION",
        target_id=obs_id,
        after_state={"action": action_in.action.value, "note": action_in.note},
        ip_address=request.client.host if request.client else None
    )
    return ver

@router.post("/cases/{case_id}/verifications/findings/{finding_id}", response_model=VerificationResponse)
async def submit_finding_verification(
    case_id: str,
    finding_id: str,
    action_in: VerificationActionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VERIFY_FINDING, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to verify finding")

    ver = await verify_finding(
        db=db,
        case_id=case_id,
        finding_id=finding_id,
        action=action_in.action,
        user=current_user,
        note=action_in.note
    )
    await record_audit_log(
        db=db,
        action=f"FINDING_{action_in.action.value}",
        case_id=case_id,
        user=current_user,
        target_type="FINDING",
        target_id=finding_id,
        after_state={"action": action_in.action.value, "note": action_in.note},
        ip_address=request.client.host if request.client else None
    )
    return ver
