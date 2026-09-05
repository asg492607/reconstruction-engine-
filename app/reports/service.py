from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.entities import (
    Report, Case, Evidence, Observation, CandidateEntity, CandidateEntityLink,
    Finding, Claim, CorrelatedTimelineEvent, Hypothesis, GapConflict, Verification, User
)

async def generate_case_report(
    db: AsyncSession,
    case: Case,
    user: User
) -> Report:
    # 1. Fetch all data for the case
    ev_res = await db.execute(select(Evidence).where(Evidence.case_id == case.id))
    evidence_items = ev_res.scalars().all()

    obs_res = await db.execute(select(Observation).where(Observation.case_id == case.id))
    observations = obs_res.scalars().all()

    ent_res = await db.execute(select(CandidateEntity).where(CandidateEntity.case_id == case.id))
    entities = ent_res.scalars().all()

    links_res = await db.execute(select(CandidateEntityLink).where(CandidateEntityLink.case_id == case.id))
    links = links_res.scalars().all()

    claims_res = await db.execute(select(Claim).where(Claim.case_id == case.id))
    claims = claims_res.scalars().all()

    corr_res = await db.execute(
        select(CorrelatedTimelineEvent)
        .where(CorrelatedTimelineEvent.case_id == case.id)
        .order_by(CorrelatedTimelineEvent.event_time)
    )
    events = corr_res.scalars().all()

    hyp_res = await db.execute(select(Hypothesis).where(Hypothesis.case_id == case.id))
    hypotheses = hyp_res.scalars().all()

    gap_res = await db.execute(select(GapConflict).where(GapConflict.case_id == case.id))
    gaps = gap_res.scalars().all()

    ver_res = await db.execute(select(Verification).where(Verification.case_id == case.id))
    verifications = ver_res.scalars().all()

    # Determine report version
    v_res = await db.execute(select(func.count(Report.id)).where(Report.case_id == case.id))
    version_num = (v_res.scalar() or 0) + 1

    report_payload: Dict[str, Any] = {
        "report_metadata": {
            "title": f"Investigation Intelligence Report: {case.title}",
            "case_number": case.case_number,
            "case_id": case.id,
            "report_version": version_num,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by_user_id": user.id,
            "status": case.status.value,
        },
        "executive_summary": {
            "incident_overview": f"Investigation into {case.case_type.value.lower()} reported at {case.incident_location or 'premises'}: {case.title}.",
            "primary_hypothesis": hypotheses[0].label if hypotheses else "Insufficient evidence for reconstruction.",
            "overall_strength": hypotheses[0].overall_strength.value if hypotheses else "UNKNOWN",
            "total_evidence_sources": len(evidence_items),
            "total_observations": len(observations),
            "critical_gaps_identified": len([g for g in gaps if g.significance.value == "CRITICAL"]),
            "non_verdict_notice": "This platform produces an evidence-grounded reconstruction of factual observations, gaps, and competing hypotheses. It makes no autonomous assertion of legal guilt, statutory violation, or culpability. Final legal and procedural decisions remain exclusively with authorized human personnel."
        },
        "chain_of_custody_and_evidence": [
            {
                "evidence_id": e.id,
                "filename": e.original_filename,
                "type": e.evidence_type.value,
                "sha256_fingerprint": e.sha256_hash,
                "file_size_bytes": e.file_size_bytes,
                "authorized_departments": e.authorized_departments,
                "uploaded_at": e.uploaded_at.isoformat()
            }
            for e in evidence_items
        ],
        "correlated_timeline": [
            {
                "time": e.event_time.isoformat() if e.event_time else "Approximate",
                "description": e.description,
                "confidence": e.time_confidence.value,
                "supporting_evidence_ids": e.supporting_evidence_ids
            }
            for e in events
        ],
        "candidate_entities": [
            {
                "id": ent.id,
                "label": ent.label,
                "type": ent.entity_type.value,
                "status": ent.identity_status.value,
                "linked_observations_count": len([l for l in links if l.candidate_entity_id == ent.id]),
                "confirmed_links_count": len([l for l in links if l.candidate_entity_id == ent.id and l.is_human_confirmed])
            }
            for ent in entities
        ],
        "reconstructed_hypotheses": [
            {
                "label": h.label,
                "description": h.description,
                "overall_strength": h.overall_strength.value,
                "status": h.status.value,
                "sequence": h.sequence,
                "deterministic_issues_count": len(h.deterministic_issues),
                "ai_challenge_notes_count": len(h.ai_challenge_notes),
                "reviewed_by": h.reviewed_by
            }
            for h in hypotheses
        ],
        "gaps_and_conflicts": [
            {
                "type": g.gc_type.value,
                "significance": g.significance.value,
                "description": g.description,
                "is_resolved": g.is_resolved,
                "resolution_note": g.resolution_note
            }
            for g in gaps
        ],
        "human_verifications_count": len(verifications),
        "ai_disclosure_and_judicial_compliance": {
            "platform": "Reality Reconstruction Engine (RRE) v2.0",
            "disclosure_statement": (
                "This document was synthesized by an AI-assisted investigative platform. "
                "Original physical and digital evidence was preserved immutably with SHA-256 cryptographic verification. "
                "All entity linkages and hypothesis conclusions represent constrained analytical possibilities, "
                "not judicial verdicts. Determination of culpability and factual identity remains under exclusive "
                "human authority."
            ),
            "attesting_investigator": user.full_name or user.email,
            "attestation_timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

    report = Report(
        case_id=case.id,
        version=version_num,
        report_data=report_payload,
        generated_by=user.id,
        generated_at=datetime.now(timezone.utc)
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report

async def list_reports_for_case(db: AsyncSession, case_id: str) -> List[Report]:
    stmt = select(Report).where(Report.case_id == case_id).order_by(desc(Report.version))
    return list((await db.execute(stmt)).scalars().all())

async def get_report_by_id(db: AsyncSession, report_id: str) -> Optional[Report]:
    stmt = select(Report).where(Report.id == report_id)
    return (await db.execute(stmt)).scalar_one_or_none()
