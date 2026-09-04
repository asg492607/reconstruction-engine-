from typing import List, Dict, Any, Optional
from app.models.entities import CandidateEntityLink, Observation, Claim, Finding
from app.models.enums import VerificationStatus

def run_layer1_deterministic_checks(
    hypothesis_sequence: List[Dict[str, Any]],
    candidate_links: List[CandidateEntityLink],
    observations: List[Observation],
    claims: List[Claim]
) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    # 1. Check for unconfirmed entity links
    unconfirmed_links = [l for l in candidate_links if not l.is_human_confirmed]
    if unconfirmed_links:
        issues.append({
            "check": "CHECK_UNCONFIRMED_ENTITY_LINK",
            "passed": False,
            "severity": "HIGH",
            "issue": f"{len(unconfirmed_links)} candidate entity linkage(s) relied upon in reconstruction have not been verified by a human investigator.",
            "recommendation": "Require investigator confirmation of P1 clothing similarity before treating entity path as fact."
        })

    # 2. Check for unverified observations
    pending_obs = [o for o in observations if o.verification_status == VerificationStatus.PENDING]
    if pending_obs:
        issues.append({
            "check": "CHECK_UNVERIFIED_OBSERVATIONS",
            "passed": False,
            "severity": "MEDIUM",
            "issue": f"Hypothesis sequence relies on {len(pending_obs)} AI-generated observation(s) currently in PENDING review status.",
            "recommendation": "Review and accept raw CCTV and witness detections."
        })

    # 3. Check for single-source dependencies
    for c in claims:
        if len(c.finding_ids) <= 1:
            issues.append({
                "check": "CHECK_SINGLE_SOURCE_CLAIM",
                "passed": False,
                "severity": "MEDIUM",
                "issue": f"Claim '{c.claim_text[:60]}...' is supported by only a single analytical finding.",
                "recommendation": "Seek independent corroborating evidence (e.g. cross-correlate CCTV with physical forensic report)."
            })

    # 4. Check impossible time sequence
    times = []
    for step in hypothesis_sequence:
        t_str = step.get("time")
        if t_str:
            times.append(t_str)

    # If any timestamp appears out of order
    for i in range(len(times) - 1):
        if times[i] > times[i + 1]:
            issues.append({
                "check": "CHECK_IMPOSSIBLE_TIME_SEQUENCE",
                "passed": False,
                "severity": "CRITICAL",
                "issue": f"Sequence anomaly: Step at {times[i]} precedes earlier step at {times[i+1]}.",
                "recommendation": "Verify camera clock synchronization and timestamp offsets."
            })

    return issues
