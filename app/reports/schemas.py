from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict

class ReportResponse(BaseModel):
    id: str
    case_id: str
    version: int
    report_data: Dict[str, Any]
    generated_by: str
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
