from app.models.enums import CaseStatus
from fastapi import HTTPException, status

ALLOWED_TRANSITIONS = {
    CaseStatus.CREATED: [CaseStatus.EVIDENCE_COLLECTION, CaseStatus.CLOSED],
    CaseStatus.EVIDENCE_COLLECTION: [CaseStatus.ANALYSIS, CaseStatus.CREATED, CaseStatus.CLOSED],
    CaseStatus.ANALYSIS: [CaseStatus.RECONSTRUCTION, CaseStatus.EVIDENCE_COLLECTION, CaseStatus.CLOSED],
    CaseStatus.RECONSTRUCTION: [CaseStatus.UNDER_REVIEW, CaseStatus.ANALYSIS, CaseStatus.CLOSED],
    CaseStatus.UNDER_REVIEW: [CaseStatus.CLOSED, CaseStatus.RECONSTRUCTION, CaseStatus.ANALYSIS],
    CaseStatus.CLOSED: [CaseStatus.UNDER_REVIEW], # Reopening
}

def validate_case_status_transition(current_status: CaseStatus, next_status: CaseStatus) -> None:
    if current_status == next_status:
        return
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if next_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Illegal case state transition from '{current_status.value}' to '{next_status.value}'. Allowed next states: {[s.value for s in allowed]}"
        )
