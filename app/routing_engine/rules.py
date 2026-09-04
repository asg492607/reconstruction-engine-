from typing import List
from app.models.enums import EvidenceType, Department

ROUTING_RULES = {
    EvidenceType.CCTV: [Department.INVESTIGATION, Department.FORENSIC],
    EvidenceType.IMAGE: [Department.FORENSIC, Department.INVESTIGATION],
    EvidenceType.AUDIO: [Department.INVESTIGATION],
    EvidenceType.WITNESS_STATEMENT: [Department.INVESTIGATION],
    EvidenceType.INVENTORY_RECORD: [Department.INVESTIGATION, Department.FINANCIAL],
    EvidenceType.TRANSACTION_RECORD: [Department.FINANCIAL, Department.INVESTIGATION],
    EvidenceType.VEHICLE_RECORD: [Department.INVESTIGATION],
    EvidenceType.FORENSIC_REPORT: [Department.FORENSIC, Department.INVESTIGATION],
    EvidenceType.DOCUMENT: [Department.INVESTIGATION, Department.FORENSIC, Department.FINANCIAL],
    EvidenceType.OTHER: [Department.INVESTIGATION, Department.FORENSIC, Department.FINANCIAL],
}

def determine_authorized_departments(evidence_type: EvidenceType) -> List[str]:
    """
    Returns the canonical list of authorized department names for a given evidence type.
    """
    departments = ROUTING_RULES.get(evidence_type, [Department.INVESTIGATION])
    return [d.value for d in departments]
