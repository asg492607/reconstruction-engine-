from datetime import datetime, timedelta
from typing import Optional, List
from app.models.enums import Significance, GapConflictType

def score_time_discrepancy(
    time_a: Optional[datetime],
    time_b: Optional[datetime],
    incident_window_start: Optional[datetime] = None,
    incident_window_end: Optional[datetime] = None
) -> Significance:
    if not time_a or not time_b:
        return Significance.MEDIUM

    delta = abs((time_a - time_b).total_seconds())

    # If within incident window
    in_incident_window = False
    if incident_window_start and incident_window_end:
        if (incident_window_start <= time_a <= incident_window_end) or (incident_window_start <= time_b <= incident_window_end):
            in_incident_window = True

    # Sub-minute variance
    if delta <= 120: # under 2 minutes
        return Significance.LOW if not in_incident_window else Significance.MEDIUM
    elif delta <= 600: # 2 to 10 minutes
        return Significance.HIGH if in_incident_window else Significance.MEDIUM
    else:
        return Significance.CRITICAL if in_incident_window else Significance.HIGH
