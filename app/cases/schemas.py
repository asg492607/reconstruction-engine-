from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import CaseType, CaseStatus, Department, OffenseCategory, SpecificOffense

class CaseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    case_number: Optional[str] = None # Auto-generated if not supplied
    case_type: CaseType = CaseType.THEFT
    offense_category: Optional[OffenseCategory] = None
    specific_offense: Optional[SpecificOffense] = None
    incident_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    investigative_objectives: Optional[List[str]] = Field(default_factory=list)
    incident_location: Optional[str] = None
    incident_time_observed: Optional[datetime] = None
    incident_time_estimated: Optional[Dict[str, Any]] = None # {"min": "...", "max": "..."}

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[CaseStatus] = None
    offense_category: Optional[OffenseCategory] = None
    specific_offense: Optional[SpecificOffense] = None
    incident_context: Optional[Dict[str, Any]] = None
    investigative_objectives: Optional[List[str]] = None
    incident_location: Optional[str] = None
    incident_time_observed: Optional[datetime] = None
    incident_time_estimated: Optional[Dict[str, Any]] = None

class CaseAssign(BaseModel):
    user_id: str
    department: Department

class CaseSnapshotRequest(BaseModel):
    reason: Optional[str] = "Manual case state snapshot"

class CaseAssignmentResponse(BaseModel):
    id: str
    case_id: str
    user_id: str
    department: Department
    assigned_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class CaseResponse(BaseModel):
    id: str
    case_number: str
    title: str
    case_type: CaseType
    offense_category: Optional[OffenseCategory] = None
    specific_offense: Optional[SpecificOffense] = None
    incident_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    investigative_objectives: Optional[List[str]] = Field(default_factory=list)
    status: CaseStatus
    incident_location: Optional[str] = None
    incident_time_observed: Optional[datetime] = None
    incident_time_estimated: Optional[Dict[str, Any]] = None
    organization_id: Optional[str] = None
    created_by: str
    current_version: int
    created_at: datetime
    updated_at: datetime
    assignments: List[CaseAssignmentResponse] = []

    model_config = ConfigDict(from_attributes=True)

class CaseVersionResponse(BaseModel):
    id: str
    case_id: str
    version_number: int
    snapshot: Dict[str, Any]
    created_by: str
    created_at: datetime
    reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
