import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entities import Evidence, Observation, Case
from app.models.enums import EvidenceType, ProcessingStatus, Department, ObservationType, VerificationStatus
from app.department_engines.framework.registry import engine_registry
from app.department_engines.framework.planner import dynamic_planner, DynamicAnalysisPlan
from app.department_engines.framework.base import (
    EngineContext,
    EngineExecutionRecord,
    EngineExecutionResult,
    ExecutionMode
)
from app.department_engines.framework.governance import resource_governor
from app.department_engines.framework.output_gate import output_gate, GateDecision
from app.observations.service import create_observation

logger = logging.getLogger(__name__)

# Execution Telemetry in-memory cache keyed by case_id
_CASE_EXECUTION_RECORDS: Dict[str, List[EngineExecutionRecord]] = {}
_CASE_EXECUTION_HISTORY: Dict[str, List[Dict[str, Any]]] = {}

def get_case_telemetry(case_id: str) -> List[Dict[str, Any]]:
    records = _CASE_EXECUTION_RECORDS.get(case_id, [])
    return [r.model_dump() for r in records]

def get_case_analysis_runs(case_id: str) -> List[Dict[str, Any]]:
    return _CASE_EXECUTION_HISTORY.get(case_id, [])

async def get_case_analysis_plan(db: AsyncSession, case: Case) -> DynamicAnalysisPlan:
    """
    Constructs the dynamic analysis plan for a case based on its uploaded exhibits and context.
    """
    stmt = select(Evidence).where(Evidence.case_id == case.id)
    res = await db.execute(stmt)
    evidence_list = list(res.scalars().all())

    plan = dynamic_planner.generate_plan(
        case_id=case.id,
        evidence_list=evidence_list,
        specific_offense=case.specific_offense.value if hasattr(case.specific_offense, "value") and case.specific_offense else str(case.specific_offense or ""),
        investigative_objectives=case.investigative_objectives or []
    )
    return plan

async def run_case_analysis(
    db: AsyncSession,
    case: Case,
    target_engine_ids: Optional[List[str]] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Phase 2 — Unified Case Analysis Operation.

    One click executes whatever is currently supportable:
      - Tier 1-5 engines always run based on available evidence
      - Tier 6 (R01-R04) gated ONLY by X06 sufficiency, not by absence of other outputs
      - Final Verification Engine (Phase 7) runs after all engines complete
      - Output Gate (Phase 6) applied post-execution on MODEL/LLM/HYBRID engines
      - Resource Governor (Phase 8) enforces per-engine time budgets

    Legacy alias: execute_case_analysis_plan → run_case_analysis
    """
    stmt = select(Evidence).where(Evidence.case_id == case.id)
    res = await db.execute(stmt)
    evidence_list = list(res.scalars().all())

    plan = await get_case_analysis_plan(db, case)
    engine_sequence = target_engine_ids or plan.execution_order

    context = EngineContext(
        case_id=case.id,
        case_title=case.title,
        specific_offense=str(case.specific_offense.value if hasattr(case.specific_offense, "value") and case.specific_offense else (case.specific_offense or "")),
        incident_location=case.incident_location,
        incident_time=case.incident_time_observed or datetime.now(timezone.utc),
        user_id=user_id
    )

    execution_records: List[EngineExecutionRecord] = []
    saved_observations: List[Observation] = []

    for eid in engine_sequence:
        eng = engine_registry.get(eid)
        if not eng:
            continue

        # 1. HARD DOWNSTREAM GATE: Check explicit dependencies
        dep_blocked = False
        for dep_id in eng.definition.dependencies:
            dep_rec = context.prior_results.get(dep_id)
            if dep_rec:
                if dep_rec.status == EngineExecutionResult.BLOCKED:
                    dep_blocked = True
                    record = EngineExecutionRecord(
                        case_id=case.id,
                        engine_id=eid,
                        engine_version=eng.definition.engine_version,
                        execution_mode=eng.definition.execution_mode,
                        status=EngineExecutionResult.BLOCKED,
                        confidence=None,
                        actual_execution_path="BLOCKED_PREREQUISITE_FAILED",
                        actual_execution_mode="BLOCKED",
                        failure_reason=f"Prerequisite engine '{dep_id}' was BLOCKED ({dep_rec.failure_reason or 'prerequisite unavailable'})."
                    )
                    context.prior_results[eid] = record
                    execution_records.append(record)
                    break
                elif dep_rec.status == EngineExecutionResult.NO_USABLE_OUTPUT:
                    dep_blocked = True
                    record = EngineExecutionRecord(
                        case_id=case.id,
                        engine_id=eid,
                        engine_version=eng.definition.engine_version,
                        execution_mode=eng.definition.execution_mode,
                        status=EngineExecutionResult.BLOCKED,
                        confidence=None,
                        actual_execution_path="BLOCKED_PREREQUISITE_NO_USABLE_OUTPUT",
                        actual_execution_mode="BLOCKED",
                        failure_reason=f"Prerequisite engine '{dep_id}' produced NO_USABLE_OUTPUT ({dep_rec.failure_reason or 'no usable features'})."
                    )
                    context.prior_results[eid] = record
                    execution_records.append(record)
                    break
                elif dep_rec.status == EngineExecutionResult.FAILED:
                    dep_blocked = True
                    record = EngineExecutionRecord(
                        case_id=case.id,
                        engine_id=eid,
                        engine_version=eng.definition.engine_version,
                        execution_mode=eng.definition.execution_mode,
                        status=EngineExecutionResult.BLOCKED,
                        confidence=None,
                        actual_execution_path="BLOCKED_PREREQUISITE_FAILED",
                        actual_execution_mode="BLOCKED",
                        failure_reason=f"Prerequisite engine '{dep_id}' FAILED ({dep_rec.failure_reason or 'engine error'})."
                    )
                    context.prior_results[eid] = record
                    execution_records.append(record)
                    break
        if dep_blocked:
            continue

        # 2. HARD DOWNSTREAM GATE FOR RECONSTRUCTION (X06 -> R01, R02, R03)
        if eid in ["R01", "R02", "R03"]:
            x06_rec = context.prior_results.get("X06")
            is_insufficient = False
            if x06_rec:
                if x06_rec.status in [EngineExecutionResult.BLOCKED, EngineExecutionResult.FAILED]:
                    is_insufficient = True
                elif x06_rec.outputs:
                    top_x06 = x06_rec.outputs[0]
                    if not top_x06.get("proceed_to_reconstruction", True) or top_x06.get("sufficiency_rating") == "INSUFFICIENT_FOR_RECONSTRUCTION":
                        is_insufficient = True
            else:
                is_insufficient = True

            if is_insufficient:
                reason = "Required corroborating observations unavailable (X06: INSUFFICIENT_FOR_RECONSTRUCTION)"
                if eid == "R02":
                    reason = "Prerequisite engine R01 is BLOCKED (no defensible sequence to test)."
                elif eid == "R03":
                    reason = "Prerequisite engine R01 is BLOCKED (no hypotheses exist to adversarially challenge)."
                record = EngineExecutionRecord(
                    case_id=case.id,
                    engine_id=eid,
                    engine_version=eng.definition.engine_version,
                    execution_mode=eng.definition.execution_mode,
                    status=EngineExecutionResult.BLOCKED,
                    confidence=None,
                    actual_execution_path="BLOCKED_PREREQUISITE_INSUFFICIENT" if eid == "R01" else "BLOCKED_PREREQUISITE_FAILED",
                    actual_execution_mode="BLOCKED",
                    failure_reason=reason,
                    outputs=[]
                )
                context.prior_results[eid] = record
                execution_records.append(record)
                continue

        # Phase 8: Governance — check objective relevance for optional engines
        if eid in plan.optional_engines:
            if resource_governor.should_skip_for_objective(
                eid, case.investigative_objectives or []
            ):
                record = EngineExecutionRecord(
                    case_id=case.id,
                    engine_id=eid,
                    engine_version=eng.definition.engine_version,
                    execution_mode=eng.definition.execution_mode,
                    status=EngineExecutionResult.SKIPPED_NO_INPUT,
                    actual_execution_path="SKIPPED_NOT_REQUIRED",
                    actual_execution_mode="SKIPPED",
                    failure_reason="Skipped: No investigative objective matches engine relevance."
                )
                context.prior_results[eid] = record
                execution_records.append(record)
                continue

        # Match relevant evidence for departmental engines
        matched_evidence = None
        if eng.definition.accepted_evidence_types:
            for ev in evidence_list:
                ev_type_str = ev.evidence_type.value if hasattr(ev.evidence_type, "value") else str(ev.evidence_type)
                if ev_type_str in eng.definition.accepted_evidence_types:
                    matched_evidence = ev
                    break
            if not matched_evidence:
                # Modality is unavailable in this case exhibits: BLOCK execution
                record = EngineExecutionRecord(
                    case_id=case.id,
                    engine_id=eid,
                    engine_version=eng.definition.engine_version,
                    execution_mode=eng.definition.execution_mode,
                    status=EngineExecutionResult.BLOCKED,
                    confidence=None,
                    actual_execution_path="BLOCKED_UNAVAILABLE_MODALITY",
                    actual_execution_mode="BLOCKED",
                    failure_reason=f"Unavailable: No accepted evidence modality ({', '.join(eng.definition.accepted_evidence_types)}) attached to case."
                )
                context.prior_results[eid] = record
                execution_records.append(record)
                continue
        elif eid.startswith("E"):
            # Evidence foundation engines without specific restriction operate on case exhibit manifest
            matched_evidence = evidence_list[0] if evidence_list else None

        try:
            record = await engine_registry.execute_engine(
                engine_id=eid,
                case_id=case.id,
                evidence=matched_evidence,
                context=context
            )
            # Evidence Reference Integrity Gate enforcement
            from app.reconstruction.integrity_gate import (
                validate_evidence_reference_integrity,
                validate_provenance_citations
            )
            is_valid, violations = validate_evidence_reference_integrity(
                case_evidence_list=evidence_list,
                payload=record.outputs,
                context_desc=f"Engine {eid} ({eng.definition.engine_name})"
            )
            if not is_valid:
                logger.warning(f"REJECTING output for {eid} due to UNSUPPORTED_EVIDENCE_REFERENCE: {violations}")
                record.status = EngineExecutionResult.BLOCKED
                record.actual_execution_mode = "BLOCKED"
                record.failure_reason = f"UNSUPPORTED_EVIDENCE_REFERENCE: {'; '.join(violations)}"
                record.outputs = []

            # Also validate citation provenance for R01 / reconstruction outputs
            if record.outputs and eid in ["R01", "R02", "R03"]:
                valid_outputs = []
                for out_item in record.outputs:
                    cits = out_item.get("supporting_evidence_citations", []) or out_item.get("supporting_claims", [])
                    c_valid, c_errors = validate_provenance_citations(
                        case_id=case.id,
                        engine_id=eid,
                        citations=cits,
                        execution_records=context.prior_results,
                        evidence_id=matched_evidence.id if matched_evidence else None
                    )
                    if c_valid:
                        valid_outputs.append(out_item)
                    else:
                        logger.warning(f"REJECTING claim in {eid} due to INVALID_PROVENANCE_REFERENCE: {c_errors[0]['reason']}")
                        record.warnings.append(f"INVALID_PROVENANCE_REFERENCE: {c_errors[0]['reason']}")
                if not valid_outputs:
                    record.status = EngineExecutionResult.BLOCKED
                    record.actual_execution_mode = "BLOCKED"
                    record.failure_reason = "INVALID_PROVENANCE_REFERENCE: Hypotheses cited BLOCKED or unverified engines."
                    record.outputs = []
                else:
                    record.outputs = valid_outputs
        except Exception as e:
            logger.error(f"Error executing engine {eid}: {e}", exc_info=True)
            record = EngineExecutionRecord(
                case_id=case.id,
                engine_id=eid,
                engine_version=eng.definition.engine_version,
                execution_mode=eng.definition.execution_mode,
                status=EngineExecutionResult.FAILED,
                actual_execution_mode="FAILED",
                failure_reason=str(e)
            )

        # Post-execution normalization for truthful provenance and gating
        if record.status == EngineExecutionResult.BLOCKED:
            record.confidence = None
            record.actual_execution_mode = "BLOCKED"
            if not record.actual_execution_path or record.actual_execution_path == "NOT_STARTED":
                record.actual_execution_path = "BLOCKED"
            record.llm_provider = None
            record.llm_model = None
            record.grounding_sources = []
            record.evidence_ids = []
        else:
            # Deterministic / Model / Hybrid execution path normalization
            if not record.llm_provider:
                if eng.definition.execution_mode == ExecutionMode.HYBRID:
                    if record.actual_execution_path in ["NOT_STARTED", "DETERMINISTIC_ONLY", ""]:
                        record.actual_execution_path = "DETERMINISTIC_COMPONENT"
                elif eng.definition.execution_mode == ExecutionMode.MODEL:
                    if record.status == EngineExecutionResult.NO_USABLE_OUTPUT:
                        if not record.actual_execution_path or record.actual_execution_path in ["NOT_STARTED", "DETERMINISTIC_ONLY", "DETERMINISTIC_COMPONENT", ""]:
                            record.actual_execution_path = "NO_USABLE_INPUT"
                    elif record.status == EngineExecutionResult.BLOCKED:
                        if not record.actual_execution_path or record.actual_execution_path in ["NOT_STARTED", "DETERMINISTIC_ONLY", "DETERMINISTIC_COMPONENT", ""]:
                            record.actual_execution_path = "BLOCKED_MODEL_UNAVAILABLE"
                    else:
                        if not record.actual_execution_path or record.actual_execution_path in ["NOT_STARTED", "DETERMINISTIC_ONLY", "DETERMINISTIC_COMPONENT", ""]:
                            record.actual_execution_path = "MODEL_INFERENCE"
                elif eng.definition.execution_mode == ExecutionMode.DETERMINISTIC:
                    record.actual_execution_path = "DETERMINISTIC_ONLY"

            # Set human-readable grounding sources from actual matched evidence if not already set by engine
            if matched_evidence:
                ev_type_val = matched_evidence.evidence_type.value if hasattr(matched_evidence.evidence_type, "value") else str(matched_evidence.evidence_type)
                ev_name = getattr(matched_evidence, "title", None) or getattr(matched_evidence, "original_filename", None) or f"Exhibit {matched_evidence.id[:8]}"
                record.grounding_sources = [f"{ev_name} ({ev_type_val})"]
                record.evidence_ids = [matched_evidence.id]
            elif record.grounding_sources:
                # Retain engine's explicitly populated grounding context (e.g. X02 coverage, X05 input breakdown)
                pass
            elif eid == "X06" and record.outputs:
                rating_str = record.outputs[0].get("sufficiency_rating", "INSUFFICIENT_FOR_RECONSTRUCTION")
                record.grounding_sources = [f"Decision: {rating_str}"]
            elif eid.startswith("X") or eid.startswith("R"):
                record.grounding_sources = ["Cross-Engine Corroboration"]
            elif evidence_list:
                record.grounding_sources = ["Case Exhibit Manifest"]
            else:
                record.grounding_sources = []

        # Phase 6: Output Gate — apply 5-stage validation for AI/Model/Hybrid engines
        if record.execution_mode in (
            ExecutionMode.MODEL, ExecutionMode.LLM,
            ExecutionMode.REAL_LLM, ExecutionMode.HYBRID
        ) and record.status not in (
            EngineExecutionResult.BLOCKED, EngineExecutionResult.FAILED,
            EngineExecutionResult.SKIPPED, EngineExecutionResult.SKIPPED_NO_INPUT
        ):
            valid_ev_ids: Set[str] = {ev.id for ev in evidence_list}
            gate_result = output_gate.evaluate(record, valid_evidence_ids=valid_ev_ids)
            if not gate_result.passed:
                record = output_gate.apply_decision(record, gate_result)

        context.prior_results[eid] = record
        execution_records.append(record)

        # Convert valid outputs to persistent observations if applicable
        if record.status in [EngineExecutionResult.SUCCESS, EngineExecutionResult.PARTIAL] and matched_evidence:
            for item in record.outputs:
                if isinstance(item, dict):
                    # Derive observation type
                    obs_type = ObservationType.OTHER
                    if "person" in str(item).lower() or eid in ["I03", "I04"]:
                        obs_type = ObservationType.PERSON_DETECTED
                    elif "vehicle" in str(item).lower() or eid == "I05":
                        obs_type = ObservationType.VEHICLE_DETECTED
                    elif "damage" in str(item).lower() or eid in ["F04", "F06"]:
                        obs_type = ObservationType.PHYSICAL_MARK_DETECTED
                    elif eid in ["FI02", "FI04", "FI05", "FI06", "FI07"]:
                        obs_type = ObservationType.TRANSACTION_FLAGGED
                    elif eid == "I11":
                        obs_type = ObservationType.TEXT_EXTRACTED
                    elif eid in ["X01", "X02"]:
                        obs_type = ObservationType.ENTITY_EXTRACTED

                    obs = Observation(
                        evidence_id=matched_evidence.id,
                        case_id=case.id,
                        department=Department(eng.definition.department) if eng.definition.department in [d.value for d in Department] else Department.CORRELATED,
                        observation_type=obs_type,
                        raw_data=item,
                        observation_confidence=record.confidence,
                        model_name=eng.definition.engine_name,
                        model_version=eng.definition.engine_version,
                        verification_status=VerificationStatus.ACCEPTED if record.review_status == "AUTO_ACCEPTED" else VerificationStatus.PENDING
                    )
                    db.add(obs)
                    saved_observations.append(obs)

    # Record unavailable engines from plan as BLOCKED in telemetry
    executed_eids = {r.engine_id for r in execution_records}
    for unavail in plan.unavailable_engines:
        ueid = unavail["engine_id"]
        if ueid not in executed_eids:
            ueng = engine_registry.get(ueid)
            if ueng:
                execution_records.append(EngineExecutionRecord(
                    case_id=case.id,
                    engine_id=ueid,
                    engine_version=ueng.definition.engine_version,
                    execution_mode=ueng.definition.execution_mode,
                    status=EngineExecutionResult.BLOCKED,
                    actual_execution_path="BLOCKED_UNAVAILABLE_MODALITY",
                    actual_execution_mode="BLOCKED",
                    failure_reason=f"Unavailable: No accepted evidence modality attached to case ({unavail.get('reason', '')})"
                ))

    # Synchronize database state for Hypotheses and Gaps/Conflicts
    from app.models.entities import Hypothesis, GapConflict
    from app.models.enums import GapConflictType, Significance, HypothesisStatus, ClaimStrength
    from sqlalchemy import delete

    # 1. Database sync for Hypotheses
    r01_rec = context.prior_results.get("R01")
    if r01_rec and r01_rec.status == EngineExecutionResult.BLOCKED:
        # Clear stale hypotheses from prior runs
        await db.execute(delete(Hypothesis).where(Hypothesis.case_id == case.id))
    elif r01_rec and r01_rec.outputs:
        await db.execute(delete(Hypothesis).where(Hypothesis.case_id == case.id))
        for h in r01_rec.outputs:
            conf_val = h.get("confidence_score")
            str_val = ClaimStrength.STRONG if (conf_val is not None and conf_val > 0.8) else ClaimStrength.MODERATE
            db_hyp = Hypothesis(
                case_id=case.id,
                label=h.get("hypothesis_title", "Reconstruction Hypothesis"),
                description=h.get("narrative", ""),
                status=HypothesisStatus.DRAFT,
                overall_strength=str_val,
                assumptions=h.get("supporting_evidence_citations", []),
                sequence=h.get("sequence", [])
            )
            db.add(db_hyp)

    # 2. Database sync for Gaps (X04)
    x04_rec = context.prior_results.get("X04")
    if x04_rec is not None:
        await db.execute(delete(GapConflict).where(GapConflict.case_id == case.id, GapConflict.gc_type == GapConflictType.GAP))
        for g in (x04_rec.outputs or []):
            sig = Significance.CRITICAL if g.get("significance") == "CRITICAL" else Significance.HIGH
            gc = GapConflict(
                case_id=case.id,
                gc_type=GapConflictType.GAP,
                description=g.get("description", "Evidentiary gap identified"),
                significance=sig,
                significance_reason=g.get("remediation")
            )
            db.add(gc)

    # 3. Database sync for Conflicts (X05)
    x05_rec = context.prior_results.get("X05")
    if x05_rec is not None:
        await db.execute(delete(GapConflict).where(GapConflict.case_id == case.id, GapConflict.gc_type != GapConflictType.GAP))
        for c in (x05_rec.outputs or []):
            gc = GapConflict(
                case_id=case.id,
                gc_type=GapConflictType.SOURCE_DISAGREEMENT,
                description=c.get("discrepancy_explanation") or c.get("description", "Source discrepancy"),
                significance=Significance.HIGH,
                significance_reason=c.get("admissibility_and_credibility_note")
            )
            db.add(gc)

    await db.commit()

    # Update telemetry store
    _CASE_EXECUTION_RECORDS[case.id] = execution_records

    # Track immutable analysis run history for audit integrity
    run_history = _CASE_EXECUTION_HISTORY.setdefault(case.id, [])
    run_number = len(run_history) + 1
    run_id = f"RUN_{uuid.uuid4().hex[:8].upper()}"

    run_snapshot = {
        "run_id": run_id,
        "run_number": run_number,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "triggered_by": user_id,
        "engines_executed": len(execution_records),
        "successful_engines": len([r for r in execution_records if r.status == EngineExecutionResult.SUCCESS]),
        "partial_engines": len([r for r in execution_records if r.status == EngineExecutionResult.PARTIAL]),
        "blocked_engines": len([r for r in execution_records if r.status == EngineExecutionResult.BLOCKED]),
        "failed_engines": len([r for r in execution_records if r.status == EngineExecutionResult.FAILED]),
        "observations_created": len(saved_observations),
        "telemetry_summary": [
            {
                "engine_id": r.engine_id,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "actual_path": r.actual_execution_path,
                "execution_id": r.execution_id
            }
            for r in execution_records
        ]
    }
    run_history.append(run_snapshot)

    # Phase 7: Final Verification Engine — independent technical audit
    try:
        from app.reconstruction.final_verification_engine import final_verification_engine
        valid_ev_ids_for_fve: Set[str] = {ev.id for ev in evidence_list}
        fve_result = final_verification_engine.verify(
            engine_outputs=context.prior_results,
            valid_evidence_ids=valid_ev_ids_for_fve,
            case_id=case.id
        )
        final_verification = fve_result.to_dict()
    except Exception as fve_err:
        logger.warning(f"Final Verification Engine encountered error: {fve_err}")
        final_verification = {
            "determination": "VERIFICATION_ERROR",
            "summary": f"Final verification could not complete: {fve_err}",
        }

    return {
        "case_id": case.id,
        "run_id": run_id,
        "run_number": run_number,
        "total_historical_runs": len(run_history),
        "engines_executed": len(execution_records),
        "successful_engines": len([r for r in execution_records if r.status == EngineExecutionResult.SUCCESS]),
        "partial_engines": len([r for r in execution_records if r.status == EngineExecutionResult.PARTIAL]),
        "blocked_engines": len([r for r in execution_records if r.status == EngineExecutionResult.BLOCKED]),
        "failed_engines": len([r for r in execution_records if r.status == EngineExecutionResult.FAILED]),
        "observations_created": len(saved_observations),
        "final_verification": final_verification,
        "telemetry": [r.model_dump() for r in execution_records]
    }


# ---------------------------------------------------------------------------
# Backward-compatibility alias (Phase 2)
# Tests and routers that import execute_case_analysis_plan continue to work.
# ---------------------------------------------------------------------------
async def execute_case_analysis_plan(
    db: AsyncSession,
    case: Case,
    target_engine_ids: Optional[List[str]] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Legacy alias for run_case_analysis (Phase 2 rename)."""
    return await run_case_analysis(db, case, target_engine_ids, user_id)

from app.evidence.storage import storage_manager
from app.department_engines.investigation.service import run_investigation_pipeline
from app.department_engines.forensic.image import forensic_image_processor
from app.department_engines.forensic.report import forensic_report_processor
from app.department_engines.financial.transactions import financial_transaction_processor

async def dispatch_evidence_processing(
    db: AsyncSession,
    case: Case,
    evidence: Evidence
) -> List[Observation]:
    """
    Direct single-evidence processor.
    Routes file to Image, Report, Transaction, or Video processor to generate initial observations.
    """
    file_bytes = storage_manager.get_file_bytes(evidence.storage_key)
    base_time = case.incident_time_observed or datetime.now(timezone.utc)

    if evidence.evidence_type == EvidenceType.IMAGE:
        evidence.processing_status = ProcessingStatus.IN_PROGRESS
        await db.commit()
        obs_inputs = forensic_image_processor.process_image_file(
            image_bytes=file_bytes,
            filename=evidence.original_filename,
            evidence_id=evidence.id,
            metadata=evidence.metadata_json,
            base_timestamp=base_time
        )
        saved = []
        for obs_in in obs_inputs:
            obs = await create_observation(db, case.id, obs_in)
            saved.append(obs)
        evidence.processing_status = ProcessingStatus.COMPLETED
        await db.commit()
        return saved

    elif evidence.evidence_type == EvidenceType.FORENSIC_REPORT:
        evidence.processing_status = ProcessingStatus.IN_PROGRESS
        await db.commit()
        text_content = file_bytes.decode("utf-8", errors="replace")
        obs_inputs = forensic_report_processor.process_report_text(
            report_text=text_content,
            evidence_id=evidence.id,
            base_timestamp=base_time
        )
        saved = []
        for obs_in in obs_inputs:
            obs = await create_observation(db, case.id, obs_in)
            saved.append(obs)
        evidence.processing_status = ProcessingStatus.COMPLETED
        await db.commit()
        return saved

    elif evidence.evidence_type == EvidenceType.INVENTORY_RECORD:
        from app.department_engines.investigation.inventory import inventory_processor
        evidence.processing_status = ProcessingStatus.IN_PROGRESS
        await db.commit()
        text_content = file_bytes.decode("utf-8", errors="replace")
        obs_inputs = inventory_processor.process_inventory_data(
            content=text_content,
            evidence_id=evidence.id,
            base_timestamp=base_time
        )
        saved = []
        for obs_in in obs_inputs:
            obs = await create_observation(db, case.id, obs_in)
            saved.append(obs)
        evidence.processing_status = ProcessingStatus.COMPLETED
        await db.commit()
        return saved

    elif evidence.evidence_type == EvidenceType.TRANSACTION_RECORD:
        evidence.processing_status = ProcessingStatus.IN_PROGRESS
        await db.commit()
        text_content = file_bytes.decode("utf-8", errors="replace")
        obs_inputs = financial_transaction_processor.process_transactions(
            transaction_data=text_content,
            evidence_id=evidence.id,
            base_timestamp=base_time
        )
        saved = []
        for obs_in in obs_inputs:
            obs = await create_observation(db, case.id, obs_in)
            saved.append(obs)
        evidence.processing_status = ProcessingStatus.COMPLETED
        await db.commit()
        return saved

    else:
        return await run_investigation_pipeline(db, case, evidence)


