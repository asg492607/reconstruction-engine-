from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User
from app.cases.service import get_case_by_id
from app.reports.schemas import ReportResponse
from app.reports.service import generate_case_report, list_reports_for_case, get_report_by_id
from app.policy import Action, check_access
from app.audit import record_audit_log

router = APIRouter(tags=["Reports"])

@router.post("/cases/{case_id}/reports/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    case_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.GENERATE_REPORT, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to generate report")

    try:
        report = await generate_case_report(db, case, current_user)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    await record_audit_log(
        db=db,
        action="REPORT_GENERATED",
        case_id=case_id,
        user=current_user,
        target_type="REPORT",
        target_id=report.id,
        after_state={"version": report.version},
        ip_address=request.client.host if request.client else None
    )
    return report

@router.get("/cases/{case_id}/reports", response_model=List[ReportResponse])
async def list_reports(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_REPORT, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await list_reports_for_case(db, case_id)

@router.get("/cases/{case_id}/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    case_id: str,
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_REPORT, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    report = await get_report_by_id(db, report_id)
    if not report or report.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report
