from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User
from app.cases.service import get_case_by_id
from app.copilot.schemas import CopilotQueryRequest, CopilotResponse
from app.copilot.service import answer_copilot_query
from app.policy import Action, check_access
from app.audit import record_audit_log

router = APIRouter(tags=["Investigation Copilot"])

@router.post("/cases/{case_id}/copilot/query", response_model=CopilotResponse)
async def query_copilot(
    case_id: str,
    body: CopilotQueryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.QUERY_COPILOT, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to query copilot")

    response = await answer_copilot_query(db, case, body.query, body.mode or "AUTO")

    await record_audit_log(
        db=db,
        action="COPILOT_QUERIED",
        case_id=case_id,
        user=current_user,
        target_type="COPILOT",
        after_state={"query": body.query[:100], "mode": response.mode, "is_prohibited": response.is_prohibited_query},
        ip_address=request.client.host if request.client else None
    )
    return response
