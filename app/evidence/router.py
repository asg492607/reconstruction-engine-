from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, Response
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User
from app.models.enums import EvidenceType
from app.cases.service import get_case_by_id
from app.evidence.schemas import EvidenceResponse, EvidenceClassifyRequest, EvidenceProvenanceResponse
from app.evidence.service import ingest_evidence, get_evidence_by_id, list_evidence_for_case, get_evidence_provenance
from app.evidence.storage import storage_manager
from app.routing_engine.service import route_and_classify_evidence
from app.policy import Action, check_access
from app.audit import record_audit_log

router = APIRouter(tags=["Evidence"])

@router.post("/cases/{case_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    case_id: str,
    request: Request,
    file: UploadFile = File(...),
    evidence_type: Optional[EvidenceType] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.UPLOAD_EVIDENCE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to upload evidence")

    evidence = await ingest_evidence(
        db=db,
        case_id=case_id,
        user=current_user,
        upload_file=file,
        evidence_type=evidence_type
    )

    await record_audit_log(
        db=db,
        action="EVIDENCE_UPLOADED",
        case_id=case_id,
        user=current_user,
        target_type="EVIDENCE",
        target_id=evidence.id,
        after_state={
            "filename": evidence.original_filename,
            "sha256": evidence.sha256_hash,
            "size": evidence.file_size_bytes,
            "type": evidence.evidence_type.value,
            "authorized_departments": evidence.authorized_departments
        },
        ip_address=request.client.host if request.client else None
    )
    return evidence

@router.get("/cases/{case_id}/evidence", response_model=List[EvidenceResponse])
async def list_evidence(
    case_id: str,
    evidence_type: Optional[EvidenceType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not check_access(current_user, Action.VIEW_CASE, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    all_evidence = await list_evidence_for_case(db, case_id, evidence_type=evidence_type)
    # ABAC filter per evidence authorized departments
    accessible = []
    for ev in all_evidence:
        if check_access(current_user, Action.VIEW_EVIDENCE, resource=ev, case=case):
            accessible.append(ev)
    return accessible

@router.get("/cases/{case_id}/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    case_id: str,
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    evidence = await get_evidence_by_id(db, evidence_id)
    if not evidence or evidence.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    if not check_access(current_user, Action.VIEW_EVIDENCE, resource=evidence, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this evidence")
    return evidence

@router.get("/cases/{case_id}/evidence/{evidence_id}/download")
async def download_evidence_file(
    case_id: str,
    evidence_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    evidence = await get_evidence_by_id(db, evidence_id)
    if not evidence or evidence.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    if not check_access(current_user, Action.DOWNLOAD_EVIDENCE, resource=evidence, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to download evidence")

    file_bytes = storage_manager.get_file_bytes(evidence.storage_key)

    await record_audit_log(
        db=db,
        action="EVIDENCE_DOWNLOADED",
        case_id=case_id,
        user=current_user,
        target_type="EVIDENCE",
        target_id=evidence.id,
        ip_address=request.client.host if request.client else None
    )

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=evidence.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{evidence.original_filename}"'}
    )

@router.post("/cases/{case_id}/evidence/{evidence_id}/classify", response_model=EvidenceResponse)
async def classify_evidence(
    case_id: str,
    evidence_id: str,
    classify_in: EvidenceClassifyRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    evidence = await get_evidence_by_id(db, evidence_id)
    if not evidence or evidence.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    if not check_access(current_user, Action.CLASSIFY_EVIDENCE, resource=evidence, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to classify evidence")

    updated = await route_and_classify_evidence(
        db=db,
        evidence=evidence,
        evidence_type=classify_in.evidence_type,
        override_departments=classify_in.authorized_departments,
        classification_notes=classify_in.classification_notes
    )

    await record_audit_log(
        db=db,
        action="EVIDENCE_CLASSIFIED",
        case_id=case_id,
        user=current_user,
        target_type="EVIDENCE",
        target_id=evidence.id,
        after_state={
            "type": updated.evidence_type.value,
            "authorized_departments": updated.authorized_departments
        },
        ip_address=request.client.host if request.client else None
    )
    return updated

@router.get("/cases/{case_id}/evidence/{evidence_id}/routing")
async def get_evidence_routing(
    case_id: str,
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    evidence = await get_evidence_by_id(db, evidence_id)
    if not evidence or evidence.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    return {
        "evidence_id": evidence.id,
        "evidence_type": evidence.evidence_type.value,
        "authorized_departments": evidence.authorized_departments,
        "is_classified": evidence.is_classified,
        "processing_status": evidence.processing_status.value
    }

from app.department_engines.dispatcher import dispatch_evidence_processing

@router.post("/cases/{case_id}/evidence/{evidence_id}/process")
async def process_evidence(
    case_id: str,
    evidence_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    evidence = await get_evidence_by_id(db, evidence_id)
    if not evidence or evidence.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    if not check_access(current_user, Action.PROCESS_EVIDENCE, resource=evidence, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to process evidence")

    observations = await dispatch_evidence_processing(db, case, evidence)

    await record_audit_log(
        db=db,
        action="EVIDENCE_PROCESSED",
        case_id=case_id,
        user=current_user,
        target_type="EVIDENCE",
        target_id=evidence.id,
        after_state={"observations_generated": len(observations), "status": evidence.processing_status.value},
        ip_address=request.client.host if request.client else None
    )

    return {
        "status": "COMPLETED",
        "evidence_id": evidence.id,
        "observations_generated": len(observations),
        "observations": [
            {
                "id": o.id,
                "type": o.observation_type.value,
                "confidence": o.observation_confidence,
                "time_raw": o.observed_time_raw,
                "time_confidence": o.time_confidence.value,
                "location": o.location_label,
            }
            for o in observations
        ]
    }

@router.get("/cases/{case_id}/evidence/{evidence_id}/provenance", response_model=EvidenceProvenanceResponse)
async def get_provenance(
    case_id: str,
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    evidence = await get_evidence_by_id(db, evidence_id)
    if not evidence or evidence.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    if not check_access(current_user, Action.VIEW_EVIDENCE, resource=evidence, case=case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    prov = await get_evidence_provenance(db, evidence_id)
    return prov
