from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.enums import TargetType, VerificationAction

class VerificationResponse(BaseModel):
    id: str
    case_id: str
    target_type: TargetType
    target_id: str
    action: VerificationAction
    note: Optional[str] = None
    corrected_data: Optional[Dict[str, Any]] = None
    verified_by: str
    verified_at: datetime

    model_config = ConfigDict(from_attributes=True)

class VerificationActionRequest(BaseModel):
    action: VerificationAction = VerificationAction.ACCEPTED
    note: Optional[str] = None
    corrected_data: Optional[Dict[str, Any]] = None

class PendingVerificationsResponse(BaseModel):
    pending_observations: List[Dict[str, Any]] = []
    pending_findings: List[Dict[str, Any]] = []
    pending_entity_links: List[Dict[str, Any]] = []
