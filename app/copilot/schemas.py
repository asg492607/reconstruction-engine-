from typing import Optional, List
from pydantic import BaseModel

class CopilotQueryRequest(BaseModel):
    query: str
    mode: Optional[str] = "AUTO" # "AUTO", "EVIDENCE", "REASONING"

class CopilotResponse(BaseModel):
    answer: str
    mode: str # "EVIDENCE", "REASONING", "SYSTEM_SAFEGUARD"
    evidence_references: List[str] = []
    confidence_note: str
    uncertainty_note: str
    disclaimer: str
    is_prohibited_query: bool = False
