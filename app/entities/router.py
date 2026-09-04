from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User
from app.cases.service import get_case_by_id
from app.entities.schemas import (
    CandidateEntityCreate, CandidateEntityResponse, CandidateEntityLinkResponse, EntityLinkCreate
)
from app.entities.service import (
    create_candidate_entity, get_candidate_entity_by_id, list_candidate_entities,
    link_observation_to_entity, confirm_entity_link, auto_link_case_observations
)
from app.policy import Action, check_access
from app.audit import record_audit_log

router = APIRouter(tags=["Entities"])

@router.post("/cases/{case_id}/entities", response_model=CandidateEntityResponse, status_code=status.HTTP_201_CREATED)
async def add_candidate_entity(
    case_id: str,
    entity_in: CandidateEntityCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.CREATE_ENTITY, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to create entity")

    entity = await create_candidate_entity(db, case_id, entity_in)
    await record_audit_log(
        db=db,
        action="ENTITY_CREATED",
        case_id=case_id,
        user=current_user,
        target_type="CANDIDATE_ENTITY",
        target_id=entity.id,
        after_state={"label": entity.label, "type": entity.entity_type.value},
        ip_address=request.client.host if request.client else None
    )
    return entity

@router.get("/cases/{case_id}/entities", response_model=List[CandidateEntityResponse])
async def get_all_entities(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_CASE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await list_candidate_entities(db, case_id)

@router.get("/cases/{case_id}/entities/{entity_id}", response_model=CandidateEntityResponse)
async def get_entity_details(
    case_id: str,
    entity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    entity = await get_candidate_entity_by_id(db, entity_id)
    if not entity or entity.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return entity

@router.post("/cases/{case_id}/entities/{entity_id}/links", response_model=CandidateEntityLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_observation(
    case_id: str,
    entity_id: str,
    link_in: EntityLinkCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    entity = await get_candidate_entity_by_id(db, entity_id)
    if not entity or entity.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    link = await link_observation_to_entity(
        db=db,
        case_id=case_id,
        candidate_entity_id=entity_id,
        observation_id=link_in.observation_id,
        link_confidence=link_in.link_confidence,
        link_method=link_in.link_method,
        link_evidence=link_in.link_evidence
    )
    await record_audit_log(
        db=db,
        action="ENTITY_LINKED",
        case_id=case_id,
        user=current_user,
        target_type="CANDIDATE_ENTITY_LINK",
        target_id=link.id,
        after_state={"entity": entity.label, "confidence": link.link_confidence},
        ip_address=request.client.host if request.client else None
    )
    return link

@router.post("/cases/{case_id}/entities/{entity_id}/links/{link_id}/confirm", response_model=CandidateEntityLinkResponse)
async def confirm_link(
    case_id: str,
    entity_id: str,
    link_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.CONFIRM_ENTITY_LINK, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to confirm entity link")

    confirmed = await confirm_entity_link(db, case_id, link_id, current_user)
    await record_audit_log(
        db=db,
        action="ENTITY_LINK_CONFIRMED",
        case_id=case_id,
        user=current_user,
        target_type="CANDIDATE_ENTITY_LINK",
        target_id=confirmed.id,
        after_state={"is_human_confirmed": True, "confirmed_by": current_user.id},
        ip_address=request.client.host if request.client else None
    )
    return confirmed

@router.post("/cases/{case_id}/entities/{entity_id}/confirm", response_model=CandidateEntityResponse)
async def confirm_candidate_entity(
    case_id: str,
    entity_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.CONFIRM_ENTITY_LINK, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to confirm entity")

    entity = await get_candidate_entity_by_id(db, entity_id)
    if not entity or entity.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    from app.models.enums import IdentityStatus
    entity.identity_status = IdentityStatus.CONFIRMED
    await db.commit()
    await db.refresh(entity)

    await record_audit_log(
        db=db,
        action="CANDIDATE_ENTITY_CONFIRMED",
        case_id=case_id,
        user=current_user,
        target_type="CANDIDATE_ENTITY",
        target_id=entity.id,
        after_state={"identity_status": "CONFIRMED", "confirmed_by": current_user.id},
        ip_address=request.client.host if request.client else None
    )
    return entity

@router.post("/cases/{case_id}/entities/auto-link", response_model=List[CandidateEntityLinkResponse])
async def trigger_auto_link(
    case_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    links = await auto_link_case_observations(db, case_id)
    await record_audit_log(
        db=db,
        action="ENTITY_AUTO_LINKED",
        case_id=case_id,
        user=current_user,
        target_type="CANDIDATE_ENTITY",
        after_state={"total_links_created": len(links)},
        ip_address=request.client.host if request.client else None
    )
    return links
