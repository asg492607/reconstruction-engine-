from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User, Evidence, Observation, Case
from app.models.enums import ObservationType, Department, EvidenceType
from app.cases.service import get_case_by_id
from app.evidence.storage import storage_manager
from app.ocr.service import process_document_ocr
from app.audit import record_audit_log
from app.policy import Action, check_access

router = APIRouter(prefix="/cases/{case_id}/ocr", tags=["Forensic OCR & Document Intelligence"])

@router.post("/extract", response_model=Dict[str, Any])
async def extract_ocr_direct(
    case_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    contents = await file.read()
    result = await process_document_ocr(
        file_bytes=contents,
        filename=file.filename or "uploaded_document",
        mime_type=file.content_type
    )
    return result

@router.post("/evidence/{evidence_id}", response_model=Dict[str, Any])
async def run_evidence_ocr(
    case_id: str,
    evidence_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    res = await db.execute(select(Evidence).where(Evidence.id == evidence_id, Evidence.case_id == case_id))
    evidence = res.scalars().first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence exhibit not found")

    file_bytes = b""
    try:
        file_bytes = storage_manager.get_file_bytes(evidence.storage_key)
    except Exception as e:
        meta = evidence.metadata_json or {}
        raw_txt = meta.get("statement_text") or meta.get("narrative") or ""
        file_bytes = raw_txt.encode("utf-8")

    ocr_result = await process_document_ocr(
        file_bytes=file_bytes,
        filename=evidence.original_filename,
        mime_type=evidence.mime_type
    )

    # Create or update TEXT_EXTRACTED observation
    obs = Observation(
        evidence_id=evidence.id,
        case_id=case_id,
        analysis_version=1,
        department=Department.FORENSIC,
        observation_type=ObservationType.TEXT_EXTRACTED,
        raw_data={
            "document_type": ocr_result.get("document_type"),
            "merchant_or_issuer": ocr_result.get("merchant_or_issuer"),
            "monetary_amounts": ocr_result.get("monetary_amounts"),
            "skus_and_serials": ocr_result.get("skus_and_serials"),
            "dates_and_times": ocr_result.get("dates_and_times"),
            "identified_persons": ocr_result.get("identified_persons"),
            "full_text_excerpt": ocr_result.get("full_text", "")[:500],
            "summary": ocr_result.get("summary")
        },
        observation_confidence=ocr_result.get("confidence_score", 0.95),
        model_name="Gemini-Multimodal-Forensic-OCR" if ocr_result.get("provider") == "GEMINI_MULTIMODAL_OCR" else "Deterministic-Forensic-OCR",
        model_version="2.0.0"
    )
    db.add(obs)

    # Stamp onto evidence metadata
    curr_meta = dict(evidence.metadata_json or {})
    curr_meta["ocr_data"] = ocr_result
    evidence.metadata_json = curr_meta

    await db.commit()

    await record_audit_log(
        db=db,
        action="EVIDENCE_OCR_PERFORMED",
        case_id=case_id,
        user=current_user,
        target_type="EVIDENCE",
        target_id=evidence.id,
        after_state={"ocr_status": ocr_result.get("status"), "document_type": ocr_result.get("document_type")},
        ip_address=request.client.host if request.client else None
    )

    return {
        "evidence_id": evidence.id,
        "observation_id": obs.id,
        "ocr_result": ocr_result
    }

@router.post("/commit", response_model=Dict[str, Any])
async def commit_ocr_to_case(
    case_id: str,
    payload: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    evidence_id = payload.get("evidence_id")
    ocr_data = payload.get("ocr_data", {})
    verified_text = payload.get("verified_text") or ocr_data.get("full_text", "")
    
    # Create persistent verified observation
    obs = Observation(
        evidence_id=evidence_id or case.id,
        case_id=case_id,
        analysis_version=1,
        department=Department.FORENSIC,
        observation_type=ObservationType.TEXT_EXTRACTED,
        raw_data={
            "document_type": ocr_data.get("document_type", "VERIFIED_DOCUMENT"),
            "merchant_or_issuer": ocr_data.get("merchant_or_issuer"),
            "monetary_amounts": ocr_data.get("monetary_amounts", []),
            "total_amount": ocr_data.get("total_amount"),
            "payment_status": ocr_data.get("payment_status"),
            "skus_and_serials": ocr_data.get("skus_and_serials", []),
            "dates_and_times": ocr_data.get("dates_and_times", []),
            "forensic_flags": ocr_data.get("forensic_flags", []),
            "line_items": ocr_data.get("line_items", []),
            "verified_by_officer": current_user.full_name,
            "officer_badge": current_user.role.value,
            "sha256_hash": ocr_data.get("sha256_hash"),
            "transcript_excerpt": verified_text[:1000]
        },
        observation_confidence=1.0,
        verification_status="ACCEPTED",
        model_name="Detective-Verified-Forensic-OCR",
        model_version="2.0.0"
    )
    db.add(obs)
    await db.commit()

    await record_audit_log(
        db=db,
        action="OCR_EVIDENCE_COMMITTED_BY_OFFICER",
        case_id=case_id,
        user=current_user,
        target_type="OBSERVATION",
        target_id=obs.id,
        after_state={
            "doc_type": ocr_data.get("document_type"),
            "total_amount": ocr_data.get("total_amount"),
            "flags": ocr_data.get("forensic_flags")
        },
        ip_address=request.client.host if request.client else None
    )

    return {
        "status": "SUCCESS",
        "observation_id": obs.id,
        "message": "Verified OCR document committed to case repository and audit ledger."
    }

