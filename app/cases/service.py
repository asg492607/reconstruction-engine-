import random
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from app.models.entities import Case, CaseAssignment, CaseVersion, User, Evidence, Observation, Finding, Claim, Hypothesis
from app.models.enums import CaseStatus, Department, Role
from app.cases.schemas import CaseCreate, CaseUpdate
from app.cases.state_machine import validate_case_status_transition

async def generate_case_number(db: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    count_res = await db.execute(select(func.count(Case.id)))
    count = count_res.scalar() or 0
    return f"THF-{year}-{count + 1:04d}"

async def create_case(db: AsyncSession, case_in: CaseCreate, user: User) -> Case:
    case_num = case_in.case_number or await generate_case_number(db)
    case = Case(
        case_number=case_num,
        title=case_in.title,
        case_type=case_in.case_type,
        offense_category=case_in.offense_category,
        specific_offense=case_in.specific_offense,
        incident_context=case_in.incident_context or {},
        investigative_objectives=case_in.investigative_objectives or [],
        status=CaseStatus.CREATED,
        incident_location=case_in.incident_location,
        incident_time_observed=case_in.incident_time_observed,
        incident_time_estimated=case_in.incident_time_estimated,
        organization_id=user.organization_id,
        created_by=user.id,
        current_version=1,
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)

    # Automatically assign creator to case
    assignment = CaseAssignment(
        case_id=case.id,
        user_id=user.id,
        department=user.department if user.department != Department.ADMIN else Department.INVESTIGATION,
        assigned_by=user.id,
        is_active=True
    )
    db.add(assignment)
    await db.commit()
    
    return await get_case_by_id(db, case.id)

async def get_case_by_id(db: AsyncSession, case_id: str) -> Optional[Case]:
    stmt = (
        select(Case)
        .where(Case.id == case_id)
        .options(selectinload(Case.assignments))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def list_cases(
    db: AsyncSession,
    status: Optional[CaseStatus] = None,
    user: Optional[User] = None
) -> List[Case]:
    stmt = select(Case).options(selectinload(Case.assignments)).order_by(desc(Case.created_at))
    if status:
        stmt = stmt.where(Case.status == status)
    
    result = await db.execute(stmt)
    cases = result.scalars().all()

    # Filter by user assignment if not admin
    if user and user.role != Role.ADMIN:
        assigned_cases = []
        for c in cases:
            if c.created_by == user.id:
                assigned_cases.append(c)
            elif any(a.user_id == user.id and a.is_active for a in c.assignments):
                assigned_cases.append(c)
        return assigned_cases

    return list(cases)

async def update_case(db: AsyncSession, case: Case, case_update: CaseUpdate) -> Case:
    if case_update.status is not None:
        validate_case_status_transition(case.status, case_update.status)
        case.status = case_update.status

    if case_update.title is not None:
        case.title = case_update.title
    if case_update.incident_location is not None:
        case.incident_location = case_update.incident_location
    if case_update.incident_time_observed is not None:
        case.incident_time_observed = case_update.incident_time_observed
    if case_update.incident_time_estimated is not None:
        case.incident_time_estimated = case_update.incident_time_estimated

    case.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return await get_case_by_id(db, case.id)

async def assign_user_to_case(
    db: AsyncSession,
    case_id: str,
    user_id: str,
    department: Department,
    assigned_by_id: str
) -> CaseAssignment:
    # Check if existing active assignment
    stmt = select(CaseAssignment).where(
        CaseAssignment.case_id == case_id,
        CaseAssignment.user_id == user_id,
        CaseAssignment.is_active == True
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    if existing:
        existing.department = department
        await db.commit()
        await db.refresh(existing)
        return existing

    assignment = CaseAssignment(
        case_id=case_id,
        user_id=user_id,
        department=department,
        assigned_by=assigned_by_id,
        is_active=True
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment

async def snapshot_case_version(
    db: AsyncSession,
    case_id: str,
    user_id: str,
    reason: Optional[str] = None
) -> CaseVersion:
    case = await get_case_by_id(db, case_id)
    if not case:
        raise ValueError("Case not found")

    # Build comprehensive case snapshot
    evidence_res = await db.execute(select(Evidence).where(Evidence.case_id == case_id))
    evidence_items = evidence_res.scalars().all()

    observations_res = await db.execute(select(Observation).where(Observation.case_id == case_id))
    obs_items = observations_res.scalars().all()

    findings_res = await db.execute(select(Finding).where(Finding.case_id == case_id))
    findings_items = findings_res.scalars().all()

    claims_res = await db.execute(select(Claim).where(Claim.case_id == case_id))
    claims_items = claims_res.scalars().all()

    hyp_res = await db.execute(select(Hypothesis).where(Hypothesis.case_id == case_id))
    hyp_items = hyp_res.scalars().all()

    snapshot_data = {
        "case": {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "status": case.status.value,
            "incident_location": case.incident_location,
            "incident_time_observed": case.incident_time_observed.isoformat() if case.incident_time_observed else None,
            "current_version": case.current_version,
        },
        "evidence_count": len(evidence_items),
        "evidence": [
            {
                "id": e.id,
                "evidence_type": e.evidence_type.value,
                "original_filename": e.original_filename,
                "sha256_hash": e.sha256_hash,
                "authorized_departments": e.authorized_departments,
            }
            for e in evidence_items
        ],
        "observations_count": len(obs_items),
        "findings_count": len(findings_items),
        "claims_count": len(claims_items),
        "hypotheses_count": len(hyp_items),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    new_version_number = case.current_version + 1
    version_entry = CaseVersion(
        case_id=case.id,
        version_number=new_version_number,
        snapshot=snapshot_data,
        created_by=user_id,
        reason=reason or f"Version {new_version_number} snapshot"
    )
    case.current_version = new_version_number
    db.add(version_entry)
    await db.commit()
    await db.refresh(version_entry)
    return version_entry

async def get_case_versions(db: AsyncSession, case_id: str) -> List[CaseVersion]:
    stmt = select(CaseVersion).where(CaseVersion.case_id == case_id).order_by(desc(CaseVersion.version_number))
    res = await db.execute(stmt)
    return list(res.scalars().all())

async def get_case_version_by_number(db: AsyncSession, case_id: str, version_number: int) -> Optional[CaseVersion]:
    stmt = select(CaseVersion).where(
        CaseVersion.case_id == case_id,
        CaseVersion.version_number == version_number
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()
