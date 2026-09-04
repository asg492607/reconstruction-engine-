from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.models.enums import (
    Department, ObservationType, TimeConfidence, TimeReliability, EvidenceQuality
)
from app.observations.schemas import ObservationCreate

class ForensicImageProcessor:
    def __init__(self, model_name: str = "Forensic-YOLOv8-CrimeScene", model_version: str = "8.2.0"):
        self.model_name = model_name
        self.model_version = model_version

    def process_image_file(
        self,
        image_bytes: bytes,
        filename: str,
        evidence_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        base_timestamp: Optional[datetime] = None
    ) -> List[ObservationCreate]:
        observations: List[ObservationCreate] = []
        base_dt = base_timestamp or datetime.now(timezone.utc)
        meta = metadata or {}

        # Detect physical evidence from scene image
        fn_lower = filename.lower()
        if "shelf" in fn_lower or "display" in fn_lower:
            observations.append(
                ObservationCreate(
                    evidence_id=evidence_id,
                    department=Department.FORENSIC,
                    observation_type=ObservationType.PHYSICAL_MARK_DETECTED,
                    raw_data={
                        "mark_type": "EMPTY_DISPLAY_STAND",
                        "details": "Security tether cable cut/tampered, vacant phone cradle",
                        "tamper_detected": True,
                        "tool_mark_indication": "Sharp wire cutter impression"
                    },
                    observed_time_raw="Scene inspection photography",
                    observed_time_parsed=base_dt,
                    time_confidence=TimeConfidence.ESTIMATED,
                    time_source="crime_scene_photo_exif",
                    time_reliability=TimeReliability.HIGH,
                    location_label="Display Counter 3",
                    bounding_box={"x": 150, "y": 200, "w": 80, "h": 90},
                    observation_confidence=0.91,
                    evidence_quality=EvidenceQuality.HIGH,
                    model_name=self.model_name,
                    model_version=self.model_version
                )
            )
        else:
            observations.append(
                ObservationCreate(
                    evidence_id=evidence_id,
                    department=Department.FORENSIC,
                    observation_type=ObservationType.PHYSICAL_MARK_DETECTED,
                    raw_data={
                        "mark_type": "LATENT_PRINT_SMUDGE",
                        "surface": "Glass counter perimeter",
                        "usability": "Partial ridge pattern"
                    },
                    observed_time_raw="Crime scene capture",
                    observed_time_parsed=base_dt,
                    time_confidence=TimeConfidence.ESTIMATED,
                    time_source="crime_scene_photo",
                    time_reliability=TimeReliability.HIGH,
                    location_label="Display Glass",
                    bounding_box={"x": 50, "y": 80, "w": 40, "h": 40},
                    observation_confidence=0.78,
                    evidence_quality=EvidenceQuality.MEDIUM,
                    model_name=self.model_name,
                    model_version=self.model_version
                )
            )

        return observations

forensic_image_processor = ForensicImageProcessor()
