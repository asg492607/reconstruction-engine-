from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.enums import ClaimStrength, HypothesisStatus

class HypothesisResponse(BaseModel):
    id: str
    case_id: str
    label: str
    description: Optional[str] = None
    sequence: List[Dict[str, Any]]
    supporting_claim_ids: List[str] = []
    contradicting_claim_ids: List[str] = []
    assumptions: List[str] = []
    unknowns: List[str] = []
    overall_strength: ClaimStrength
    deterministic_issues: List[Dict[str, Any]] = []
    ai_challenge_notes: List[Dict[str, Any]] = []
    status: HypothesisStatus
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HypothesisReviewRequest(BaseModel):
    status: HypothesisStatus = HypothesisStatus.ACCEPTED
    review_note: Optional[str] = None
