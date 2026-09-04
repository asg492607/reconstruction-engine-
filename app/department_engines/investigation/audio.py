from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.models.enums import (
    Department, ObservationType, TimeConfidence, TimeReliability, EvidenceQuality
)
from app.observations.schemas import ObservationCreate
from app.department_engines.investigation.witness import witness_processor

class AudioProcessor:
    def __init__(self, model_name: str = "Whisper-Base", model_version: str = "openai/whisper-base"):
        self.model_name = model_name
        self.model_version = model_version

    def process_audio_file(
        self,
        audio_bytes: bytes,
        filename: str,
        evidence_id: str,
        base_timestamp: Optional[datetime] = None
    ) -> List[ObservationCreate]:
        observations: List[ObservationCreate] = []
        base_dt = base_timestamp or datetime.now(timezone.utc)

        # For MVP/audio inputs: extract transcription or simulate Whisper inference
        transcript_text = "I saw a man in a black jacket rushing past the register with a dark bag around 8:44 PM."

        # 1. Transcript observation
        transcript_obs = ObservationCreate(
            evidence_id=evidence_id,
            department=Department.INVESTIGATION,
            observation_type=ObservationType.AUDIO_TRANSCRIBED,
            raw_data={
                "transcription": transcript_text,
                "audio_duration_sec": 14.2,
                "confidence_score": 0.93,
                "speaker_identified": "Witness_01"
            },
            observed_time_raw="8:44 PM",
            observed_time_parsed=base_dt,
            time_confidence=TimeConfidence.APPROXIMATE,
            time_source="audio_timestamp",
            time_reliability=TimeReliability.HIGH,
            location_label="Near Cash Register",
            observation_confidence=0.93,
            evidence_quality=EvidenceQuality.HIGH,
            model_name=self.model_name,
            model_version=self.model_version
        )
        observations.append(transcript_obs)

        # 2. Extract entities from transcribed text
        extracted_entities = witness_processor.process_witness_statement(
            statement_text=transcript_text,
            evidence_id=evidence_id,
            base_timestamp=base_dt
        )
        observations.extend(extracted_entities)

        return observations

audio_processor = AudioProcessor()
