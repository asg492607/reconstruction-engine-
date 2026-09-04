from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.enums import Department, GeneratedBy, VerificationStatus, ClaimStrength

class FindingCreate(BaseModel):
    department: Department = Department.INVESTIGATION
    finding_type: str # e.g. "MOVEMENT_PATH", "PHYSICAL_MATCH", "TRANSACTION_ANOMALY"
    description: str
    observation_ids: List[str] = []
    entity_ids: List[str] = []
    time_start: Optional[datetime] = None
    time_end: Optional[datetime] = None
    detection_confidence: float = 0.85
    corroboration_count: int = 1
    corroboration_sources: List[str] = []
    generated_by: GeneratedBy = GeneratedBy.AI

class FindingResponse(BaseModel):
    id: str
    case_id: str
    department: Department
    finding_type: str
    description: str
    observation_ids: List[str] = []
    entity_ids: List[str] = []
    time_start: Optional[datetime] = None
    time_end: Optional[datetime] = None
    detection_confidence: float
    corroboration_count: int
    corroboration_sources: List[str] = []
    is_contradicted_by: List[str] = []
    generated_by: GeneratedBy
    verification_status: VerificationStatus
    verified_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClaimCreate(BaseModel):
    claim_text: str
    finding_ids: List[str] = []
    claim_strength: ClaimStrength = ClaimStrength.STRONG

class ClaimResponse(BaseModel):
    id: str
    case_id: str
    claim_text: str
    finding_ids: List[str] = []
    claim_strength: ClaimStrength
    contradicted_by_finding_ids: List[str] = []
    is_verified: bool
    verified_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
