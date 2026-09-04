from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.enums import EntityType, IdentityStatus

class CandidateEntityCreate(BaseModel):
    entity_type: EntityType = EntityType.PERSON
    label: str # e.g. "P1", "V1", "ITEM-PHONE"
    description: Dict[str, Any] = {}
    first_observed: Optional[datetime] = None
    last_observed: Optional[datetime] = None
    identity_status: IdentityStatus = IdentityStatus.CANDIDATE
    identity_note: Optional[str] = None

class CandidateEntityLinkResponse(BaseModel):
    id: str
    case_id: str
    observation_id: str
    candidate_entity_id: str
    link_confidence: float
    link_evidence: Dict[str, Any]
    link_method: str
    is_human_confirmed: bool
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CandidateEntityResponse(BaseModel):
    id: str
    case_id: str
    entity_type: EntityType
    label: str
    description: Dict[str, Any]
    first_observed: Optional[datetime] = None
    last_observed: Optional[datetime] = None
    identity_status: IdentityStatus
    identity_note: Optional[str] = None
    created_at: datetime
    links: List[CandidateEntityLinkResponse] = []

    model_config = ConfigDict(from_attributes=True)

class EntityLinkCreate(BaseModel):
    observation_id: str
    link_confidence: float = 0.75
    link_evidence: Dict[str, Any] = {}
    link_method: str = "clothing_similarity"
