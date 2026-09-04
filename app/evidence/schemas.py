from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.enums import EvidenceType, ProcessingStatus, Department

class EvidenceResponse(BaseModel):
    id: str
    case_id: str
    evidence_type: EvidenceType
    original_filename: str
    storage_key: str
    file_size_bytes: int
    sha256_hash: str
    mime_type: Optional[str] = None
    uploaded_by: str
    uploaded_at: datetime
    is_classified: bool
    classification_notes: Optional[str] = None
    authorized_departments: List[str] = []
    processing_status: ProcessingStatus
    metadata_json: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)

class EvidenceClassifyRequest(BaseModel):
    evidence_type: Optional[EvidenceType] = None
    authorized_departments: Optional[List[Department]] = None
    classification_notes: Optional[str] = None

class EvidenceProvenanceResponse(BaseModel):
    evidence_id: str
    original_filename: str
    sha256_hash: str
    uploaded_at: datetime
    observations_count: int
    observations: List[Dict[str, Any]] = []
