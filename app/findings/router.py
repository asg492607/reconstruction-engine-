from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User
from app.models.enums import Department
from app.cases.service import get_case_by_id
from app.findings.schemas import FindingCreate, FindingResponse, ClaimCreate, ClaimResponse
from app.findings.service import create_finding, list_findings_for_case, create_claim, list_claims_for_case
from app.policy import Action, check_access
from app.audit import record_audit_log

router = APIRouter(tags=["Findings & Claims"])

@router.post("/cases/{case_id}/findings", response_model=FindingResponse, status_code=status.HTTP_201_CREATED)
async def add_finding(
    case_id: str,
    finding_in: FindingCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.CREATE_FINDING, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to add finding")

    finding = await create_finding(db, case_id, finding_in)
    await record_audit_log(
        db=db,
        action="FINDING_CREATED",
        case_id=case_id,
        user=current_user,
        target_type="FINDING",
        target_id=finding.id,
        after_state={"finding_type": finding.finding_type, "department": finding.department.value},
        ip_address=request.client.host if request.client else None
    )
    return finding

@router.get("/cases/{case_id}/findings", response_model=List[FindingResponse])
async def get_findings(
    case_id: str,
    department: Optional[Department] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_FINDING, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await list_findings_for_case(db, case_id, department=department)

@router.post("/cases/{case_id}/claims", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def add_claim(
    case_id: str,
    claim_in: ClaimCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.CREATE_CLAIM, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to add claim")

    claim = await create_claim(db, case_id, claim_in)
    await record_audit_log(
        db=db,
        action="CLAIM_CREATED",
        case_id=case_id,
        user=current_user,
        target_type="CLAIM",
        target_id=claim.id,
        after_state={"strength": claim.claim_strength.value},
        ip_address=request.client.host if request.client else None
    )
    return claim

@router.get("/cases/{case_id}/claims", response_model=List[ClaimResponse])
async def get_claims(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_CLAIM, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await list_claims_for_case(db, case_id)
