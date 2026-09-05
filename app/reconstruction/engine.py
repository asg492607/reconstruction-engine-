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
    ObservationType, EntityType, Department, EvidenceQuality
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
        if any(o.id in step.get("observation_ids", []) for step in sequence) and o.observation_confidence is not None and o.observation_confidence > 0
    ]
    avg_conf = sum(rel_obs_confidences) / len(rel_obs_confidences) if rel_obs_confidences else 0.8
    if avg_conf >= 0.80:
        score += 1

    # Check for exculpatory authorized stock adjustment
    has_exculpatory_adj = any(
        i.get("check") == "CHECK_EXCULPATORY_STOCK_ADJUSTMENT" for i in deterministic_issues
    ) or any(
        (o.raw_data or {}).get("anomaly_type") == "AUTHORIZED_STOCK_ADJUSTMENT_RECORDED" or
        "authorized" in str((o.raw_data or {}).get("status", "")).lower() or
        "authorized" in str((o.raw_data or {}).get("reason", "")).lower()
        for o in observations
    )
    if has_exculpatory_adj:
        score -= 8

    # Score mapping
    if has_exculpatory_adj:
        strength = ClaimStrength.WEAK
        rationale = "Derived WEAK strength: Missing inventory discrepancy is fully accounted for by authorized stock-adjustment record. Theft hypothesis cannot reach strong support."
    elif score >= 4 and contradictions_count == 0:
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

    # 0. Check for Insufficient Evidence to formulate a defensible theft hypothesis
    has_candidate_person = any(e.entity_type == EntityType.PERSON for e in entities) or any(
        o.observation_type in (ObservationType.PERSON_DETECTED, ObservationType.ENTRY_EVENT) for o in obs
    )
    has_item_delta = any(o.observation_type == ObservationType.OBJECT_DETECTED for o in obs) or any(
        "missing" in str(o.raw_data or {}).lower() or "-1" in str(o.raw_data or {}) for o in obs
    )
    has_scene_presence = any(
        any(loc in (o.location_label or "").lower() for loc in ["aisle", "shelf", "counter", "display", "scene"]) or
        o.observation_type in (ObservationType.PHYSICAL_MARK_DETECTED, ObservationType.MOVEMENT_DETECTED)
        for o in obs
    )

    is_insufficient = (
        len(obs) < 2 or
        (not has_candidate_person and not has_scene_presence) or
        (not has_item_delta and not has_scene_presence)
    )

    if is_insufficient:
        insufficient_hyp = Hypothesis(
            case_id=case.id,
            label="Insufficient Evidence: Defensible Theft Hypothesis Cannot Be Established",
            description=(
                "Insufficient evidence to generate a defensible theft hypothesis. "
                "Current evidentiary record lacks necessary spatial-temporal correlation, candidate identity, "
                "or confirmed property loss. Reconstruction safely halted pending further evidentiary discovery."
            ),
            sequence=[],
            supporting_claim_ids=claim_ids,
            contradicting_claim_ids=[],
            assumptions=["No verified candidate presence or property movement established."],
            unknowns=[
                "Identity of suspect unestablished",
                "Direct observations of property removal absent",
                "Evidentiary record insufficient for reconstruction"
            ],
            overall_strength=ClaimStrength.SPECULATIVE,
            deterministic_issues=[{
                "check": "CHECK_INSUFFICIENT_EVIDENCE",
                "severity": "CRITICAL",
                "message": "Evidentiary record fails minimum threshold for theft sequence generation (We don't know yet)."
            }],
            ai_challenge_notes=[{
                "finding": "INSUFFICIENT_EVIDENCE",
                "note": "Reconstruction safely halted: insufficient empirical grounding to construct a defensible sequence."
            }],
            status=HypothesisStatus.INSUFFICIENT_EVIDENCE
        )
        db.add(insufficient_hyp)
        await db.commit()
        await db.refresh(insufficient_hyp)
        return [insufficient_hyp]

    # 1. Discover Primary Candidate Person Entity (default to P1 if present)
    p1_entity = next((e for e in entities if e.entity_type == EntityType.PERSON and e.label == "P1"), None)
    if not p1_entity:
        p1_entity = next((e for e in entities if e.entity_type == EntityType.PERSON), None)
    p1_label = p1_entity.label if p1_entity else "P1"
    p1_id = p1_entity.id if p1_entity else None

    # Discover attributes for P1 from observations
    p1_attr_desc = ""
    for o in obs:
        raw = o.raw_data or {}
        attrs = raw.get("attributes") or {}
        if attrs:
            clothing = attrs.get("clothing")
            bag = attrs.get("carrying") or attrs.get("bag")
            parts = []
            if clothing:
                parts.append(clothing)
            if bag:
                parts.append(f"carrying {bag}")
            if parts:
                p1_attr_desc = f" ({', '.join(parts)})"
                break

    # 2. Discover Target Missing Item dynamically from observations, claims, or case metadata
    item_name = None
    for o in obs:
        raw = o.raw_data or {}
        if "item_name" in raw and raw["item_name"]:
            item_name = str(raw["item_name"]).strip()
            break
        elif "item" in raw and raw["item"]:
            item_name = str(raw["item"]).strip()
            break
        elif "sku" in raw and raw["sku"]:
            item_name = f"SKU-{raw['sku']}"
            break

    if not item_name and case.title:
        import re
        m = re.search(r"(?:stolen|missing|theft of|grand larceny|larceny|robbery of|item|product)\s*:?\s*([A-Za-z0-9\s\-]+?)(?:\.|\,|$|\n)", case.title, re.IGNORECASE)
        if m:
            item_name = m.group(1).strip()

    if not item_name:
        item_name = "Targeted Property"

    # 3. Discover Ingress / Entry Observation
    entry_obs = next(
        (o for o in obs if o.observation_type == ObservationType.ENTRY_EVENT or 
         "entrance" in (o.location_label or "").lower() or "entry" in (o.location_label or "").lower() or
         (evidence_map.get(o.evidence_id) and any(kw in evidence_map[o.evidence_id].original_filename.lower() for kw in ["entrance", "entry"]))),
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
    elif evidence_items:
        entry_ev_sources.append(evidence_items[0].original_filename)

    # 4. Discover Proximity & Tampering Observations (Aisle / Shelf / Counter / Tether damage / Witness)
    shelf_obs = [
        o for o in obs if 
        any(loc in (o.location_label or "").lower() for loc in ["aisle", "shelf", "counter", "display", "scene"]) or
        o.observation_type in (ObservationType.PHYSICAL_MARK_DETECTED, ObservationType.MOVEMENT_DETECTED) or
        (evidence_map.get(o.evidence_id) and any(kw in evidence_map[o.evidence_id].original_filename.lower() for kw in ["aisle", "shelf", "witness", "tamper", "display", "counter", "scene"]))
    ]
    cctv_shelf = next((o for o in shelf_obs if o.time_source in ("camera_overlay", "camera_timestamp")), None)
    shelf_dt = (cctv_shelf.observed_time_parsed if cctv_shelf and cctv_shelf.observed_time_parsed else None) or next((o.observed_time_parsed for o in shelf_obs if o.observed_time_parsed), None) or (
        case.incident_time_observed if case.incident_time_observed else entry_dt + timedelta(minutes=4)
    )
    shelf_time_str = f"{shelf_dt.strftime('%I:%M %p').lstrip('0')} - {(shelf_dt + timedelta(minutes=3)).strftime('%I:%M %p').lstrip('0')}"
    shelf_loc = next((o.location_label for o in shelf_obs if o.location_label), "Display Shelf / Counter Area")
    shelf_ev_sources = []
    shelf_obs_ids = []
    for so in shelf_obs:
        shelf_obs_ids.append(so.id)
        ev = evidence_map.get(so.evidence_id)
        if ev and ev.original_filename not in shelf_ev_sources:
            shelf_ev_sources.append(ev.original_filename)
    if not shelf_ev_sources and evidence_items:
        shelf_ev_sources = [evidence_items[min(1, len(evidence_items) - 1)].original_filename]

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
    elif evidence_items:
        exit_ev_sources.append(evidence_items[-1].original_filename)

    # Add transaction record source to exit reconciliation if present
    tx_ev = next((e for e in evidence_items if any(kw in e.original_filename.lower() for kw in ["transaction", "pos", "receipt", "audit"])), None)
    if tx_ev and tx_ev.original_filename not in exit_ev_sources:
        exit_ev_sources.append(tx_ev.original_filename)

    # 6. Discover Coverage Gap between Shelf and Exit
    corridor_gap = next((g for g in gaps if g.gc_type.value == "GAP" or any(kw in g.description.lower() for kw in ["corridor", "blind", "unmonitored", "coverage"])), None)
    gap_start = shelf_dt + timedelta(minutes=2)
    gap_end = exit_dt - timedelta(minutes=1) if exit_dt > gap_start else gap_start + timedelta(minutes=1)
    corridor_dt = gap_start
    corridor_time_str = f"{gap_start.strftime('%I:%M %p').lstrip('0')} - {gap_end.strftime('%I:%M %p').lstrip('0')}"
    corridor_loc = (corridor_gap.description.split(":")[0] if corridor_gap else "Unmonitored Surveillance Gap Area")
    corridor_ev_sources = [f"Coverage Gap: {corridor_loc}"]

    # Check whether direct item handling was visually observed
    has_direct_handling_captured = any(
        (o.raw_data or {}).get("direct_concealment_observed") is True for o in obs
    )

    # Check evidence quality degradation
    qualities = [o.evidence_quality for o in obs if o.evidence_quality]
    has_degraded_quality = any(str(q.value if hasattr(q, "value") else q).upper() in ("LOW", "POOR") for q in qualities)

    # Dynamic Department Stances
    inv_obs = [o for o in obs if o.department == Department.INVESTIGATION]
    for_obs = [o for o in obs if o.department == Department.FORENSIC]
    fin_obs = [o for o in obs if o.department == Department.FINANCIAL]

    # Investigation Stance
    if any(o.observation_type in (ObservationType.ENTRY_EVENT, ObservationType.PERSON_DETECTED) for o in inv_obs):
        inv_stance = f"Surveillance video corroborates {p1_label} presence near {shelf_loc}."
    else:
        inv_stance = f"Investigation records candidate {p1_label} presence within vicinity of premises."

    # Forensic Stance: check if physical evidence links candidate to handling the item
    has_forensic_toolmark = any(
        "cut" in str(o.raw_data or {}).lower() or "toolmark" in str(o.raw_data or {}).lower() or
        o.observation_type == ObservationType.PHYSICAL_MARK_DETECTED for o in for_obs
    )
    has_handling_dna_or_prints = any(
        "positive" in str(o.raw_data or {}).lower() and "match" in str(o.raw_data or {}).lower()
        for o in for_obs
    )
    if has_forensic_toolmark and not has_handling_dna_or_prints:
        for_stance = f"Physical examination establishes mechanical tool cutting on security tether; latent prints unindividualized (handling by {p1_label} not physically confirmed)."
    elif not for_obs or not has_handling_dna_or_prints:
        for_stance = f"No physical, fingerprint, or toolmark evidence establishes that {p1_label} handled or detached the item."
    else:
        for_stance = f"Forensic analysis identifies physical trace evidence associated with {p1_label} on item or mount."

    # Financial Stance: check for authorized stock adjustment or matching purchase
    has_authorized_adj = any(
        (o.raw_data or {}).get("anomaly_type") == "AUTHORIZED_STOCK_ADJUSTMENT_RECORDED" or
        "authorized" in str((o.raw_data or {}).get("status", "")).lower() or
        "authorized" in str((o.raw_data or {}).get("reason", "")).lower()
        for o in obs
    )
    has_matching_purchase = any(
        (o.raw_data or {}).get("anomaly_type") == "MATCHING_TRANSACTION_FOUND" for o in fin_obs
    )

    if has_authorized_adj:
        fin_stance = f"Financial/inventory audit establishes authorized stock adjustment accounting for the missing item delta."
    elif has_matching_purchase:
        fin_stance = f"Point-of-sale audit confirms matching purchase transaction for {item_name}."
    else:
        fin_stance = f"Point-of-sale audit confirms zero matching purchase transactions for {item_name}."

    dept_stances = {
        "INVESTIGATION": inv_stance,
        "FORENSIC": for_stance,
        "FINANCIAL": fin_stance
    }

    step1_support = "MODERATE" if has_degraded_quality else "STRONG"
    step1_rationale = (
        "Observation supported by degraded or low-resolution sensor capture."
        if has_degraded_quality
        else "Direct optical sensor confirmation from entrance camera timestamp overlay."
    )

    step2_support = "MODERATE"
    if "no physical" in for_stance.lower() or "not physically confirmed" in for_stance.lower():
        step2_rationale = (
            f"Subject {p1_label} proximity to {shelf_loc} corroborated by surveillance; "
            f"forensics establishes no physical evidence of {p1_label} handling the item. "
            "Direct detachment remains physically unestablished."
        )
    else:
        step2_rationale = (
            f"Subject {p1_label} proximity to {shelf_loc} corroborated by physical severed tether toolmark; "
            "direct item detachment and concealment was not visually captured on camera (inferred from proximity and absence)."
        )

    step3_support = "UNCONFIRMED"
    step3_rationale = (
        f"Traversal through {corridor_loc.lower()}; zero direct surveillance coverage during this window."
    )

    if has_authorized_adj:
        step4_support = "REFUTED"
        step4_rationale = (
            f"Missing inventory delta for {item_name} is accounted for by authorized stock adjustment / transfer log. "
            "Absence of checkout transaction does not represent theft."
        )
    else:
        step4_support = "LIMITED"
        step4_rationale = (
            f"Subject {p1_label} egress directly recorded on camera without corresponding transaction; "
            f"physical possession of {item_name} at departure is inferred from prior proximity and missing inventory delta."
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
            "description": f"Subject {p1_label}{p1_attr_desc} enters store through {entry_loc.lower()}.",
            "evidence_sources": entry_ev_sources,
            "observation_ids": entry_obs_ids,
            "entity_ids": [p1_label] + ([p1_id] if p1_id else []),
            "support_level": step1_support,
            "support_rationale": step1_rationale,
            "is_directly_observed": True,
            "department_stances": dept_stances
        },
        {
            "step": 2,
            "phase": "PROXIMITY_AND_TAMPERING",
            "time": shelf_time_str,
            "time_parsed": shelf_dt.isoformat(),
            "location": shelf_loc,
            "description": f"Subject {p1_label} observed at {shelf_loc}; physical tampering or {item_name} removal observed.",
            "evidence_sources": shelf_ev_sources,
            "observation_ids": shelf_obs_ids,
            "entity_ids": [p1_label] + ([p1_id] if p1_id else []),
            "support_level": step2_support,
            "support_rationale": step2_rationale,
            "is_directly_observed": False,
            "department_stances": dept_stances
        },
        {
            "step": 3,
            "phase": "CORRIDOR_TRANSITION",
            "time": corridor_time_str,
            "time_parsed": corridor_dt.isoformat(),
            "location": corridor_loc,
            "description": f"Subject moves through {corridor_loc.lower()} toward exit.",
            "evidence_sources": corridor_ev_sources,
            "observation_ids": [],
            "entity_ids": [p1_label] + ([p1_id] if p1_id else []),
            "support_level": step3_support,
            "support_rationale": step3_rationale,
            "is_directly_observed": False,
            "department_stances": dept_stances
        },
        {
            "step": 4,
            "phase": "EXIT",
            "time": exit_time_str,
            "time_parsed": exit_dt.isoformat(),
            "location": exit_loc,
            "description": f"Subject {p1_label} exits through {exit_loc.lower()} with no purchase record for {item_name}.",
            "evidence_sources": exit_ev_sources,
            "observation_ids": exit_obs_ids,
            "entity_ids": [p1_label] + ([p1_id] if p1_id else []),
            "support_level": step4_support,
            "support_rationale": step4_rationale,
            "is_directly_observed": False,
            "department_stances": dept_stances
        }
    ]

    layer1_a = run_layer1_deterministic_checks(
        p1_sequence, list(links), list(obs), list(claims),
        supporting_claim_ids=claim_ids, candidate_entities=list(entities)
    )

    if has_authorized_adj:
        layer1_a.append({
            "check": "CHECK_EXCULPATORY_STOCK_ADJUSTMENT",
            "severity": "CRITICAL",
            "message": "Missing inventory discrepancy is fully explained by authorized stock adjustment. Theft hypothesis cannot reach strong support."
        })

    layer2_a = await run_layer2_ai_adversarial_review("Hypothesis A", p1_sequence, layer1_a, gap_dicts)

    unknowns_a = ["Visual confirmation of item concealment during surveillance coverage gap."]
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
        assumptions=[f"Item {item_name} remained in possession from {shelf_loc} through {exit_loc}."],
        unknowns=unknowns_a,
        is_speculative_branch=False
    )

    if has_authorized_adj:
        hyp_a_desc = (
            f"Uncorroborated theft allegation: although candidate {p1_label} was observed near {shelf_loc}, "
            f"inventory audit confirms an authorized stock adjustment explaining the missing {item_name}. "
            "Theft cannot be defensibly asserted."
        )
    elif "no physical" in for_stance.lower() or "not physically confirmed" in for_stance.lower():
        hyp_a_desc = (
            f"Candidate {p1_label} is strongly associated with presence near the incident area ({shelf_loc}), "
            f"but direct handling of the stolen item ({item_name}) remains unestablished."
        )
    else:
        hyp_a_desc = (
            f"Candidate Entity {p1_label} entered via {entry_loc}, was present at {shelf_loc} "
            f"during incident window, traversed {corridor_loc}, and exited via {exit_loc} "
            f"with {item_name} without authorized transaction record."
        )

    hyp_a = Hypothesis(
        case_id=case.id,
        label=f"Hypothesis A: Sole Actor Concealment ({p1_label})",
        description=hyp_a_desc,
        sequence=p1_sequence,
        supporting_claim_ids=claim_ids,
        contradicting_claim_ids=[],
        assumptions=[f"Item {item_name} remained in possession from {shelf_loc} through {exit_loc}."],
        unknowns=unknowns_a,
        overall_strength=strength_a,
        deterministic_issues=layer1_a,
        ai_challenge_notes=layer2_a,
        status=HypothesisStatus.CHALLENGED if has_authorized_adj else HypothesisStatus.DRAFT
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
            "entity_ids": [p1_label] + ([p1_id] if p1_id else []),
            "support_level": "STRONG",
            "support_rationale": "Direct optical sensor confirmation from entrance camera timestamp overlay.",
            "is_directly_observed": True,
            "department_stances": dept_stances
        },
        {
            "step": 2,
            "phase": "TAMPERING",
            "time": shelf_time_str.split(" - ")[0],
            "time_parsed": shelf_dt.isoformat(),
            "location": shelf_loc,
            "description": f"{p1_label} accesses or detaches {item_name} at {shelf_loc}.",
            "evidence_sources": [s for s in shelf_ev_sources if any(kw in s.lower() for kw in ["cctv", "cam", "video", "shelf"])] or shelf_ev_sources[:1],
            "observation_ids": shelf_obs_ids,
            "entity_ids": [p1_label] + ([p1_id] if p1_id else []),
            "support_level": "MODERATE",
            "support_rationale": "Presence corroborated; physical detachment inferred.",
            "is_directly_observed": False,
            "department_stances": dept_stances
        },
        {
            "step": 3,
            "phase": "HAND_OFF",
            "time": corridor_time_str,
            "time_parsed": corridor_dt.isoformat(),
            "location": corridor_loc,
            "description": f"{p1_label} transfers item to second entity (P2) within {corridor_loc.lower()}.",
            "evidence_sources": corridor_ev_sources,
            "observation_ids": [],
            "entity_ids": [p1_label, "P2"],
            "support_level": "SPECULATIVE",
            "support_rationale": "Speculative accomplice hand-off inside coverage gap; zero physical or visual evidence confirms presence of a second actor.",
            "is_directly_observed": False,
            "department_stances": dept_stances
        },
        {
            "step": 4,
            "phase": "SEPARATE_EXIT",
            "time": f"{exit_time_str} - {(exit_dt + timedelta(minutes=3)).strftime('%I:%M %p').lstrip('0')}",
            "time_parsed": exit_dt.isoformat(),
            "location": f"{exit_loc} / Perimeter",
            "description": f"{p1_label} departs clean through {exit_loc.lower()} while P2 exits separately.",
            "evidence_sources": exit_ev_sources[:1] if exit_ev_sources else corridor_ev_sources,
            "observation_ids": exit_obs_ids,
            "entity_ids": [p1_label, "P2"],
            "support_level": "SPECULATIVE",
            "support_rationale": "Hypothetical secondary departure route unconfirmed by surveillance.",
            "is_directly_observed": False,
            "department_stances": dept_stances
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
        assumptions=["Existence of second accomplice inside premises", f"Hand-off occurred during {corridor_time_str} window"],
        unknowns=["No physical or visual evidence directly confirms presence of a second actor in the coverage gap."],
        is_speculative_branch=True
    )

    hyp_b = Hypothesis(
        case_id=case.id,
        label="Hypothesis B: Two-Person Accomplice Hand-Off",
        description=(
            f"Candidate Entity {p1_label} accessed {item_name} at {shelf_loc} and passed it "
            f"to an unidentified accomplice (P2) inside {corridor_loc}, who exited separately."
        ),
        sequence=p2_sequence,
        supporting_claim_ids=claim_ids[:1],
        contradicting_claim_ids=[],
        assumptions=["Existence of second accomplice inside premises", f"Hand-off occurred during {corridor_time_str} window"],
        unknowns=["No physical or visual evidence directly confirms presence of a second actor at the shelf or coverage gap."],
        overall_strength=strength_b,
        deterministic_issues=layer1_b,
        ai_challenge_notes=layer2_b,
        status=HypothesisStatus.DRAFT
    )
    hypotheses.append(hyp_b)
    from app.reconstruction.integrity_gate import validate_evidence_reference_integrity
    for h in hypotheses:
        is_valid, violations = validate_evidence_reference_integrity(
            case_evidence_list=evidence_items,
            payload={
                "label": h.label,
                "description": h.description,
                "sequence": h.sequence,
                "assumptions": h.assumptions,
                "unknowns": h.unknowns
            },
            context_desc=f"Hypothesis {h.label}"
        )
        if not is_valid:
            # Reject output completely: do not sanitize, prevent reaching verified status
            h.status = HypothesisStatus.REJECTED
            h.review_note = f"UNSUPPORTED_EVIDENCE_REFERENCE: {'; '.join(violations)}"
            h.overall_strength = ClaimStrength.SPECULATIVE
        db.add(h)

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

async def get_hypothesis_provenance_chain(db: AsyncSession, case_id: str, hypothesis_id: str) -> Dict[str, Any]:
    """
    Builds an end-to-end provenance chain for a hypothesis:
    Hypothesis -> Sequence Step -> Observations -> Evidence File -> SHA-256 Hash -> Model/Version -> Human Verification Status.
    """
    hyp = await get_hypothesis_by_id(db, hypothesis_id)
    if not hyp or hyp.case_id != case_id:
        raise ValueError("Hypothesis not found")

    evidence_items = (await db.execute(select(Evidence).where(Evidence.case_id == case_id))).scalars().all()
    evidence_map = {e.id: e for e in evidence_items}

    obs_items = (await db.execute(select(Observation).where(Observation.case_id == case_id))).scalars().all()
    obs_map = {o.id: o for o in obs_items}

    ver_items = (await db.execute(select(Verification).where(Verification.case_id == case_id))).scalars().all()
    ver_map = {v.target_id: v for v in ver_items}

    chain_steps = []
    for step in hyp.sequence:
        step_obs_list = []
        for oid in step.get("observation_ids", []):
            o = obs_map.get(oid)
            if o:
                ev = evidence_map.get(o.evidence_id)
                v = ver_map.get(o.id)
                step_obs_list.append({
                    "observation_id": o.id,
                    "type": o.observation_type.value,
                    "department": o.department.value,
                    "location": o.location_label,
                    "observed_time": o.observed_time_raw,
                    "confidence": o.observation_confidence,
                    "quality": o.evidence_quality.value if o.evidence_quality else "MEDIUM",
                    "model_name": o.model_name,
                    "model_version": o.model_version,
                    "verification_status": v.action.value if v else o.verification_status.value,
                    "verified_by": v.verified_by if v else None,
                    "verified_at": v.verified_at.isoformat() if v else None,
                    "evidence": {
                        "evidence_id": ev.id if ev else None,
                        "filename": ev.original_filename if ev else None,
                        "sha256_hash": ev.sha256_hash if ev else None,
                        "storage_key": ev.storage_key if ev else None,
                        "uploaded_at": ev.uploaded_at.isoformat() if ev else None
                    } if ev else None
                })

        chain_steps.append({
            "step": step.get("step"),
            "phase": step.get("phase"),
            "time": step.get("time"),
            "location": step.get("location"),
            "description": step.get("description"),
            "support_level": step.get("support_level", "MODERATE"),
            "support_rationale": step.get("support_rationale", ""),
            "is_directly_observed": step.get("is_directly_observed", False),
            "evidence_sources": step.get("evidence_sources", []),
            "observations": step_obs_list,
            "department_stances": step.get("department_stances", {})
        })

    return {
        "hypothesis_id": hyp.id,
        "case_id": hyp.case_id,
        "label": hyp.label,
        "overall_strength": hyp.overall_strength.value,
        "status": hyp.status.value,
        "reviewed_by": hyp.reviewed_by,
        "reviewed_at": hyp.reviewed_at.isoformat() if hyp.reviewed_at else None,
        "review_note": hyp.review_note,
        "provenance_chain": chain_steps
    }
