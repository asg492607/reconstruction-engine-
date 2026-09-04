from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import Evidence
from app.models.enums import EvidenceType, Department, ProcessingStatus
from app.routing_engine.rules import determine_authorized_departments

async def route_and_classify_evidence(
    db: AsyncSession,
    evidence: Evidence,
    evidence_type: Optional[EvidenceType] = None,
    override_departments: Optional[List[Department]] = None,
    classification_notes: Optional[str] = None
) -> Evidence:
    if evidence_type is not None:
        evidence.evidence_type = evidence_type

    if override_departments is not None and len(override_departments) > 0:
        evidence.authorized_departments = [d.value if hasattr(d, "value") else str(d) for d in override_departments]
    else:
        evidence.authorized_departments = determine_authorized_departments(evidence.evidence_type)

    evidence.is_classified = True
    if classification_notes:
        evidence.classification_notes = classification_notes
    if evidence.processing_status == ProcessingStatus.PENDING:
        evidence.processing_status = ProcessingStatus.ROUTING

    await db.commit()
    await db.refresh(evidence)
    return evidence
