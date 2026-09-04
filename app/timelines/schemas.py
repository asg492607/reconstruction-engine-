from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.enums import Department, TimeConfidence

class SourceTimelineEventResponse(BaseModel):
    id: str
    source_timeline_id: str
    observation_id: Optional[str] = None
    event_type: str
    description: str
    observed_time_raw: Optional[str] = None
    event_time: Optional[datetime] = None
    time_confidence: TimeConfidence
    time_window_min: Optional[datetime] = None
    time_window_max: Optional[datetime] = None
    entity_ids: List[str] = []
    sequence_order: int

    model_config = ConfigDict(from_attributes=True)

class SourceTimelineResponse(BaseModel):
    id: str
    case_id: str
    source_label: str
    evidence_id: str
    department: Department
    created_at: datetime
    events: List[SourceTimelineEventResponse] = []

    model_config = ConfigDict(from_attributes=True)

class CorrelatedTimelineEventResponse(BaseModel):
    id: str
    case_id: str
    event_time: Optional[datetime] = None
    time_confidence: TimeConfidence
    time_window_min: Optional[datetime] = None
    time_window_max: Optional[datetime] = None
    description: str
    source_event_ids: List[str] = []
    supporting_evidence_ids: List[str] = []
    entity_ids: List[str] = []
    department: Department
    is_disputed: bool
    dispute_note: Optional[str] = None
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
