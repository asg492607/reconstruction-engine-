from datetime import datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import Evidence, Observation, Case
from app.models.enums import EvidenceType, ProcessingStatus, Department
from app.evidence.storage import storage_manager
from app.observations.service import create_observation
from app.department_engines.investigation.service import run_investigation_pipeline
from app.department_engines.forensic.image import forensic_image_processor
from app.department_engines.forensic.report import forensic_report_processor
from app.department_engines.financial.transactions import financial_transaction_processor

async def dispatch_evidence_processing(
    db: AsyncSession,
    case: Case,
    evidence: Evidence
) -> List[Observation]:
    """
    Unified departmental dispatcher.
    Routes evidence to Investigation, Forensic, or Financial engines based on canonical type.
    """
    file_bytes = storage_manager.get_file_bytes(evidence.storage_key)
    base_time = case.incident_time_observed or datetime.now(timezone.utc)

    # Forensic Engine routing
    if evidence.evidence_type == EvidenceType.IMAGE:
        evidence.processing_status = ProcessingStatus.IN_PROGRESS
        await db.commit()
        obs_inputs = forensic_image_processor.process_image_file(
            image_bytes=file_bytes,
            filename=evidence.original_filename,
            evidence_id=evidence.id,
            metadata=evidence.metadata_json,
            base_timestamp=base_time
        )
        saved = []
        for obs_in in obs_inputs:
            obs = await create_observation(db, case.id, obs_in)
            saved.append(obs)
        evidence.processing_status = ProcessingStatus.COMPLETED
        await db.commit()
        return saved

    elif evidence.evidence_type == EvidenceType.FORENSIC_REPORT:
        evidence.processing_status = ProcessingStatus.IN_PROGRESS
        await db.commit()
        text_content = file_bytes.decode("utf-8", errors="replace")
        obs_inputs = forensic_report_processor.process_report_text(
            report_text=text_content,
            evidence_id=evidence.id,
            base_timestamp=base_time
        )
        saved = []
        for obs_in in obs_inputs:
            obs = await create_observation(db, case.id, obs_in)
            saved.append(obs)
        evidence.processing_status = ProcessingStatus.COMPLETED
        await db.commit()
        return saved

    # Financial Engine routing
    elif evidence.evidence_type == EvidenceType.TRANSACTION_RECORD:
        evidence.processing_status = ProcessingStatus.IN_PROGRESS
        await db.commit()
        text_content = file_bytes.decode("utf-8", errors="replace")
        obs_inputs = financial_transaction_processor.process_transactions(
            transaction_data=text_content,
            evidence_id=evidence.id,
            base_timestamp=base_time
        )
        saved = []
        for obs_in in obs_inputs:
            obs = await create_observation(db, case.id, obs_in)
            saved.append(obs)
        evidence.processing_status = ProcessingStatus.COMPLETED
        await db.commit()
        return saved

    # Investigation Engine routing
    else:
        return await run_investigation_pipeline(db, case, evidence)
