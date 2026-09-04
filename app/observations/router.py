from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User
from app.models.enums import Department, ObservationType, VerificationStatus
from app.cases.service import get_case_by_id
from app.observations.schemas import ObservationCreate, ObservationResponse
from app.observations.service import (
    create_observation, get_observation_by_id, list_observations_for_case,
    get_observation_provenance_chain
)
from app.policy import Action, check_access
from app.audit import record_audit_log

router = APIRouter(tags=["Observations"])

@router.post("/cases/{case_id}/observations", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
async def add_manual_observation(
    case_id: str,
    obs_in: ObservationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.CREATE_OBSERVATION, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to add observation")

    obs = await create_observation(db, case_id, obs_in)
    await record_audit_log(
        db=db,
        action="OBSERVATION_CREATED",
        case_id=case_id,
        user=current_user,
        target_type="OBSERVATION",
        target_id=obs.id,
        after_state={"type": obs.observation_type.value, "department": obs.department.value},
        ip_address=request.client.host if request.client else None
    )
    return obs

@router.get("/cases/{case_id}/observations", response_model=List[ObservationResponse])
async def list_observations(
    case_id: str,
    department: Optional[Department] = None,
    observation_type: Optional[ObservationType] = None,
    verification_status: Optional[VerificationStatus] = None,
    evidence_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_CASE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await list_observations_for_case(
        db=db,
        case_id=case_id,
        department=department,
        observation_type=observation_type,
        verification_status=verification_status,
        evidence_id=evidence_id
    )

@router.get("/cases/{case_id}/observations/{obs_id}", response_model=ObservationResponse)
async def get_observation(
    case_id: str,
    obs_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    obs = await get_observation_by_id(db, obs_id)
    if not obs or obs.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found")
    return obs

@router.get("/cases/{case_id}/observations/{obs_id}/provenance")
async def get_observation_provenance(
    case_id: str,
    obs_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    chain = await get_observation_provenance_chain(db, obs_id)
    if not chain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found")
    return chain
