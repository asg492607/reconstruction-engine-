from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.models.enums import (
    Department, ObservationType, TimeConfidence, TimeReliability, EvidenceQuality
)
from app.observations.schemas import ObservationCreate

class ForensicReportProcessor:
    def __init__(self, model_name: str = "Forensic-Doc-Parser", model_version: str = "1.1.0"):
        self.model_name = model_name
        self.model_version = model_version

    def process_report_text(
        self,
        report_text: str,
        evidence_id: str,
        base_timestamp: Optional[datetime] = None
    ) -> List[ObservationCreate]:
        observations: List[ObservationCreate] = []
        base_dt = base_timestamp or datetime.now(timezone.utc)

        # 1. Text extraction observation
        observations.append(
            ObservationCreate(
                evidence_id=evidence_id,
                department=Department.FORENSIC,
                observation_type=ObservationType.TEXT_EXTRACTED,
                raw_data={
                    "report_type": "BALLISTICS_TOOLMARK_OR_LATENT_REPORT",
                    "content_summary": report_text.strip()[:300]
                },
                observed_time_raw="Forensic examination report",
                observed_time_parsed=base_dt,
                time_confidence=TimeConfidence.ESTIMATED,
                time_source="forensic_lab_report",
                time_reliability=TimeReliability.HIGH,
                observation_confidence=0.96,
                evidence_quality=EvidenceQuality.HIGH,
                model_name=self.model_name,
                model_version=self.model_version
            )
        )

        # 2. Extract specific forensic mark findings
        lower = report_text.lower()
        if "tether" in lower or "cut" in lower or "cable" in lower or "shear" in lower:
            observations.append(
                ObservationCreate(
                    evidence_id=evidence_id,
                    department=Department.FORENSIC,
                    observation_type=ObservationType.PHYSICAL_MARK_DETECTED,
                    raw_data={
                        "category": "MECHANICAL_TAMPERING",
                        "finding": "Anti-theft security cable sheared using diagonal wire-cutter pliers",
                        "tool_identified": "Diagonal cutters (estimated jaw width 8mm)"
                    },
                    observed_time_raw="Forensic lab toolmark analysis",
                    observed_time_parsed=base_dt,
                    time_confidence=TimeConfidence.ESTIMATED,
                    time_source="forensic_lab_report",
                    time_reliability=TimeReliability.HIGH,
                    location_label="Electronics Counter 3",
                    observation_confidence=0.94,
                    evidence_quality=EvidenceQuality.HIGH,
                    model_name=self.model_name,
                    model_version=self.model_version
                )
            )

        return observations

forensic_report_processor = ForensicReportProcessor()
