from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User
from app.models.enums import CaseStatus
from app.cases.schemas import (
    CaseCreate, CaseUpdate, CaseAssign, CaseSnapshotRequest,
    CaseResponse, CaseAssignmentResponse, CaseVersionResponse
)
from app.cases.service import (
    create_case, get_case_by_id, list_cases, update_case,
    assign_user_to_case, snapshot_case_version, get_case_versions,
    get_case_version_by_number
)
from app.policy import Action, check_access
from app.audit import record_audit_log

router = APIRouter(prefix="/cases", tags=["Cases"])

@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_new_case(
    case_in: CaseCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await create_case(db, case_in, current_user)
    await record_audit_log(
        db=db,
        action="CASE_CREATED",
        case_id=case.id,
        user=current_user,
        target_type="CASE",
        target_id=case.id,
        after_state={"case_number": case.case_number, "title": case.title, "status": case.status.value},
        ip_address=request.client.host if request.client else None
    )
    return case

@router.get("", response_model=List[CaseResponse])
async def get_all_cases(
    status: Optional[CaseStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await list_cases(db, status=status, user=current_user)

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case_details(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_CASE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this case")
    return case

@router.patch("/{case_id}", response_model=CaseResponse)
async def patch_case(
    case_id: str,
    case_update: CaseUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.UPDATE_CASE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: cannot update case")

    old_status = case.status.value
    updated = await update_case(db, case, case_update)
    
    action_name = "CASE_STATUS_CHANGED" if case_update.status and case_update.status.value != old_status else "CASE_UPDATED"
    await record_audit_log(
        db=db,
        action=action_name,
        case_id=case.id,
        user=current_user,
        target_type="CASE",
        target_id=case.id,
        before_state={"status": old_status},
        after_state={"status": updated.status.value, "title": updated.title},
        ip_address=request.client.host if request.client else None
    )
    return updated

@router.post("/{case_id}/assign", response_model=CaseAssignmentResponse)
async def assign_user(
    case_id: str,
    assign_in: CaseAssign,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.ASSIGN_CASE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to assign users to this case")

    assignment = await assign_user_to_case(
        db=db,
        case_id=case_id,
        user_id=assign_in.user_id,
        department=assign_in.department,
        assigned_by_id=current_user.id
    )
    await record_audit_log(
        db=db,
        action="USER_ASSIGNED_TO_CASE",
        case_id=case_id,
        user=current_user,
        target_type="CASE_ASSIGNMENT",
        target_id=assignment.id,
        after_state={"assigned_user": assign_in.user_id, "department": assign_in.department.value},
        ip_address=request.client.host if request.client else None
    )
    return assignment

@router.post("/{case_id}/snapshot", response_model=CaseVersionResponse)
async def create_snapshot(
    case_id: str,
    body: CaseSnapshotRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.SNAPSHOT_CASE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to snapshot case")

    version = await snapshot_case_version(db, case_id, current_user.id, reason=body.reason)
    await record_audit_log(
        db=db,
        action="CASE_VERSION_SNAPSHOTTED",
        case_id=case_id,
        user=current_user,
        target_type="CASE_VERSION",
        target_id=version.id,
        after_state={"version_number": version.version_number, "reason": version.reason},
        ip_address=request.client.host if request.client else None
    )
    return version

@router.get("/{case_id}/versions", response_model=List[CaseVersionResponse])
async def list_versions(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_CASE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await get_case_versions(db, case_id)

@router.get("/{case_id}/versions/{version_number}", response_model=CaseVersionResponse)
async def get_version(
    case_id: str,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_CASE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    version = await get_case_version_by_number(db, case_id, version_number)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return version
