from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import Evidence, Observation, Case
from app.models.enums import (
    EvidenceType, ProcessingStatus, Department, ObservationType,
    TimeConfidence, TimeReliability, EvidenceQuality
)
from app.evidence.storage import storage_manager
from app.observations.service import create_observation
from app.observations.schemas import ObservationCreate
from app.department_engines.investigation.cctv import cctv_processor
from app.department_engines.investigation.witness import witness_processor
from app.department_engines.investigation.inventory import inventory_processor
from app.department_engines.investigation.vehicle import vehicle_processor
from app.department_engines.investigation.audio import audio_processor
from app.department_engines.forensic.image import forensic_image_processor
from app.department_engines.forensic.report import forensic_report_processor
from app.department_engines.financial.transactions import financial_transaction_processor

logger = logging.getLogger(__name__)

async def run_investigation_pipeline(
    db: AsyncSession,
    case: Case,
    evidence: Evidence
) -> List[Observation]:
    """
    Executes the multi-modality Investigation & Forensic analysis pipeline on authorized exhibits.
    Extracts high-fidelity, empirically grounded observations stamped with department provenance.
    """
    evidence.processing_status = ProcessingStatus.IN_PROGRESS
    await db.commit()

    # Resilient storage retrieval: fetch file bytes or fallback to metadata payload
    file_bytes = b""
    try:
        if evidence.storage_key:
            file_bytes = storage_manager.get_file_bytes(evidence.storage_key)
    except Exception as e:
        logger.warning(f"Storage retrieval fallback for evidence {evidence.id}: {e}")
        meta = evidence.metadata_json or {}
        raw_txt = meta.get("statement_text") or meta.get("narrative") or meta.get("content") or meta.get("text") or ""
        file_bytes = raw_txt.encode("utf-8")

    base_time = case.incident_time_observed or datetime.now(timezone.utc)
    observation_inputs: List[ObservationCreate] = []

    try:
        # 1. Modality-specific processing
        if evidence.evidence_type == EvidenceType.CCTV:
            observation_inputs = cctv_processor.process_cctv_file(
                file_bytes=file_bytes,
                filename=evidence.original_filename,
                evidence_id=evidence.id,
                metadata=evidence.metadata_json,
                base_timestamp=base_time
            )

        elif evidence.evidence_type == EvidenceType.IMAGE:
            observation_inputs = forensic_image_processor.process_image_file(
                image_bytes=file_bytes,
                filename=evidence.original_filename,
                evidence_id=evidence.id,
                metadata=evidence.metadata_json,
                base_timestamp=base_time
            )

        elif evidence.evidence_type == EvidenceType.WITNESS_STATEMENT:
            text_content = file_bytes.decode("utf-8", errors="replace")
            observation_inputs = witness_processor.process_witness_statement(
                statement_text=text_content,
                evidence_id=evidence.id,
                base_timestamp=base_time
            )

        elif evidence.evidence_type == EvidenceType.INVENTORY_RECORD:
            text_content = file_bytes.decode("utf-8", errors="replace")
            observation_inputs = inventory_processor.process_inventory_data(
                content=text_content,
                evidence_id=evidence.id,
                base_timestamp=base_time
            )

        elif evidence.evidence_type == EvidenceType.VEHICLE_RECORD:
            text_content = file_bytes.decode("utf-8", errors="replace")
            observation_inputs = vehicle_processor.process_vehicle_record(
                record_text=text_content,
                evidence_id=evidence.id,
                base_timestamp=base_time
            )

        elif evidence.evidence_type == EvidenceType.AUDIO:
            observation_inputs = audio_processor.process_audio_file(
                audio_bytes=file_bytes,
                filename=evidence.original_filename,
                evidence_id=evidence.id,
                base_timestamp=base_time
            )

        elif evidence.evidence_type == EvidenceType.FORENSIC_REPORT:
            text_content = file_bytes.decode("utf-8", errors="replace")
            observation_inputs = forensic_report_processor.process_report_text(
                report_text=text_content,
                evidence_id=evidence.id,
                base_timestamp=base_time
            )

        elif evidence.evidence_type == EvidenceType.TRANSACTION_RECORD:
            text_content = file_bytes.decode("utf-8", errors="replace")
            observation_inputs = financial_transaction_processor.process_transactions(
                transaction_data=text_content,
                evidence_id=evidence.id,
                base_timestamp=base_time
            )

        else:
            # DOCUMENT or OTHER fallback
            text_content = file_bytes.decode("utf-8", errors="replace")
            # If CSV formatted, attempt inventory or transaction parsing
            if "," in text_content and ("sku" in text_content.lower() or "price" in text_content.lower() or "amount" in text_content.lower()):
                observation_inputs = inventory_processor.process_inventory_data(
                    content=text_content,
                    evidence_id=evidence.id,
                    base_timestamp=base_time
                )
            else:
                observation_inputs = witness_processor.process_witness_statement(
                    statement_text=text_content,
                    evidence_id=evidence.id,
                    base_timestamp=base_time
                )

        # 2. Ingest OCR intelligence if attached to metadata
        if evidence.metadata_json and "ocr_data" in evidence.metadata_json:
            ocr = evidence.metadata_json["ocr_data"]
            observation_inputs.append(
                ObservationCreate(
                    evidence_id=evidence.id,
                    department=Department.FORENSIC if evidence.evidence_type in [EvidenceType.DOCUMENT, EvidenceType.IMAGE] else Department.INVESTIGATION,
                    observation_type=ObservationType.TEXT_EXTRACTED,
                    raw_data={
                        "document_type": ocr.get("document_type", "OCR_EXTRACTED_RECORD"),
                        "merchant_or_issuer": ocr.get("merchant_or_issuer"),
                        "monetary_amounts": ocr.get("monetary_amounts", []),
                        "total_amount": ocr.get("total_amount"),
                        "skus_and_serials": ocr.get("skus_and_serials", []),
                        "dates_and_times": ocr.get("dates_and_times", []),
                        "forensic_flags": ocr.get("forensic_flags", []),
                        "line_items": ocr.get("line_items", []),
                        "sha256_hash": ocr.get("sha256_hash", evidence.sha256_hash),
                        "summary": ocr.get("summary", "Verified OCR document intelligence")
                    },
                    observed_time_raw=ocr.get("dates_and_times", [None])[0] if ocr.get("dates_and_times") else None,
                    observed_time_parsed=base_time,
                    time_confidence=TimeConfidence.APPROXIMATE,
                    time_reliability=TimeReliability.HIGH,
                    observation_confidence=ocr.get("confidence_score", 0.95),
                    evidence_quality=EvidenceQuality.HIGH,
                    model_name=ocr.get("provider", "Forensic-OCR-Engine"),
                    model_version="2.0.0"
                )
            )

        # 3. Persist and return observations
        persisted_observations = []
        for obs_in in observation_inputs:
            obs = await create_observation(db, case.id, obs_in)
            persisted_observations.append(obs)

        evidence.processing_status = ProcessingStatus.COMPLETED
        await db.commit()
        await db.refresh(evidence)
        return persisted_observations

    except Exception as e:
        logger.error(f"Error executing investigation pipeline on evidence {evidence.id}: {e}", exc_info=True)
        evidence.processing_status = ProcessingStatus.FAILED
        await db.commit()
        raise e
