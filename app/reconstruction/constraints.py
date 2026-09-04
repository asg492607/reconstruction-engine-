from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class TheftConstraints:
    entry_required: bool = True
    proximity_to_item_required: bool = True
    item_disappearance_required: bool = True
    exit_required: bool = True
    no_valid_transaction: bool = True

@dataclass
class EvidencePathStep:
    step_number: int
    step_type: str # "ENTRY", "PROXIMITY_TO_ITEM", "ITEM_DISAPPEARANCE", "EXIT"
    description: str
    event_time: Optional[datetime] = None
    location: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    entity_ids: List[str] = field(default_factory=list)
