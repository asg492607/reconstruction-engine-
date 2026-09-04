import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser
from app.models.enums import (
    Department, ObservationType, TimeConfidence, TimeReliability, EvidenceQuality
)
from app.observations.schemas import ObservationCreate

TIME_REGEX = re.compile(r'\b(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))\b|\b(\d{1,2}:\d{2})\b')
CLOTHING_REGEX = re.compile(r'\b(?:wearing|in)\s+((?:a\s+)?(?:black|dark|navy|blue|red|green|grey|white)?\s*(?:jacket|hoodie|coat|shirt|jeans|cap|mask))\b', re.IGNORECASE)
LOCATION_REGEX = re.compile(r'\b(?:near|at|by|in|around)\s+(?:the\s+)?([a-zA-Z0-9\s]+(?:shelf|counter|aisle|entrance|exit|store|display|register|parking))\b', re.IGNORECASE)
ITEM_REGEX = re.compile(r'\b(iPhone|phone|watch|jewelry|ring|necklace|laptop|cash|tablet|camera)\b', re.IGNORECASE)

class WitnessProcessor:
    def __init__(self, model_name: str = "RuleBased-Witness-NER", model_version: str = "1.2.0"):
        self.model_name = model_name
        self.model_version = model_version

    def process_witness_statement(
        self,
        statement_text: str,
        evidence_id: str,
        base_timestamp: Optional[datetime] = None
    ) -> List[ObservationCreate]:
        observations: List[ObservationCreate] = []
        base_dt = base_timestamp or datetime.now(timezone.utc)

        # 1. Parse time references
        time_match = TIME_REGEX.search(statement_text)
        time_raw = None
        parsed_dt = None
        time_window_min = None
        time_window_max = None

        if time_match:
            time_raw = time_match.group(0)
            try:
                # Try parsing relative to base_dt date
                time_part = date_parser.parse(time_raw).time()
                parsed_dt = datetime.combine(base_dt.date(), time_part, tzinfo=base_dt.tzinfo or timezone.utc)
                time_window_min = parsed_dt - timedelta(minutes=10)
                time_window_max = parsed_dt + timedelta(minutes=10)
            except Exception:
                parsed_dt = base_dt
        else:
            time_raw = "Time unspecified in statement"
            parsed_dt = base_dt
            time_window_min = None
            time_window_max = None

        # 2. Extract clothing & person mentions
        clothing_match = CLOTHING_REGEX.search(statement_text)
        clothing_desc = clothing_match.group(1).strip() if clothing_match else "Unspecified clothing"

        # 3. Extract location mentions
        loc_match = LOCATION_REGEX.search(statement_text)
        loc_desc = loc_match.group(1).strip() if loc_match else "Unspecified location"

        # Observation for the observed individual
        observations.append(
            ObservationCreate(
                evidence_id=evidence_id,
                department=Department.INVESTIGATION,
                observation_type=ObservationType.ENTITY_EXTRACTED,
                raw_data={
                    "entity_category": "PERSON",
                    "clothing": clothing_desc,
                    "location_reported": loc_desc,
                    "statement_excerpt": statement_text[:200],
                },
                observed_time_raw=time_raw,
                observed_time_parsed=parsed_dt,
                time_confidence=TimeConfidence.APPROXIMATE,
                time_source="witness_statement",
                time_reliability=TimeReliability.MEDIUM,
                time_window_min=time_window_min,
                time_window_max=time_window_max,
                location_label=loc_desc,
                observation_confidence=0.72,
                evidence_quality=EvidenceQuality.MEDIUM,
                model_name=self.model_name,
                model_version=self.model_version
            )
        )

        # 4. Check for mentioned items
        item_match = ITEM_REGEX.search(statement_text)
        if item_match:
            item_name = item_match.group(1).strip()
            observations.append(
                ObservationCreate(
                    evidence_id=evidence_id,
                    department=Department.INVESTIGATION,
                    observation_type=ObservationType.ENTITY_EXTRACTED,
                    raw_data={
                        "entity_category": "ITEM",
                        "item_name": item_name,
                        "context": "Reported seen or discussed by witness"
                    },
                    observed_time_raw=time_raw,
                    observed_time_parsed=parsed_dt,
                    time_confidence=TimeConfidence.APPROXIMATE,
                    time_source="witness_statement",
                    time_reliability=TimeReliability.MEDIUM,
                    time_window_min=time_window_min,
                    time_window_max=time_window_max,
                    location_label=loc_desc,
                    observation_confidence=0.68,
                    evidence_quality=EvidenceQuality.MEDIUM,
                    model_name=self.model_name,
                    model_version=self.model_version
                )
            )

        return observations

witness_processor = WitnessProcessor()
