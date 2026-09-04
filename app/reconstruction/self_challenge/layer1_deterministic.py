import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser
from app.models.entities import CandidateEntityLink, Observation, Claim
from app.models.enums import VerificationStatus

def parse_time_point(time_val: Any) -> Optional[datetime]:
    """
    Safely parses a time point, ISO string, or time range (e.g. '8:41 PM - 8:44 PM') into a datetime.
    For ranges, returns the start boundary for ordering.
    """
    if not time_val:
        return None
    if isinstance(time_val, datetime):
        return time_val if time_val.tzinfo else time_val.replace(tzinfo=timezone.utc)
    
    t_str = str(time_val).strip()
    # If range like '8:41 PM - 8:44 PM', pick first part
    if " - " in t_str:
        t_str = t_str.split(" - ")[0].strip()
    elif "-" in t_str and not re.search(r'\d{4}-\d{2}-\d{2}', t_str):
        t_str = t_str.split("-")[0].strip()

    try:
        dt = date_parser.parse(t_str)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        # Try extracting 12h or 24h time with regex
        match = re.search(r'\b(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\b', t_str)
        if match:
            try:
                dt = date_parser.parse(match.group(1))
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass
    return None

def run_layer1_deterministic_checks(
    hypothesis_sequence: List[Dict[str, Any]],
    candidate_links: List[CandidateEntityLink],
    observations: List[Observation],
    claims: List[Claim],
    supporting_claim_ids: Optional[List[str]] = None,
    candidate_entities: Optional[List[Any]] = None
) -> List[Dict[str, Any]]:
    """
    Layer 1: Deterministic Evidence & Consistency Validation.
    Evaluates only dependencies of this specific hypothesis:
    - Verifies temporal sequencing using parsed datetime comparisons
    - Checks whether entities referenced in this hypothesis have unconfirmed candidate links
    - Checks verification status of observations relied upon in this hypothesis
    - Checks single-source or contradictory claims tied to this hypothesis
    """
    issues: List[Dict[str, Any]] = []

    # 1. Identify relevant evidence sources / observation IDs / entity IDs for this hypothesis
    rel_obs_ids = set()
    rel_entity_labels = set()
    rel_entity_ids = set()
    for step in hypothesis_sequence:
        for obs_id in step.get("observation_ids", []):
            rel_obs_ids.add(obs_id)
        for ent in step.get("entity_ids", []):
            rel_entity_labels.add(str(ent))
            rel_entity_ids.add(str(ent))
        desc = step.get("description", "")
        # Look for P1, P2, V1 mentions
        for match in re.findall(r'\b(P\d+|V\d+|[A-Z]{1,3}-\w+)\b', desc):
            rel_entity_labels.add(match)

    entity_label_by_id = {}
    if candidate_entities:
        for e in candidate_entities:
            entity_label_by_id[e.id] = getattr(e, "label", str(e.id))
            if getattr(e, "label", None) in rel_entity_labels:
                rel_entity_ids.add(e.id)

    # Scoped unconfirmed links for entities involved in this hypothesis
    rel_links = [
        l for l in candidate_links 
        if (l.observation_id in rel_obs_ids) or 
           (l.candidate_entity_id in rel_entity_ids) or
           (entity_label_by_id.get(l.candidate_entity_id) in rel_entity_labels) or
           (getattr(l, "candidate_entity", None) and l.candidate_entity.label in rel_entity_labels) or
           (not rel_obs_ids and not rel_entity_labels)
    ]
    unconfirmed_links = [l for l in rel_links if not l.is_human_confirmed]
    if unconfirmed_links:
        issues.append({
            "check": "CHECK_UNCONFIRMED_ENTITY_LINK",
            "passed": False,
            "severity": "HIGH",
            "issue": f"{len(unconfirmed_links)} candidate entity linkage(s) relied upon in this hypothesis have not been verified by a human investigator.",
            "recommendation": "Require investigator confirmation of candidate linkages before treating this sequence as verified."
        })

    # 2. Check unverified observations scoped to this hypothesis
    rel_obs = [o for o in observations if (o.id in rel_obs_ids) or not rel_obs_ids]
    pending_obs = [o for o in rel_obs if o.verification_status == VerificationStatus.PENDING]
    if pending_obs:
        issues.append({
            "check": "CHECK_UNVERIFIED_OBSERVATIONS",
            "passed": False,
            "severity": "MEDIUM",
            "issue": f"Hypothesis sequence relies on {len(pending_obs)} observation(s) currently in PENDING review status.",
            "recommendation": "Review and accept raw sensory/departmental observations before finalizing."
        })

    # 3. Check claims supporting this hypothesis
    target_claims = [c for c in claims if not supporting_claim_ids or c.id in supporting_claim_ids]
    for c in target_claims:
        if len(c.finding_ids) <= 1:
            issues.append({
                "check": "CHECK_SINGLE_SOURCE_CLAIM",
                "passed": False,
                "severity": "MEDIUM",
                "issue": f"Claim '{c.claim_text[:60]}...' is supported by only a single analytical finding.",
                "recommendation": "Seek independent corroborating evidence across specialist departments."
            })

    # 4. Deterministic temporal chronology check with parsed datetimes
    parsed_sequence_times = []
    for step in hypothesis_sequence:
        t_parsed = parse_time_point(step.get("time_parsed") or step.get("time"))
        if t_parsed:
            parsed_sequence_times.append((step.get("time", str(t_parsed)), t_parsed, step.get("step", 0)))

    for i in range(len(parsed_sequence_times) - 1):
        curr_label, curr_dt, curr_step = parsed_sequence_times[i]
        next_label, next_dt, next_step = parsed_sequence_times[i + 1]
        if curr_dt > next_dt:
            issues.append({
                "check": "CHECK_IMPOSSIBLE_TIME_SEQUENCE",
                "passed": False,
                "severity": "CRITICAL",
                "issue": f"Temporal sequencing anomaly: Step {curr_step} at '{curr_label}' is recorded after Step {next_step} at '{next_label}'.",
                "recommendation": "Verify camera clock synchronization and timestamp offsets."
            })

    return issues
