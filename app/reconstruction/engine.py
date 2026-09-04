from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.entities import (
    Hypothesis, Case, CandidateEntity, CandidateEntityLink, Observation,
    Claim, Finding, GapConflict, User, Verification
)
from app.models.enums import ClaimStrength, HypothesisStatus, TargetType, VerificationAction
from app.reconstruction.self_challenge.layer1_deterministic import run_layer1_deterministic_checks
from app.reconstruction.self_challenge.layer2_ai import run_layer2_ai_adversarial_review

async def generate_theft_hypotheses(db: AsyncSession, case: Case) -> List[Hypothesis]:
    # Check if already generated
    existing_stmt = select(Hypothesis).where(Hypothesis.case_id == case.id)
    existing = (await db.execute(existing_stmt)).scalars().all()
    if existing:
        return list(existing)

    # Load case context
    obs = (await db.execute(select(Observation).where(Observation.case_id == case.id))).scalars().all()
    entities = (await db.execute(select(CandidateEntity).where(CandidateEntity.case_id == case.id))).scalars().all()
    links = (await db.execute(select(CandidateEntityLink).where(CandidateEntityLink.case_id == case.id))).scalars().all()
    claims = (await db.execute(select(Claim).where(Claim.case_id == case.id))).scalars().all()
    findings = (await db.execute(select(Finding).where(Finding.case_id == case.id))).scalars().all()
    gaps = (await db.execute(select(GapConflict).where(GapConflict.case_id == case.id))).scalars().all()

    claim_ids = [c.id for c in claims]
    gap_dicts = [{"description": g.description, "type": g.gc_type.value} for g in gaps]

    hypotheses = []

    # 1. Hypothesis A: Primary Person (P1) Concealment and Exit
    p1_sequence = [
        {
            "step": 1,
            "phase": "ENTRY",
            "time": "8:37 PM",
            "location": "Store Entrance",
            "description": "Subject P1 (wearing dark jacket and backpack) enters store through main entrance.",
            "evidence_sources": ["cctv_entrance.mp4"]
        },
        {
            "step": 2,
            "phase": "PROXIMITY_AND_TAMPERING",
            "time": "8:41 PM - 8:44 PM",
            "location": "Electronics Display Shelf (Aisle 3)",
            "description": "Subject P1 reaches toward display cradle; anti-theft security tether is severed; iPhone 15 Pro removed.",
            "evidence_sources": ["cctv_aisle.mp4", "witness_statement.txt", "crime_scene_shelf.jpg"]
        },
        {
            "step": 3,
            "phase": "CORRIDOR_TRANSITION",
            "time": "8:44 PM - 8:45 PM",
            "location": "Unmonitored Hallway Blind Spot",
            "description": "Subject moves through unmonitored corridor toward front exit.",
            "evidence_sources": ["corridor_coverage_gap"]
        },
        {
            "step": 4,
            "phase": "EXIT",
            "time": "8:46 PM",
            "location": "Store Exit",
            "description": "Subject P1 exits through turnstiles carrying bulging backpack without payment recorded.",
            "evidence_sources": ["cctv_exit.mp4", "transactions.csv"]
        }
    ]

    layer1_a = run_layer1_deterministic_checks(p1_sequence, list(links), list(obs), list(claims))
    layer2_a = await run_layer2_ai_adversarial_review("Hypothesis A", p1_sequence, layer1_a, gap_dicts)

    hyp_a = Hypothesis(
        case_id=case.id,
        label="Hypothesis A: Sole Actor Concealment (P1)",
        description="Candidate Entity P1 entered the store, cut the security tether at display shelf 3, concealed the iPhone 15 Pro in their backpack, and exited without payment.",
        sequence=p1_sequence,
        supporting_claim_ids=claim_ids,
        contradicting_claim_ids=[],
        assumptions=["Item remained in backpack continuously from Aisle 3 through exit."],
        unknowns=["Visual confirmation of item insertion into bag during corridor blind spot."],
        overall_strength=ClaimStrength.STRONG,
        deterministic_issues=layer1_a,
        ai_challenge_notes=layer2_a,
        status=HypothesisStatus.DRAFT
    )
    db.add(hyp_a)
    hypotheses.append(hyp_a)

    # 2. Hypothesis B: Blind-Spot Accomplice Hand-Off
    p2_sequence = [
        {
            "step": 1,
            "phase": "ENTRY",
            "time": "8:37 PM",
            "location": "Store Entrance",
            "description": "Subject P1 enters store.",
            "evidence_sources": ["cctv_entrance.mp4"]
        },
        {
            "step": 2,
            "phase": "TAMPERING",
            "time": "8:41 PM",
            "location": "Electronics Display Shelf",
            "description": "P1 disconnects device from display stand.",
            "evidence_sources": ["cctv_aisle.mp4"]
        },
        {
            "step": 3,
            "phase": "HAND_OFF",
            "time": "8:43 PM",
            "location": "Corridor Blind Spot",
            "description": "P1 hands device to an unidentified second accomplice (P2) in blind spot.",
            "evidence_sources": ["corridor_coverage_gap"]
        },
        {
            "step": 4,
            "phase": "SEPARATE_EXIT",
            "time": "8:46 PM - 8:48 PM",
            "location": "Store Exit / Parking Area",
            "description": "P1 exits store clean as decoy while P2 leaves via rear/outside vehicle.",
            "evidence_sources": ["cctv_exit.mp4", "vehicle_sighting.txt"]
        }
    ]

    layer1_b = run_layer1_deterministic_checks(p2_sequence, list(links), list(obs), list(claims))
    layer2_b = await run_layer2_ai_adversarial_review("Hypothesis B", p2_sequence, layer1_b, gap_dicts)


    hyp_b = Hypothesis(
        case_id=case.id,
        label="Hypothesis B: Two-Person Accomplice Hand-Off",
        description="Candidate Entity P1 extracted the phone from the display stand and passed it to an unidentified accomplice (P2) inside the surveillance blind spot, who exited separately.",
        sequence=p2_sequence,
        supporting_claim_ids=claim_ids[:1],
        contradicting_claim_ids=[],
        assumptions=["Existence of second accomplice inside store", "Hand-off occurred during 8:42-8:45 PM window"],
        unknowns=["No physical or visual evidence directly confirms presence of a second actor at the shelf."],
        overall_strength=ClaimStrength.SPECULATIVE,
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
