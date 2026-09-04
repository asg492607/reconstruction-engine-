from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User
from app.cases.service import get_case_by_id
from app.reconstruction.schemas import HypothesisResponse, HypothesisReviewRequest
from app.reconstruction.engine import (
    generate_theft_hypotheses, get_hypotheses_for_case, get_hypothesis_by_id, review_hypothesis
)
from app.policy import Action, check_access
from app.audit import record_audit_log

router = APIRouter(tags=["Reconstruction"])

@router.post("/cases/{case_id}/hypotheses/generate", response_model=List[HypothesisResponse], status_code=status.HTTP_201_CREATED)
async def generate_hypotheses(
    case_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.GENERATE_HYPOTHESIS, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to generate hypotheses")

    hypotheses = await generate_theft_hypotheses(db, case)
    await record_audit_log(
        db=db,
        action="HYPOTHESIS_GENERATED",
        case_id=case_id,
        user=current_user,
        target_type="HYPOTHESIS",
        after_state={"count": len(hypotheses)},
        ip_address=request.client.host if request.client else None
    )
    return hypotheses

@router.get("/cases/{case_id}/hypotheses", response_model=List[HypothesisResponse])
async def get_hypotheses(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_HYPOTHESIS, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await get_hypotheses_for_case(db, case_id)

@router.get("/cases/{case_id}/hypotheses/{hypothesis_id}", response_model=HypothesisResponse)
async def get_single_hypothesis(
    case_id: str,
    hypothesis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    hyp = await get_hypothesis_by_id(db, hypothesis_id)
    if not hyp or hyp.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hypothesis not found")
    return hyp

@router.post("/cases/{case_id}/hypotheses/{hypothesis_id}/review", response_model=HypothesisResponse)
async def submit_hypothesis_review(
    case_id: str,
    hypothesis_id: str,
    review_in: HypothesisReviewRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.REVIEW_HYPOTHESIS, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to review hypothesis")

    reviewed = await review_hypothesis(
        db=db,
        case_id=case_id,
        hypothesis_id=hypothesis_id,
        user=current_user,
        status=review_in.status,
        review_note=review_in.review_note
    )
    await record_audit_log(
        db=db,
        action=f"HYPOTHESIS_{review_in.status.value}",
        case_id=case_id,
        user=current_user,
        target_type="HYPOTHESIS",
        target_id=reviewed.id,
        after_state={"status": reviewed.status.value, "note": review_in.review_note},
        ip_address=request.client.host if request.client else None
    )
    return reviewed

@router.get("/cases/{case_id}/hypotheses/{hypothesis_id}/provenance-chain")
async def get_hypothesis_chain(
    case_id: str,
    hypothesis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_HYPOTHESIS, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        from app.reconstruction.engine import get_hypothesis_provenance_chain
        chain = await get_hypothesis_provenance_chain(db, case_id, hypothesis_id)
        return chain
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
