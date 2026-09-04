from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.enums import (
    Department, ObservationType, TimeConfidence, TimeReliability,
    EvidenceQuality, VerificationStatus
)

class ObservationCreate(BaseModel):
    evidence_id: str
    department: Department = Department.INVESTIGATION
    observation_type: ObservationType
    raw_data: Dict[str, Any] = {}
    observed_time_raw: Optional[str] = None
    observed_time_parsed: Optional[datetime] = None
    time_confidence: TimeConfidence = TimeConfidence.UNKNOWN
    time_source: Optional[str] = None
    time_reliability: TimeReliability = TimeReliability.UNKNOWN
    estimated_clock_offset: Optional[str] = None
    time_window_min: Optional[datetime] = None
    time_window_max: Optional[datetime] = None
    location_label: Optional[str] = None
    bounding_box: Optional[Dict[str, Any]] = None
    frame_reference: Optional[str] = None
    observation_confidence: float = 0.8
    evidence_quality: EvidenceQuality = EvidenceQuality.MEDIUM
    model_name: str = "InvestigationEngine"
    model_version: str = "1.0.0"
    derived_from_observation_id: Optional[str] = None

class ObservationResponse(BaseModel):
    id: str
    evidence_id: str
    case_id: str
    department: Department
    observation_type: ObservationType
    raw_data: Dict[str, Any]
    observed_time_raw: Optional[str] = None
    observed_time_parsed: Optional[datetime] = None
    time_confidence: TimeConfidence
    time_source: Optional[str] = None
    time_reliability: TimeReliability
    estimated_clock_offset: Optional[str] = None
    time_window_min: Optional[datetime] = None
    time_window_max: Optional[datetime] = None
    location_label: Optional[str] = None
    bounding_box: Optional[Dict[str, Any]] = None
    frame_reference: Optional[str] = None
    observation_confidence: float
    evidence_quality: EvidenceQuality
    model_name: str
    model_version: str
    derived_from_observation_id: Optional[str] = None
    verification_status: VerificationStatus
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
