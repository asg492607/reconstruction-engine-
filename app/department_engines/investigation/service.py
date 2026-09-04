from datetime import datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import Evidence, Observation, Case
from app.models.enums import EvidenceType, ProcessingStatus, Department
from app.evidence.storage import storage_manager
from app.observations.service import create_observation
from app.department_engines.investigation.cctv import cctv_processor
from app.department_engines.investigation.witness import witness_processor
from app.department_engines.investigation.inventory import inventory_processor
from app.department_engines.investigation.vehicle import vehicle_processor
from app.department_engines.investigation.audio import audio_processor

async def run_investigation_pipeline(
    db: AsyncSession,
    case: Case,
    evidence: Evidence
) -> List[Observation]:
    """
    Executes the Investigation Department analysis pipeline on authorized evidence.
    Generates independent observations stamped with Department.INVESTIGATION.
    """
    evidence.processing_status = ProcessingStatus.IN_PROGRESS
    await db.commit()

    file_bytes = storage_manager.get_file_bytes(evidence.storage_key)
    base_time = case.incident_time_observed or datetime.now(timezone.utc)
    observation_inputs = []

    try:
        if evidence.evidence_type == EvidenceType.CCTV:
            observation_inputs = cctv_processor.process_cctv_file(
                file_bytes=file_bytes,
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

        else:
            # Fallback document processing
            text_content = file_bytes.decode("utf-8", errors="replace")
            observation_inputs = witness_processor.process_witness_statement(
                statement_text=text_content,
                evidence_id=evidence.id,
                base_timestamp=base_time
            )

        persisted_observations = []
        for obs_in in observation_inputs:
            obs = await create_observation(db, case.id, obs_in)
            persisted_observations.append(obs)

        evidence.processing_status = ProcessingStatus.COMPLETED
        await db.commit()
        await db.refresh(evidence)
        return persisted_observations

    except Exception as e:
        evidence.processing_status = ProcessingStatus.FAILED
        await db.commit()
        raise e
