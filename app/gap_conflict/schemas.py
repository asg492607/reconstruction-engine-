from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.enums import GapConflictType, Significance

class GapConflictResponse(BaseModel):
    id: str
    case_id: str
    gc_type: GapConflictType
    description: str
    significance: Significance
    significance_reason: Optional[str] = None
    affected_evidence_ids: List[str] = []
    affected_observation_ids: List[str] = []
    affected_event_ids: List[str] = []
    affected_entity_ids: List[str] = []
    is_resolved: bool
    resolution_note: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class GapConflictResolveRequest(BaseModel):
    resolution_note: str
