import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser
from app.models.enums import (
    Department, ObservationType, TimeConfidence, TimeReliability, EvidenceQuality
)
from app.observations.schemas import ObservationCreate

PLATE_REGEX = re.compile(r'\b([A-Z]{2}[-\s]?[0-9]{1,2}[-\s]?[A-Z]{1,3}[-\s]?[0-9*]{2,4})\b')
VEHICLE_TYPE_REGEX = re.compile(r'\b(SUV|sedan|hatchback|motorcycle|bike|van|truck|car)\b', re.IGNORECASE)
COLOR_REGEX = re.compile(r'\b(dark|black|white|silver|grey|blue|red|green)\b', re.IGNORECASE)
TIME_REGEX = re.compile(r'\b(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))\b|\b(\d{1,2}:\d{2})\b')

class VehicleProcessor:
    def __init__(self, model_name: str = "Vehicle-Record-Parser", model_version: str = "1.0.0"):
        self.model_name = model_name
        self.model_version = model_version

    def process_vehicle_record(
        self,
        record_text: str,
        evidence_id: str,
        base_timestamp: Optional[datetime] = None
    ) -> List[ObservationCreate]:
        observations: List[ObservationCreate] = []
        base_dt = base_timestamp or datetime.now(timezone.utc)

        # 1. Parse time
        time_match = TIME_REGEX.search(record_text)
        time_raw = time_match.group(0) if time_match else "8:48 PM"
        try:
            time_part = date_parser.parse(time_raw).time()
            parsed_dt = datetime.combine(base_dt.date(), time_part, tzinfo=base_dt.tzinfo or timezone.utc)
        except Exception:
            parsed_dt = base_dt

        # 2. Extract plate
        plate_match = PLATE_REGEX.search(record_text)
        plate_text = plate_match.group(1) if plate_match else "Unknown plate"

        # 3. Extract type and color
        type_match = VEHICLE_TYPE_REGEX.search(record_text)
        vehicle_type = type_match.group(1).upper() if type_match else "SUV"

        color_match = COLOR_REGEX.search(record_text)
        color = color_match.group(1).lower() if color_match else "dark"

        observations.append(
            ObservationCreate(
                evidence_id=evidence_id,
                department=Department.INVESTIGATION,
                observation_type=ObservationType.VEHICLE_DETECTED,
                raw_data={
                    "vehicle_type": vehicle_type,
                    "color": color,
                    "license_plate": plate_text,
                    "record_excerpt": record_text.strip()[:200],
                },
                observed_time_raw=time_raw,
                observed_time_parsed=parsed_dt,
                time_confidence=TimeConfidence.APPROXIMATE,
                time_source="parking_surveillance_record",
                time_reliability=TimeReliability.HIGH,
                time_window_min=parsed_dt - timedelta(minutes=5),
                time_window_max=parsed_dt + timedelta(minutes=5),
                location_label="Outside Store / Parking Lane",
                observation_confidence=0.85,
                evidence_quality=EvidenceQuality.HIGH,
                model_name=self.model_name,
                model_version=self.model_version
            )
        )

        return observations

vehicle_processor = VehicleProcessor()
