import json
from typing import Optional, List, Dict, Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.models.entities import Evidence, Case, User, Observation, Finding, Claim
from app.models.enums import EvidenceType, ProcessingStatus
from app.evidence.storage import storage_manager
from app.routing_engine.rules import determine_authorized_departments

def guess_evidence_type_from_filename(filename: str) -> EvidenceType:
    fn = filename.lower()
    if fn.endswith((".mp4", ".avi", ".mov", ".mkv")):
        return EvidenceType.CCTV
    if fn.endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp")):
        return EvidenceType.IMAGE
    if fn.endswith((".mp3", ".wav", ".m4a", ".aac", ".ogg")):
        return EvidenceType.AUDIO
    if "witness" in fn:
        return EvidenceType.WITNESS_STATEMENT
    if "inventory" in fn or "stock" in fn:
        return EvidenceType.INVENTORY_RECORD
    if "transaction" in fn or "payment" in fn or "receipt" in fn:
        return EvidenceType.TRANSACTION_RECORD
    if "vehicle" in fn or "car" in fn:
        return EvidenceType.VEHICLE_RECORD
    if "forensic" in fn:
        return EvidenceType.FORENSIC_REPORT
    if fn.endswith((".pdf", ".txt", ".csv", ".docx", ".xlsx")):
        return EvidenceType.DOCUMENT
    return EvidenceType.OTHER

async def ingest_evidence(
    db: AsyncSession,
    case_id: str,
    user: User,
    upload_file: UploadFile,
    evidence_type: Optional[EvidenceType] = None,
    metadata_json: Optional[Dict[str, Any]] = None
) -> Evidence:
    contents = await upload_file.read()
    filename = upload_file.filename or "unknown_file"

    # Save to immutable storage and calculate SHA-256 fingerprint
    storage_key, sha256_hash, file_size = await storage_manager.save_file(
        case_id=case_id,
        filename=filename,
        data=contents
    )

    inferred_type = evidence_type or guess_evidence_type_from_filename(filename)
    authorized_depts = determine_authorized_departments(inferred_type)

    evidence = Evidence(
        case_id=case_id,
        evidence_type=inferred_type,
        original_filename=filename,
        storage_key=storage_key,
        file_size_bytes=file_size,
        sha256_hash=sha256_hash,
        mime_type=upload_file.content_type,
        uploaded_by=user.id,
        is_classified=True,
        authorized_departments=authorized_depts,
        processing_status=ProcessingStatus.PENDING,
        metadata_json=metadata_json or {}
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    return evidence

async def get_evidence_by_id(db: AsyncSession, evidence_id: str) -> Optional[Evidence]:
    stmt = select(Evidence).where(Evidence.id == evidence_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_evidence_for_case(
    db: AsyncSession,
    case_id: str,
    evidence_type: Optional[EvidenceType] = None
) -> List[Evidence]:
    stmt = select(Evidence).where(Evidence.case_id == case_id).order_by(desc(Evidence.uploaded_at))
    if evidence_type:
        stmt = stmt.where(Evidence.evidence_type == evidence_type)
    res = await db.execute(stmt)
    return list(res.scalars().all())

async def get_evidence_provenance(db: AsyncSession, evidence_id: str) -> Dict[str, Any]:
    evidence = await get_evidence_by_id(db, evidence_id)
    if not evidence:
        return {}

    # Query observations derived from this evidence
    obs_stmt = select(Observation).where(Observation.evidence_id == evidence_id)
    obs_res = await db.execute(obs_stmt)
    observations = obs_res.scalars().all()

    provenance_data = {
        "evidence_id": evidence.id,
        "original_filename": evidence.original_filename,
        "sha256_hash": evidence.sha256_hash,
        "storage_key": evidence.storage_key,
        "uploaded_at": evidence.uploaded_at.isoformat(),
        "authorized_departments": evidence.authorized_departments,
        "observations_count": len(observations),
        "observations": [
            {
                "id": o.id,
                "type": o.observation_type.value,
                "department": o.department.value,
                "model_name": o.model_name,
                "model_version": o.model_version,
                "confidence": o.observation_confidence,
                "quality": o.evidence_quality.value,
                "time_confidence": o.time_confidence.value,
                "verification_status": o.verification_status.value,
                "raw_data": o.raw_data
            }
            for o in observations
        ]
    }
    return provenance_data
