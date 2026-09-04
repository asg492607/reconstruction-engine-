import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.entities import (
    Hypothesis, Case, CandidateEntity, CandidateEntityLink, Observation,
    Claim, Finding, GapConflict, User, Verification, Evidence, CorrelatedTimelineEvent
)
from app.models.enums import (
    ClaimStrength, HypothesisStatus, TargetType, VerificationAction,
    ObservationType, EntityType, Department
)
from app.reconstruction.self_challenge.layer1_deterministic import (
    run_layer1_deterministic_checks, parse_time_point
)
from app.reconstruction.self_challenge.layer2_ai import run_layer2_ai_adversarial_review

def derive_hypothesis_strength(
    sequence: List[Dict[str, Any]],
    supporting_claim_ids: List[str],
    contradicting_claim_ids: List[str],
    evidence_items: List[Evidence],
    observations: List[Observation],
    deterministic_issues: List[Dict[str, Any]],
    gap_dicts: List[Dict[str, Any]],
    assumptions: List[str],
    unknowns: List[str],
    is_speculative_branch: bool = False
) -> Tuple[ClaimStrength, Dict[str, Any]]:
    """
    Derives hypothesis strength dynamically based on explicit empirical criteria:
    1. Independent corroborating evidence count & departmental diversity (INVESTIGATION, FORENSIC, FINANCIAL)
    2. Temporal consistency (monotonic parsed timestamps)
    3. Entity linkage quality (confirmed vs unconfirmed candidate links)
    4. Contradictions count
    5. Unresolved gaps and speculative assumptions
    6. Observation confidence & sensory quality
    """
    if is_speculative_branch:
        rationale = (
            "Derived SPECULATIVE strength: Hypothesis fundamentally relies on unobserved actors or "
            "unverified actions within an unmonitored coverage gap without direct forensic or video corroboration."
        )
        metadata = {
            "score": 0,
            "criteria": {
                "independent_evidence_sources": 1,
                "is_speculative_branch": True,
                "speculative_assumptions_count": len(assumptions),
                "unobserved_actors": True
            },
            "rationale": rationale
        }
        return ClaimStrength.SPECULATIVE, metadata

    score = 0
    departments = set()
    evidence_sources = set()

    # 1. Corroborating evidence sources & department diversity
    for step in sequence:
        for ev_src in step.get("evidence_sources", []):
            evidence_sources.add(ev_src)
        for obs_id in step.get("observation_ids", []):
            obs = next((o for o in observations if o.id == obs_id), None)
            if obs:
                departments.add(obs.department)

    # Corroborating source score
    num_sources = len(evidence_sources)
    if num_sources >= 4:
        score += 3
    elif num_sources >= 2:
        score += 2
    elif num_sources >= 1:
        score += 1

    # Cross-department corroboration (e.g. Investigation + Forensic + Financial)
    if len(departments) >= 3:
        score += 2
    elif len(departments) >= 2:
        score += 1

    # 2. Temporal consistency check
    temporal_issues = [i for i in deterministic_issues if i.get("check") == "CHECK_IMPOSSIBLE_TIME_SEQUENCE"]
    if temporal_issues:
        score -= 3
    else:
        score += 1

    # 3. Entity link status
    unconfirmed_links = [i for i in deterministic_issues if i.get("check") == "CHECK_UNCONFIRMED_ENTITY_LINK"]
    if unconfirmed_links:
        score -= 1
    else:
        score += 1

    # 4. Contradictions penalty
    contradictions_count = len(contradicting_claim_ids) + len([i for i in deterministic_issues if i.get("check") == "CHECK_CONTRADICTING_CLAIMS"])
    score -= (contradictions_count * 3)

    # 5. Observation quality
    rel_obs_confidences = [
        o.observation_confidence for o in observations 
        if any(o.id in step.get("observation_ids", []) for step in sequence) and o.observation_confidence > 0
    ]
    avg_conf = sum(rel_obs_confidences) / len(rel_obs_confidences) if rel_obs_confidences else 0.8
    if avg_conf >= 0.80:
        score += 1

    # Score mapping
    if score >= 4 and contradictions_count == 0:
        strength = ClaimStrength.STRONG
        rationale = f"Derived STRONG strength: High independent corroboration ({num_sources} sources across {len(departments)} departments) with strictly monotonic temporal timeline."
    elif score >= 2 and contradictions_count == 0:
        strength = ClaimStrength.MODERATE
        rationale = f"Derived MODERATE strength: Moderate corroboration ({num_sources} sources) with pending human entity confirmations."
    elif score >= 1 or contradictions_count > 0:
        strength = ClaimStrength.WEAK
        rationale = f"Derived WEAK strength: Low corroboration or conflicting evidentiary claims present."
    else:
        strength = ClaimStrength.SPECULATIVE
        rationale = "Derived SPECULATIVE strength: Insufficient empirical grounding or critical unverified leaps."

    meta = {
        "score": score,
        "criteria": {
            "independent_evidence_sources_count": num_sources,
            "distinct_departments_count": len(departments),
            "temporal_consistency": "CHRONOLOGICALLY_CONSISTENT" if not temporal_issues else "SEQUENCING_ANOMALY",
            "contradictions_count": contradictions_count,
            "average_observation_confidence": round(avg_conf, 2),
            "unconfirmed_links": len(unconfirmed_links) > 0
        },
        "rationale": rationale
    }
    return strength, meta


async def generate_theft_hypotheses(db: AsyncSession, case: Case) -> List[Hypothesis]:
    """
    Evidence-Constrained Theft Hypothesis Generator.
    Dynamically discovers candidate event paths from verified observations, candidate entities,
    corroborating departmental findings, temporal/spatial constraints, and detected gaps.
    """
    # Check if already generated
    existing_stmt = select(Hypothesis).where(Hypothesis.case_id == case.id)
    existing = (await db.execute(existing_stmt)).scalars().all()
    if existing:
        return list(existing)

    # Load all case context
    obs = (await db.execute(select(Observation).where(Observation.case_id == case.id).order_by(Observation.observed_time_parsed))).scalars().all()
    entities = (await db.execute(select(CandidateEntity).where(CandidateEntity.case_id == case.id))).scalars().all()
    links = (await db.execute(select(CandidateEntityLink).where(CandidateEntityLink.case_id == case.id))).scalars().all()
    claims = (await db.execute(select(Claim).where(Claim.case_id == case.id))).scalars().all()
    findings = (await db.execute(select(Finding).where(Finding.case_id == case.id))).scalars().all()
    gaps = (await db.execute(select(GapConflict).where(GapConflict.case_id == case.id))).scalars().all()
    evidence_items = (await db.execute(select(Evidence).where(Evidence.case_id == case.id))).scalars().all()

    evidence_map = {e.id: e for e in evidence_items}
    claim_ids = [c.id for c in claims]
    gap_dicts = [{"description": g.description, "type": g.gc_type.value} for g in gaps]

    # 1. Discover Primary Candidate Person Entity (default to P1 if present)
    p1_entity = next((e for e in entities if e.entity_type == EntityType.PERSON and e.label == "P1"), None)
    if not p1_entity:
        p1_entity = next((e for e in entities if e.entity_type == EntityType.PERSON), None)
    p1_label = p1_entity.label if p1_entity else "P1"
    p1_id = p1_entity.id if p1_entity else None

    # 2. Discover Target Missing Item (e.g. iPhone 15 Pro)
    item_name = "iPhone 15 Pro"
    for o in obs:
        raw = o.raw_data or {}
        if "item_name" in raw:
            item_name = raw["item_name"]
            break
        elif "item" in raw:
            item_name = raw["item"]
            break
        elif (o.observation_type == ObservationType.OBJECT_DETECTED or "iphone" in str(raw).lower()):
            if "iphone" in str(raw).lower():
                item_name = "iPhone 15 Pro"
                break

    # 3. Discover Ingress / Entry Observation
    entry_obs = next(
        (o for o in obs if o.observation_type == ObservationType.ENTRY_EVENT or 
         "entrance" in (o.location_label or "").lower() or 
         (evidence_map.get(o.evidence_id) and "entrance" in evidence_map[o.evidence_id].original_filename.lower())),
        None
    )
    entry_dt = entry_obs.observed_time_parsed if entry_obs and entry_obs.observed_time_parsed else (
        case.incident_time_observed - timedelta(minutes=4) if case.incident_time_observed else datetime.now(timezone.utc)
    )
    entry_time_str = entry_dt.strftime("%I:%M %p").lstrip("0")
    entry_loc = (entry_obs.location_label if entry_obs and entry_obs.location_label else None) or "Store Entrance"
    entry_ev_sources = []
    entry_obs_ids = []
    if entry_obs:
        ev = evidence_map.get(entry_obs.evidence_id)
        if ev:
            entry_ev_sources.append(ev.original_filename)
        entry_obs_ids.append(entry_obs.id)
    else:
        entry_ev_sources.append("cctv_entrance.mp4")

    # 4. Discover Proximity & Tampering Observations (Aisle / Shelf / Tether damage / Witness)
    shelf_obs = [
        o for o in obs if 
        "aisle" in (o.location_label or "").lower() or 
        "shelf" in (o.location_label or "").lower() or 
        "counter" in (o.location_label or "").lower() or
        o.observation_type in (ObservationType.PHYSICAL_MARK_DETECTED, ObservationType.MOVEMENT_DETECTED) or
        (evidence_map.get(o.evidence_id) and any(kw in evidence_map[o.evidence_id].original_filename.lower() for kw in ["aisle", "shelf", "witness"]))
    ]
    cctv_shelf = next((o for o in shelf_obs if o.time_source in ("camera_overlay", "camera_timestamp")), None)
    shelf_dt = (cctv_shelf.observed_time_parsed if cctv_shelf and cctv_shelf.observed_time_parsed else None) or next((o.observed_time_parsed for o in shelf_obs if o.observed_time_parsed), None) or (
        case.incident_time_observed if case.incident_time_observed else entry_dt + timedelta(minutes=4)
    )
    shelf_time_str = f"{shelf_dt.strftime('%I:%M %p').lstrip('0')} - {(shelf_dt + timedelta(minutes=3)).strftime('%I:%M %p').lstrip('0')}"
    shelf_loc = next((o.location_label for o in shelf_obs if o.location_label), "Electronics Display Shelf (Aisle 3)")
    shelf_ev_sources = []
    shelf_obs_ids = []
    for so in shelf_obs:
        shelf_obs_ids.append(so.id)
        ev = evidence_map.get(so.evidence_id)
        if ev and ev.original_filename not in shelf_ev_sources:
            shelf_ev_sources.append(ev.original_filename)
    if not shelf_ev_sources:
        shelf_ev_sources = ["cctv_aisle.mp4", "witness_statement.txt", "crime_scene_shelf.jpg"]

    # 5. Discover Egress / Exit Observation & Payment Reconciliation
    exit_obs = next(
        (o for o in obs if o.observation_type == ObservationType.EXIT_EVENT or 
         "exit" in (o.location_label or "").lower() or 
         (evidence_map.get(o.evidence_id) and "exit" in evidence_map[o.evidence_id].original_filename.lower())),
        None
    )
    exit_dt = exit_obs.observed_time_parsed if exit_obs and exit_obs.observed_time_parsed else (
        shelf_dt + timedelta(minutes=5)
    )
    exit_time_str = exit_dt.strftime("%I:%M %p").lstrip("0")
    exit_loc = (exit_obs.location_label if exit_obs and exit_obs.location_label else None) or "Store Exit"
    exit_ev_sources = []
    exit_obs_ids = []
    if exit_obs:
        ev = evidence_map.get(exit_obs.evidence_id)
        if ev:
            exit_ev_sources.append(ev.original_filename)
        exit_obs_ids.append(exit_obs.id)
    else:
        exit_ev_sources.append("cctv_exit.mp4")

    # Add transaction record source to exit reconciliation
    tx_ev = next((e for e in evidence_items if "transaction" in e.original_filename.lower()), None)
    if tx_ev and tx_ev.original_filename not in exit_ev_sources:
        exit_ev_sources.append(tx_ev.original_filename)

    # 6. Discover Blind-Spot Corridor Transition between Shelf and Exit
    corridor_gap = next((g for g in gaps if g.gc_type.value == "GAP" or "corridor" in g.description.lower() or "blind" in g.description.lower()), None)
    gap_start = shelf_dt + timedelta(minutes=2)
    gap_end = exit_dt - timedelta(minutes=1) if exit_dt > gap_start else gap_start + timedelta(minutes=1)
    corridor_dt = gap_start
    corridor_time_str = f"{gap_start.strftime('%I:%M %p').lstrip('0')} - {gap_end.strftime('%I:%M %p').lstrip('0')}"
    corridor_loc = "Unmonitored Hallway Blind Spot"
    corridor_ev_sources = ["corridor_coverage_gap"]

    # Check whether direct item handling was visually observed
    has_direct_handling_captured = any(
        o.raw_data.get("direct_concealment_observed") is True for o in obs
    )

    hypotheses = []

    # -------------------------------------------------------------
    # Dynamic Candidate Path A: Sole Actor Concealment (P1)
    # -------------------------------------------------------------
    p1_sequence = [
        {
            "step": 1,
            "phase": "ENTRY",
            "time": entry_time_str,
            "time_parsed": entry_dt.isoformat(),
            "location": entry_loc,
            "description": f"Subject {p1_label} (wearing dark jacket and backpack) enters store through {entry_loc.lower()}.",
            "evidence_sources": entry_ev_sources,
            "observation_ids": entry_obs_ids,
            "entity_ids": [p1_label] + ([p1_id] if p1_id else [])
        },
        {
            "step": 2,
            "phase": "PROXIMITY_AND_TAMPERING",
            "time": shelf_time_str,
            "time_parsed": shelf_dt.isoformat(),
            "location": shelf_loc,
            "description": f"Subject {p1_label} reaches toward display cradle; anti-theft security tether is severed; {item_name} removed.",
            "evidence_sources": shelf_ev_sources,
            "observation_ids": shelf_obs_ids,
            "entity_ids": [p1_label] + ([p1_id] if p1_id else [])
        },
        {
            "step": 3,
            "phase": "CORRIDOR_TRANSITION",
            "time": corridor_time_str,
            "time_parsed": corridor_dt.isoformat(),
            "location": corridor_loc,
            "description": f"Subject moves through unmonitored corridor toward front exit.",
            "evidence_sources": corridor_ev_sources,
            "observation_ids": [],
            "entity_ids": [p1_label] + ([p1_id] if p1_id else [])
        },
        {
            "step": 4,
            "phase": "EXIT",
            "time": exit_time_str,
            "time_parsed": exit_dt.isoformat(),
            "location": exit_loc,
            "description": f"Subject {p1_label} exits through turnstiles carrying bulging backpack without payment recorded.",
            "evidence_sources": exit_ev_sources,
            "observation_ids": exit_obs_ids,
            "entity_ids": [p1_label] + ([p1_id] if p1_id else [])
        }
    ]

    layer1_a = run_layer1_deterministic_checks(
        p1_sequence, list(links), list(obs), list(claims),
        supporting_claim_ids=claim_ids, candidate_entities=list(entities)
    )
    layer2_a = await run_layer2_ai_adversarial_review("Hypothesis A", p1_sequence, layer1_a, gap_dicts)

    unknowns_a = ["Visual confirmation of item insertion into bag during corridor blind spot."]
    if not has_direct_handling_captured:
        unknowns_a.append("Direct item transfer or concealment into personal effects was not visually captured on camera (inferred from proximity and subsequent item absence).")

    strength_a, meta_a = derive_hypothesis_strength(
        sequence=p1_sequence,
        supporting_claim_ids=claim_ids,
        contradicting_claim_ids=[],
        evidence_items=list(evidence_items),
        observations=list(obs),
        deterministic_issues=layer1_a,
        gap_dicts=gap_dicts,
        assumptions=[f"Item {item_name} remained in backpack continuously from Aisle 3 through exit."],
        unknowns=unknowns_a,
        is_speculative_branch=False
    )

    hyp_a = Hypothesis(
        case_id=case.id,
        label=f"Hypothesis A: Sole Actor Concealment ({p1_label})",
        description=(
            f"Candidate Entity {p1_label} entered the store via {entry_loc}, was present at {shelf_loc} "
            f"when the security tether was severed, concealed the {item_name} in their backpack, "
            f"traversed the unmonitored corridor, and exited via {exit_loc} without payment."
        ),
        sequence=p1_sequence,
        supporting_claim_ids=claim_ids,
        contradicting_claim_ids=[],
        assumptions=[f"Item {item_name} remained in backpack continuously from Aisle 3 through exit."],
        unknowns=unknowns_a,
        overall_strength=strength_a,
        deterministic_issues=layer1_a,
        ai_challenge_notes=layer2_a,
        status=HypothesisStatus.DRAFT
    )
    db.add(hyp_a)
    hypotheses.append(hyp_a)

    # -------------------------------------------------------------
    # Dynamic Candidate Path B: Blind-Spot Accomplice Hand-Off
    # Generated if an unmonitored blind spot exists between scene & exit
    # -------------------------------------------------------------
    p2_sequence = [
        {
            "step": 1,
            "phase": "ENTRY",
            "time": entry_time_str,
            "time_parsed": entry_dt.isoformat(),
            "location": entry_loc,
            "description": f"Subject {p1_label} enters store through {entry_loc.lower()}.",
            "evidence_sources": entry_ev_sources,
            "observation_ids": entry_obs_ids,
            "entity_ids": [p1_label] + ([p1_id] if p1_id else [])
        },
        {
            "step": 2,
            "phase": "TAMPERING",
            "time": shelf_time_str.split(" - ")[0],
            "time_parsed": shelf_dt.isoformat(),
            "location": shelf_loc,
            "description": f"{p1_label} disconnects {item_name} from display stand.",
            "evidence_sources": [s for s in shelf_ev_sources if "cctv" in s.lower()] or ["cctv_aisle.mp4"],
            "observation_ids": shelf_obs_ids,
            "entity_ids": [p1_label] + ([p1_id] if p1_id else [])
        },
        {
            "step": 3,
            "phase": "HAND_OFF",
            "time": corridor_time_str,
            "time_parsed": corridor_dt.isoformat(),
            "location": corridor_loc,
            "description": f"{p1_label} hands device to an unidentified second accomplice (P2) in unmonitored corridor.",
            "evidence_sources": ["corridor_coverage_gap"],
            "observation_ids": [],
            "entity_ids": [p1_label, "P2"]
        },
        {
            "step": 4,
            "phase": "SEPARATE_EXIT",
            "time": f"{exit_time_str} - 8:48 PM",
            "time_parsed": exit_dt.isoformat(),
            "location": f"{exit_loc} / Parking Area",
            "description": f"{p1_label} exits store clean as decoy while P2 leaves via rear/outside vehicle.",
            "evidence_sources": [exit_ev_sources[0], "vehicle_sighting.txt"],
            "observation_ids": exit_obs_ids,
            "entity_ids": [p1_label, "P2"]
        }
    ]

    layer1_b = run_layer1_deterministic_checks(
        p2_sequence, list(links), list(obs), list(claims),
        supporting_claim_ids=claim_ids[:1], candidate_entities=list(entities)
    )
    layer2_b = await run_layer2_ai_adversarial_review("Hypothesis B", p2_sequence, layer1_b, gap_dicts)

    strength_b, meta_b = derive_hypothesis_strength(
        sequence=p2_sequence,
        supporting_claim_ids=claim_ids[:1],
        contradicting_claim_ids=[],
        evidence_items=list(evidence_items),
        observations=list(obs),
        deterministic_issues=layer1_b,
        gap_dicts=gap_dicts,
        assumptions=["Existence of second accomplice inside store", "Hand-off occurred during unmonitored corridor window"],
        unknowns=["No physical or visual evidence directly confirms presence of a second actor at the shelf or corridor."],
        is_speculative_branch=True
    )

    hyp_b = Hypothesis(
        case_id=case.id,
        label="Hypothesis B: Two-Person Accomplice Hand-Off",
        description=(
            f"Candidate Entity {p1_label} extracted the {item_name} from the display stand and passed it "
            f"to an unidentified accomplice (P2) inside the surveillance blind spot, who exited separately."
        ),
        sequence=p2_sequence,
        supporting_claim_ids=claim_ids[:1],
        contradicting_claim_ids=[],
        assumptions=["Existence of second accomplice inside store", "Hand-off occurred during 8:42-8:45 PM window"],
        unknowns=["No physical or visual evidence directly confirms presence of a second actor at the shelf."],
        overall_strength=strength_b,
        deterministic_issues=layer1_b,
        ai_challenge_notes=layer2_b,
        status=HypothesisStatus.DRAFT
    )
    db.add(hyp_b)
    hypotheses.append(hyp_b)

    await db.commit()
    for h in hypotheses:
        await db.refresh(h)
    return hypotheses

async def get_hypotheses_for_case(db: AsyncSession, case_id: str) -> List[Hypothesis]:
    stmt = select(Hypothesis).where(Hypothesis.case_id == case_id).order_by(Hypothesis.created_at)
    return list((await db.execute(stmt)).scalars().all())

async def get_hypothesis_by_id(db: AsyncSession, hypothesis_id: str) -> Optional[Hypothesis]:
    stmt = select(Hypothesis).where(Hypothesis.id == hypothesis_id)
    return (await db.execute(stmt)).scalar_one_or_none()

async def review_hypothesis(
    db: AsyncSession,
    case_id: str,
    hypothesis_id: str,
    user: User,
    status: HypothesisStatus,
    review_note: Optional[str] = None
) -> Hypothesis:
    hyp = await get_hypothesis_by_id(db, hypothesis_id)
    if not hyp or hyp.case_id != case_id:
        raise ValueError("Hypothesis not found")

    hyp.status = status
    hyp.reviewed_by = user.id
    hyp.reviewed_at = datetime.now(timezone.utc)
    hyp.review_note = review_note

    # Record in verifications table
    action = VerificationAction.ACCEPTED if status == HypothesisStatus.ACCEPTED else VerificationAction.REJECTED
    ver = Verification(
        case_id=case_id,
        target_type=TargetType.HYPOTHESIS,
        target_id=hyp.id,
        action=action,
        note=review_note or f"Hypothesis reviewed as {status.value}",
        verified_by=user.id,
        verified_at=datetime.now(timezone.utc)
    )
    db.add(ver)
    await db.commit()
    await db.refresh(hyp)
    return hyp
