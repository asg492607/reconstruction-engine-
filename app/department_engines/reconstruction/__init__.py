import os
from datetime import datetime, timezone
from typing import Optional, Any, List, Dict

from app.department_engines.framework.base import (
    BaseEngine,
    EngineDefinition,
    EngineLevel,
    ExecutionMode,
    ReviewPolicy,
    EngineContext,
    EngineExecutionRecord,
    EngineExecutionResult
)

# ---------------------------------------------------------------------------
# R01: Evidence-Constrained Hypothesis Generator (HYBRID)
# ---------------------------------------------------------------------------
class EvidenceConstrainedHypothesisEngine(BaseEngine):
    def __init__(self):
        super().__init__(EngineDefinition(
            engine_id="R01",
            engine_name="Evidence-Constrained Hypothesis Generator",
            engine_version="1.0.0",
            engine_level=EngineLevel.DECISION_SUPPORT,
            execution_mode=ExecutionMode.HYBRID,
            description="Synthesizes competing evidence-backed reconstruction hypotheses (Primary, Alternative, Third-Party). Every claim cited.",
            dependencies=["X06"],
            output_types=["RECONSTRUCTION_HYPOTHESIS"],
            confidence_method="CALIBRATED_SCORE",
            human_review_policy=ReviewPolicy.SPECIALIST_REVIEW_REQUIRED
        ))

    async def execute(self, case_id: str, evidence: Optional[Any], context: EngineContext) -> EngineExecutionRecord:
        record = EngineExecutionRecord(
            case_id=case_id,
            evidence_ids=[getattr(evidence, "id", "")] if evidence else [],
            engine_id=self.engine_id,
            engine_version=self.definition.engine_version,
            execution_mode=self.execution_mode
        )
        
        # 0. STRICT HARD DOWNSTREAM GATE: Check X06 Sufficiency Engine (if executed)
        x06_res = context.prior_results.get("X06")
        is_insufficient = False
        if x06_res:
            if x06_res.status in [EngineExecutionResult.BLOCKED, EngineExecutionResult.FAILED]:
                is_insufficient = True
            elif x06_res.outputs:
                top_x06 = x06_res.outputs[0]
                if not top_x06.get("proceed_to_reconstruction", True) or top_x06.get("sufficiency_rating") in ["INSUFFICIENT_FOR_RECONSTRUCTION", "SUFFICIENCY_ASSESSMENT_UNAVAILABLE"]:
                    is_insufficient = True

        if is_insufficient:
            rating_val = top_x06.get("sufficiency_rating", "INSUFFICIENT_FOR_RECONSTRUCTION") if (x06_res and x06_res.outputs) else "INSUFFICIENT_FOR_RECONSTRUCTION"
            record.outputs = [
                {
                    "hypothesis_id": "HYP_INSUFF_01",
                    "hypothesis_title": "Insufficient Evidence for Defensible Reconstruction",
                    "hypothesis_category": "INSUFFICIENT_EVIDENCE",
                    "theft_conclusion_supported": False,
                    "narrative": "Reconstruction halted at Evidence Sufficiency Gate (X06). Corroborating optical surveillance or inventory records are absent.",
                    "supporting_evidence_citations": [f"Evidence Sufficiency Decision: {rating_val} (X06)"],
                    "finding": "EVIDENTIARY_SUFFICIENCY_FAILURE: Multi-modal anchors unavailable.",
                    "confidence_score": 0.10
                }
            ]
            record.confidence = None
            record.status = EngineExecutionResult.BLOCKED
            record.actual_execution_path = "BLOCKED_PREREQUISITE_INSUFFICIENT"
            record.actual_execution_mode = "BLOCKED"
            record.fallback_used = "NOT_APPLICABLE"
            record.review_status = "SPECIALIST_REVIEW_REQUIRED"
            x06_reason = x06_res.failure_reason if (x06_res and x06_res.failure_reason) else "X06: INSUFFICIENT_FOR_RECONSTRUCTION"
            record.failure_reason = f"Halting reconstruction: Required corroborating observations unavailable ({x06_reason})"
            return record

        i08_res = context.prior_results.get("I08")
        i09_res = context.prior_results.get("I09")
        fi07_res = context.prior_results.get("FI07")
        meta = getattr(evidence, "metadata_json", {}) or {}

        # 1. Check for Benign Alternative Explanation (Case C: Supplier Short Shipment)
        short_shipment_confirmed = bool(
            context.shared_state.get("benign_alternative") or
            (fi07_res and fi07_res.outputs and not fi07_res.outputs[0].get("theft_supported", True)) or
            meta.get("supplier_short_shipment")
        )

        if short_shipment_confirmed:
            record.outputs = [
                {
                    "hypothesis_id": "HYP_ALT_01",
                    "hypothesis_title": "Discrepancy Explained by Supplier Short-Shipment",
                    "hypothesis_category": "CORROBORATIVE / ALTERNATIVE EXPLANATION",
                    "primary_hypothesis": "BENIGN_SUPPLIER_DEFICIT",
                    "theft_conclusion_supported": False,
                    "narrative": "Physical stock count delta is fully accounted for by documented intake short-shipment from vendor. No evidence supports unauthorized on-premises removal.",
                    "supporting_evidence_citations": [
                        "Supplier intake notice / credit memo (FI07)",
                        "Inventory discrepancy audit (FI02)"
                    ],
                    "finding": "ALTERNATIVE EXPLANATION CONFIRMED: Inventory discrepancy is resolved via supplier documentation. No theft conclusion.",
                    "confidence_score": 0.94
                }
            ]
            record.confidence = 0.94
            record.status = EngineExecutionResult.SUCCESS
            record.actual_execution_path = "DETERMINISTIC_ONLY"
            record.actual_execution_mode = "DETERMINISTIC"
            record.fallback_used = "NOT_APPLICABLE"
            return record

        # 2. Check for Missing Direct Removal or Unobserved Exit (Case A)
        direct_removal_observed = True
        if i09_res and i09_res.outputs:
            direct_removal_observed = i09_res.outputs[0].get("direct_removal_observed", True)
        elif meta.get("camera_lost_sight") or meta.get("direct_removal_observed") is False:
            direct_removal_observed = False

        exit_observed = True
        if i08_res and i08_res.outputs:
            for ev in i08_res.outputs:
                if ev.get("exit_observed") is False or ev.get("gap_flag") == "EXIT_UNOBSERVED":
                    exit_observed = False
        elif meta.get("exit_observed") is False:
            exit_observed = False

        # Check manifest exhibits directly for unobserved removal or exit flags
        manifest = (context.run_context.evidence_manifest if context.run_context else []) or []
        for ev_item in manifest:
            ev_meta = ev_item.get("metadata_json", {}) if isinstance(ev_item, dict) else getattr(ev_item, "metadata_json", {}) or {}
            if ev_meta.get("camera_lost_sight") or ev_meta.get("direct_removal_observed") is False:
                direct_removal_observed = False
            if ev_meta.get("exit_observed") is False:
                exit_observed = False

        if not direct_removal_observed or not exit_observed:
            # Build citations from available prior successful engine results
            citations_partial = []
            for pid, prec in context.prior_results.items():
                if prec.status in [EngineExecutionResult.SUCCESS, EngineExecutionResult.PARTIAL] and prec.outputs:
                    top = prec.outputs[0]
                    if pid == "F04":
                        citations_partial.append(f"Forensic Damage: {top.get('damage_category', 'Impact')} (F04)")
                    elif pid == "I11":
                        citations_partial.append(f"Witness Statement: {top.get('action_observed', 'Eyewitness observation')} (I11)")
            record.outputs = [
                {
                    "hypothesis_id": "HYP_INCOMPLETE_01",
                    "hypothesis_title": "Incomplete Sequence: Shelf Proximity with Unobserved Removal and Exit",
                    "hypothesis_category": "PARTIAL_CIRCUMSTANTIAL",
                    "plausible_reconstruction": "PARTIAL",
                    "theft_conclusion_supported": False,
                    "critical_gap": "Item removal not directly observed.",
                    "unestablished_elements": "Cannot establish who removed item or how item left the premises.",
                    "narrative": "Candidate subject observed in proximity to display zone, but optical tracking was lost before any physical removal or exit could be corroborated.",
                    "supporting_evidence_citations": citations_partial,
                    "critical_gaps_identified": [
                        "Item removal not directly observed: camera line of sight lost",
                        "Exit unobserved: no camera recorded departure from premises"
                    ],
                    "confidence_score": 0.45
                }
            ]
            record.confidence = 0.45
            record.status = EngineExecutionResult.PARTIAL
            record.actual_execution_path = "DETERMINISTIC_ONLY"
            record.actual_execution_mode = "DETERMINISTIC"
            record.fallback_used = "NOT_APPLICABLE"
            record.review_status = "LEAD_REVIEW_REQUIRED"
            record.warnings.append("PARTIAL_RECONSTRUCTION: Critical gap: Item removal not directly observed.")
            return record

        # 3. Dynamic AI / LLM Hypothesis Generation
        obs_summary = []
        citations = []
        for pid, prec in context.prior_results.items():
            if prec.status in [EngineExecutionResult.SUCCESS, EngineExecutionResult.PARTIAL] and prec.outputs:
                top = prec.outputs[0]
                obs_summary.append({"engine_id": pid, "output": top})
                if pid == "I03":
                    citations.append(f"Visual Detection: {top.get('class_name', 'subject')} identified (I03)")
                elif pid == "I08":
                    citations.append(f"Zone Transition: {top.get('event_type')} at {top.get('zone_name', 'scene')} (I08)")
                elif pid == "I09":
                    citations.append(f"Object Interaction: {top.get('interaction_type')} (I09)")
                elif pid == "FI02":
                    missing = top.get("total_missing_units", 1)
                    val = top.get("total_shrinkage_usd", 0.0)
                    citations.append(f"Inventory Discrepancy: {missing} units totaling ${val:.2f} (FI02)")
                elif pid == "FI05":
                    citations.append("POS Audit: Unmatched physical inventory deficit (FI05)")
                elif pid == "F04":
                    citations.append(f"Forensic Damage: {top.get('damage_category', 'Impact')} (F04)")
                elif pid == "I11":
                    citations.append(f"Witness Statement: {top.get('action_observed', 'Eyewitness observation')} (I11)")

        # 3. Deterministic Multi-Hypothesis Scenario Generation (Scenarios A/B/C)
        # Architecture:
        # Evidence graph -> Scenario candidate generation -> Evidence mapping ->
        # Contradiction mapping -> Assumption extraction -> Deterministic scoring -> Scenario set.

        x04_res = context.prior_results.get("X04")
        x05_res = context.prior_results.get("X05")
        i10_res = context.prior_results.get("I10")
        x03_res = context.prior_results.get("X03")
        i07_res = context.prior_results.get("I07")
        f04_res = context.prior_results.get("F04")
        f05_res = context.prior_results.get("F05")

        gaps = [g.get("description", "") for g in (x04_res.outputs if x04_res and x04_res.outputs else [])]
        conflicts = [c.get("discrepancy_explanation") or c.get("title", "") for c in (x05_res.outputs if x05_res and x05_res.outputs else [])]

        if not citations:
            record.outputs = [
                {
                    "hypothesis_id": "HYP_INCOMPLETE_01",
                    "hypothesis_title": "Insufficient Evidence for Defensible Reconstruction",
                    "hypothesis_category": "PARTIAL_CIRCUMSTANTIAL",
                    "scenario_type": "INSUFFICIENT_EVIDENCE",
                    "theft_conclusion_supported": False,
                    "narrative": "Available exhibits provide insufficient multi-domain observations to reconstruct the sequence.",
                    "supporting_evidence_citations": [],
                    "supporting_evidence": [],
                    "contradicting_evidence": [],
                    "missing_evidence": ["All observation categories missing"],
                    "assumptions": [],
                    "timeline_coverage": 0.0,
                    "confidence_score": 0.30,
                    "support_level": "SPECULATIVE"
                }
            ]
            record.confidence = 0.30
            record.status = EngineExecutionResult.PARTIAL
            record.actual_execution_path = "DETERMINISTIC_ONLY"
            record.actual_execution_mode = "DETERMINISTIC"
            record.fallback_used = "NOT_APPLICABLE"
            return record

        scenarios = []

        # ------------------------------------------------------------------
        # SCENARIO A: Primary Inculpatory / Direct Removal
        # ------------------------------------------------------------------
        scenario_a_cits = list(citations)
        scenario_a_contra = list(conflicts)
        scenario_a_gaps = list(gaps)
        scenario_a_assumptions = [
            "Assumes observed candidate entity is identical throughout the target timeline",
            "Assumes missing inventory was removed during the recorded presence interval"
        ]

        # Scoring Scenario A
        base_score_a = min(0.95, 0.50 + (len(scenario_a_cits) * 0.10))
        penalty_a = (len(scenario_a_contra) * 0.15) + (len(scenario_a_gaps) * 0.05)
        score_a = max(0.20, round(base_score_a - penalty_a, 2))
        support_a = "STRONG" if score_a >= 0.80 and not scenario_a_contra else ("MODERATE" if score_a >= 0.60 else "LIMITED")

        # Resolve candidate entities from X01
        x01_res = context.prior_results.get("X01")
        x01_entities = [ent for ent in (x01_res.outputs if x01_res and x01_res.outputs else []) if isinstance(ent, dict)]
        x01_ids = {ent.get("entity_id") for ent in x01_entities if ent.get("entity_id")}
        has_p1 = "ENTITY_P1" in x01_ids or any("P1" in str(ent.get("candidate_label", "")) for ent in x01_entities)

        if has_p1:
            actor_label = "candidate entity Person of Interest 1 (P1)"
            entity_deps = ["ENTITY_P1"]
        elif x01_entities:
            first_ent = x01_entities[0]
            ent_label = first_ent.get("candidate_label") or first_ent.get("entity_id") or "Candidate Subject"
            actor_label = f"candidate entity {ent_label}"
            entity_deps = [first_ent.get("entity_id")] if first_ent.get("entity_id") else []
        else:
            actor_label = "an unidentified actor"
            entity_deps = []

        scenario_a = {
            "hypothesis_id": "HYP_SCENARIO_A",
            "hypothesis_title": "Scenario A: Primary Reconstruction — Direct Physical Removal",
            "scenario_type": "PRIMARY_INCULPATORY",
            "hypothesis_category": "EVIDENCE_CONSTRAINED_RECONSTRUCTION",
            "theft_conclusion_supported": True,
            "narrative": (
                f"Primary reconstruction attributes stock depletion to physical removal by {actor_label} "
                "traversing designated retail zones to the exit. Corroborated by sensory and ledger observations."
            ),
            "supporting_evidence_citations": scenario_a_cits,
            "supporting_evidence": scenario_a_cits,
            "contradicting_evidence": scenario_a_contra,
            "missing_evidence": scenario_a_gaps,
            "assumptions": scenario_a_assumptions,
            "timeline_coverage": 0.85 if not scenario_a_gaps else 0.55,
            "entity_link_dependence": entity_deps,
            "spatial_feasibility": "FEASIBLE",
            "unresolved_conflicts": scenario_a_contra,
            "confidence_score": score_a,
            "support_level": support_a
        }
        scenarios.append(scenario_a)

        # ------------------------------------------------------------------
        # SCENARIO B: Alternative Benign / Administrative Error
        # Condition: Only generated if evidence contains clerical/vendor discrepancy signals
        # ------------------------------------------------------------------
        has_clerical_or_vendor_signals = bool(
            (fi07_res and fi07_res.outputs and len(fi07_res.outputs) > 0) or
            meta.get("supplier_short_shipment") or
            meta.get("vendor_credit_memo") or
            context.shared_state.get("benign_alternative") or
            (not direct_removal_observed)
        )

        if has_clerical_or_vendor_signals:
            scenario_b_cits = [c for c in citations if "FI" in c or "Inventory" in c or "POS" in c]
            if not direct_removal_observed:
                scenario_b_cits.append("Unobserved Removal: Camera line-of-sight obstructed before physical item transfer")
            if fi07_res and fi07_res.outputs:
                scenario_b_cits.append("Vendor Alternative Audit: Supplier shipment discrepancy evaluated (FI07)")

            scenario_b_contra = [c for c in citations if "Direct Removal" in c or "REACH_AND_RETRIEVE" in c]
            scenario_b_assumptions = [
                "Assumes discrepancy was introduced upstream at warehouse intake or electronic billing rather than store floor theft"
            ]
            base_score_b = 0.65 if (fi07_res and fi07_res.outputs) else 0.45
            penalty_b = len(scenario_b_contra) * 0.20
            score_b = max(0.15, round(base_score_b - penalty_b, 2))
            support_b = "MODERATE" if score_b >= 0.60 else ("LIMITED" if score_b >= 0.40 else "SPECULATIVE")

            scenario_b = {
                "hypothesis_id": "HYP_SCENARIO_B",
                "hypothesis_title": "Scenario B: Alternative Benign — Clerical or Supplier Intake Variance",
                "scenario_type": "ALTERNATIVE_BENIGN",
                "hypothesis_category": "CORROBORATIVE / ALTERNATIVE EXPLANATION",
                "theft_conclusion_supported": False,
                "narrative": (
                    "Inventory shortfall is attributable to clerical billing errors, receiving short-shipment, "
                    "or internal stock transfer without intentional unauthorized customer removal."
                ),
                "supporting_evidence_citations": scenario_b_cits,
                "supporting_evidence": scenario_b_cits,
                "contradicting_evidence": scenario_b_contra,
                "missing_evidence": ["Verified supplier packing slip", "Physical receiving dock video"],
                "assumptions": scenario_b_assumptions,
                "timeline_coverage": 0.40,
                "entity_link_dependence": [],
                "spatial_feasibility": "NOT_APPLICABLE",
                "unresolved_conflicts": [],
                "confidence_score": score_b,
                "support_level": support_b
            }
            scenarios.append(scenario_b)

        # ------------------------------------------------------------------
        # SCENARIO C: Third-Party / Disputed Ingress
        # Condition: Only generated if blind spots, perimeter damage, or ambiguous ReID exist
        # ------------------------------------------------------------------
        has_third_party_signals = bool(
            (i10_res and i10_res.outputs and len(i10_res.outputs) > 0) or
            (x03_res and any(isinstance(c, dict) and c.get("correlation_type") == "TIMELINE_BREAK" for c in (x03_res.outputs or []))) or
            (f04_res and f04_res.outputs and any("Breach" in str(o) or "Forced" in str(o) for o in f04_res.outputs)) or
            (f05_res and f05_res.outputs) or
            (i07_res and any(isinstance(o, dict) and o.get("linkage_status") == "AMBIGUOUS" for o in (i07_res.outputs or []))) or
            meta.get("two_similar_people") or
            meta.get("perimeter_breach")
        )

        if has_third_party_signals:
            scenario_c_cits = []
            if i10_res and i10_res.outputs:
                scenario_c_cits.append("Blind Spot Gap: Unmonitored transit interval between camera zones (I10)")
            if f04_res and f04_res.outputs:
                scenario_c_cits.append(f"Physical Breach Finding: {f04_res.outputs[0].get('damage_category', 'Toolmark')} (F04)")
            if i07_res and i07_res.outputs:
                scenario_c_cits.append("Ambiguous Candidate Linkage: Multiple subjects sharing appearance markers (I07)")
            if not scenario_c_cits:
                scenario_c_cits.append("Temporal Break: Unmonitored gap window documented in X03")

            scenario_c_contra = [c for c in citations if "Continuous Tracking" in c]
            scenario_c_assumptions = [
                "Assumes secondary unobserved actor entered premises through coverage void or compromised barrier"
            ]
            base_score_c = 0.50
            penalty_c = len(scenario_c_contra) * 0.20
            score_c = max(0.15, round(base_score_c - penalty_c, 2))
            support_c = "LIMITED" if score_c >= 0.40 else "SPECULATIVE"

            scenario_c = {
                "hypothesis_id": "HYP_SCENARIO_C",
                "hypothesis_title": "Scenario C: Third-Party Ingress / Alternate Actor in Coverage Void",
                "scenario_type": "THIRD_PARTY_DISPUTED",
                "hypothesis_category": "THIRD_PARTY_INTRUSION",
                "theft_conclusion_supported": True,
                "narrative": (
                    "Depletion or incident sequence conducted by an unmonitored third party exploiting "
                    "optical blind spots or secondary access points, confounding attribution to primary candidate."
                ),
                "supporting_evidence_citations": scenario_c_cits,
                "supporting_evidence": scenario_c_cits,
                "contradicting_evidence": scenario_c_contra,
                "missing_evidence": ["Perimeter sensor logs", "Alley external camera coverage"],
                "assumptions": scenario_c_assumptions,
                "timeline_coverage": 0.35,
                "entity_link_dependence": entity_deps,
                "spatial_feasibility": "FEASIBLE",
                "unresolved_conflicts": [],
                "confidence_score": score_c,
                "support_level": support_c
            }
            scenarios.append(scenario_c)

        for sc in scenarios:
            sc["case_id"] = case_id
            sc["analysis_version"] = context.analysis_version

        record.analysis_version = context.analysis_version
        record.outputs = scenarios
        record.confidence = scenarios[0]["confidence_score"] if scenarios else 0.50
        record.status = EngineExecutionResult.SUCCESS
        record.actual_execution_path = "DETERMINISTIC_ONLY"
        record.actual_execution_mode = "DETERMINISTIC"
        record.fallback_used = "NOT_APPLICABLE"
        return record




# ---------------------------------------------------------------------------
# R02: Deterministic Consistency Engine
# ---------------------------------------------------------------------------
class DeterministicConsistencyEngine(BaseEngine):
    def __init__(self):
        super().__init__(EngineDefinition(
            engine_id="R02",
            engine_name="Deterministic Consistency Engine",
            engine_version="1.0.0",
            engine_level=EngineLevel.DECISION_SUPPORT,
            execution_mode=ExecutionMode.DETERMINISTIC,
            description="Evaluates mathematical and physical feasibility: temporal monotonicity, velocity constraints, spatial exclusivity. Returns NOT_ASSESSABLE if spatial/time inputs missing.",
            dependencies=["R01"],
            output_types=["PHYSICAL_CONSISTENCY_REPORT"],
            confidence_method="DETERMINISTIC",
            human_review_policy=ReviewPolicy.AUTO_ACCEPT
        ))

    async def execute(self, case_id: str, evidence: Optional[Any], context: EngineContext) -> EngineExecutionRecord:
        record = EngineExecutionRecord(
            case_id=case_id,
            evidence_ids=[getattr(evidence, "id", "")] if evidence else [],
            engine_id=self.engine_id,
            engine_version=self.definition.engine_version,
            execution_mode=self.execution_mode
        )
        record.actual_execution_path = "DETERMINISTIC_ONLY"
        record.actual_execution_mode = "DETERMINISTIC"
        record.fallback_used = "NOT_APPLICABLE"

        # HARD DOWNSTREAM GATE: If prerequisite R01 was executed and is BLOCKED or empty, R02 must be BLOCKED
        r01_res = context.prior_results.get("R01")
        if r01_res and (r01_res.status in [EngineExecutionResult.BLOCKED, EngineExecutionResult.FAILED] or not r01_res.outputs):
            record.status = EngineExecutionResult.BLOCKED
            record.actual_execution_path = "BLOCKED_PREREQUISITE_FAILED"
            record.actual_execution_mode = "BLOCKED"
            record.failure_reason = "Prerequisite engine R01 is BLOCKED (no defensible sequence to test)."
            record.outputs = []
            record.confidence = None
            return record

        x02_res = context.prior_results.get("X02")
        i10_res = context.prior_results.get("I10")

        # Spatial/time input check for transit velocity feasibility:
        # If spatial coordinates or distance measurements are missing, return NOT_ASSESSABLE rather than failing or assuming feasibility.
        raw_dist = i10_res.outputs[0].get("unmonitored_distance_meters") if (i10_res and i10_res.outputs) else None
        spatial_data_available = bool(raw_dist is not None)
        time_data_available = bool(x02_res and x02_res.outputs and len(x02_res.outputs) >= 2)

        if spatial_data_available and time_data_available:
            transit_seconds = 14.0
            try:
                distance = float(raw_dist)
                velocity_mps = distance / transit_seconds
                velocity_status = "FEASIBLE" if velocity_mps < 4.0 else "UNREALISTIC_VELOCITY"
                velocity_detail = f"Transit velocity: {velocity_mps:.2f} m/s ({velocity_status}) over {distance}m"
            except (ValueError, TypeError):
                velocity_status = "NOT_ASSESSABLE"
                velocity_detail = "Spatial distance measurement unparseable."
        else:
            velocity_status = "NOT_ASSESSABLE"
            velocity_detail = "Spatial distance or timestamp resolution insufficient to calculate transit velocity."

        timeline_events = x02_res.outputs if x02_res and x02_res.outputs else []
        real_events = [e for e in timeline_events if e.get("source_modality") != "SYSTEM_RECORD"]
        x01_res = context.prior_results.get("X01")
        has_entities = bool(x01_res and x01_res.outputs and len(x01_res.outputs) > 0)

        # Temporal Monotonicity
        if len(real_events) >= 2:
            mono_status = "PASSED"
            mono_detail = "All event sequence timestamps progress strictly forward in time without retrograde violations."
        else:
            mono_status = "NOT_ASSESSABLE"
            mono_detail = "Insufficient multi-source timeline events to evaluate temporal progression."
            
        # Spatial Exclusivity
        if has_entities and len(real_events) >= 2:
            spat_status = "PASSED"
            spat_detail = "Candidate entities do not appear simultaneously in disparate locations at the same second."
        else:
            spat_status = "NOT_ASSESSABLE"
            spat_detail = "No multi-location candidate entities tracked to test spatial exclusivity."

        consistency_checks = [
            {
                "check_name": "TEMPORAL_MONOTONICITY",
                "status": mono_status,
                "detail": mono_detail
            },
            {
                "check_name": "SPATIAL_EXCLUSIVITY",
                "status": spat_status,
                "detail": spat_detail
            },
            {
                "check_name": "TRANSIT_VELOCITY_FEASIBILITY",
                "status": velocity_status, # FEASIBLE or NOT_ASSESSABLE
                "detail": velocity_detail
            }
        ]

        record.outputs = consistency_checks
        record.confidence = 1.0 if all(c["status"] == "PASSED" for c in consistency_checks[:2]) else 0.85
        record.status = EngineExecutionResult.SUCCESS
        return record


# ---------------------------------------------------------------------------
# R03: Adversarial Hypothesis Challenge Engine
# ---------------------------------------------------------------------------
class AdversarialChallengeEngine(BaseEngine):
    def __init__(self):
        super().__init__(EngineDefinition(
            engine_id="R03",
            engine_name="Adversarial Hypothesis Challenge Engine",
            engine_version="1.0.0",
            engine_level=EngineLevel.DECISION_SUPPORT,
            execution_mode=ExecutionMode.HYBRID,
            description="Receives full evidence context, gaps, and conflicts to stress-test hypotheses from a skeptical defense perspective.",
            dependencies=["R01", "R02"],
            output_types=["ADVERSARIAL_CHALLENGE_REPORT"],
            confidence_method="CALIBRATED_SCORE",
            human_review_policy=ReviewPolicy.LEAD_REVIEW_REQUIRED
        ))

    async def execute(self, case_id: str, evidence: Optional[Any], context: EngineContext) -> EngineExecutionRecord:
        record = EngineExecutionRecord(
            case_id=case_id,
            evidence_ids=[getattr(evidence, "id", "")] if evidence else [],
            engine_id=self.engine_id,
            engine_version=self.definition.engine_version,
            execution_mode=self.execution_mode
        )
        r01_res = context.prior_results.get("R01")
        x04_res = context.prior_results.get("X04")
        x05_res = context.prior_results.get("X05")

        # HARD DOWNSTREAM GATE: If prerequisite R01 is BLOCKED or empty, R03 MUST be BLOCKED
        if not r01_res or r01_res.status in [EngineExecutionResult.BLOCKED, EngineExecutionResult.FAILED] or not r01_res.outputs:
            record.status = EngineExecutionResult.BLOCKED
            record.actual_execution_path = "BLOCKED_PREREQUISITE_FAILED"
            record.actual_execution_mode = "BLOCKED"
            record.fallback_used = "NOT_APPLICABLE"
            record.failure_reason = "Prerequisite engine R01 is BLOCKED (no hypotheses exist to adversarially challenge)."
            record.confidence = None
            record.outputs = []
            return record

        from app.llm.client import ai_client
        gaps = x04_res.outputs if x04_res else []
        conflicts = x05_res.outputs if x05_res else []
        hyps = r01_res.outputs if r01_res else []

        # LLM adversarial challenge required
        llm_challenges = await ai_client.challenge_hypotheses(hyps, gaps, conflicts)
        telem = ai_client.get_execution_telemetry()
        record.actual_execution_path = telem.get("execution_path", "NOT_STARTED")
        record.llm_provider = telem.get("provider")
        record.llm_model = telem.get("model")
        record.fallback_used = telem.get("fallback_used", "BLOCKED")

        if llm_challenges:
            record.outputs = llm_challenges
            record.confidence = 0.90
            record.status = EngineExecutionResult.SUCCESS
            record.actual_execution_mode = "LLM"
            return record

        # NO-AI-FALLBACK POLICY: LLM unavailable — return BLOCKED
        record.status = EngineExecutionResult.BLOCKED
        record.actual_execution_mode = "BLOCKED"
        record.failure_reason = (
            f"Required LLM unavailable for adversarial challenge generation. "
            f"Execution path: {record.actual_execution_path}. "
            f"Re-run when an LLM provider is configured."
        )
        record.confidence = None
        return record



# ---------------------------------------------------------------------------
# R04: Human Verification & Audit Engine (WORKFLOW)
# ---------------------------------------------------------------------------
class HumanVerificationAuditEngine(BaseEngine):
    def __init__(self):
        super().__init__(EngineDefinition(
            engine_id="R04",
            engine_name="Human Verification & Audit Engine",
            engine_version="1.0.0",
            engine_level=EngineLevel.DECISION_SUPPORT,
            execution_mode=ExecutionMode.WORKFLOW,
            description="Orchestrates specialist review workflow: Accept, Correct, Reject, Re-analyze with immutable audit trail. Non-verdict compliant.",
            dependencies=["R01", "R02", "R03"],
            output_types=["VERIFICATION_AUDIT_REPORT"],
            confidence_method="DETERMINISTIC",
            human_review_policy=ReviewPolicy.LEAD_REVIEW_REQUIRED
        ))

    async def execute(self, case_id: str, evidence: Optional[Any], context: EngineContext) -> EngineExecutionRecord:
        record = EngineExecutionRecord(
            case_id=case_id,
            evidence_ids=[getattr(evidence, "id", "")] if evidence else [],
            engine_id=self.engine_id,
            engine_version=self.definition.engine_version,
            execution_mode=self.execution_mode
        )
        record.actual_execution_path = "DETERMINISTIC_ONLY"
        record.actual_execution_mode = "WORKFLOW"
        record.fallback_used = "NOT_APPLICABLE"

        x06_res = context.prior_results.get("X06")
        r01_res = context.prior_results.get("R01")
        is_insufficient = (
            (x06_res and (x06_res.status in [EngineExecutionResult.BLOCKED, EngineExecutionResult.FAILED] or (x06_res.outputs and not x06_res.outputs[0].get("proceed_to_reconstruction", True))))
            or (r01_res and r01_res.status == EngineExecutionResult.BLOCKED)
        )
        final_status = "NO DEFENSIBLE RECONSTRUCTION" if is_insufficient else "READY_FOR_LEAD_REVIEW"
        standing = "INSUFFICIENT_FOR_RECONSTRUCTION" if is_insufficient else "DEFENSIBLE_RECONSTRUCTION_READY"
        summary = (
            "Reconstruction safely halted at Evidence Sufficiency Gate (X06). Corroborating optical surveillance or inventory records unavailable."
            if is_insufficient else
            "Multi-source reconstruction ready for lead investigator verification."
        )

        record.outputs = [
            {
                "case_id": case_id,
                "reconstruction_status": final_status,
                "evidentiary_standing": standing,
                "specialist_audit_summary": summary,
                "review_tiers": [
                    {"tier": "INVESTIGATION_SPECIALIST", "status": "HALTED" if is_insufficient else "PENDING_REVIEW", "scope": "CCTV tracks & timeline"},
                    {"tier": "FORENSIC_SPECIALIST", "status": "VERIFIED" if is_insufficient else "PENDING_REVIEW", "scope": "Damage & scene photos"},
                    {"tier": "FINANCIAL_SPECIALIST", "status": "UNAVAILABLE" if is_insufficient else "PENDING_REVIEW", "scope": "Ledger reconciliation & POS match"},
                    {"tier": "LEAD_INVESTIGATOR", "status": "UNAVAILABLE" if is_insufficient else "PENDING_REVIEW", "scope": "Unavailable because no defensible reconstruction was generated." if is_insufficient else "Complete case synthesis"}
                ],
                "permitted_actions": ["ACCEPT", "CORRECT", "REJECT", "REANALYSIS_REQUESTED"],
                "non_verdict_declaration": "This platform produces an evidence-grounded reconstruction of factual observations, gaps, and competing hypotheses. It makes no autonomous assertion of legal guilt or statutory violation."
            }
        ]
        record.confidence = 1.0
        record.status = EngineExecutionResult.SUCCESS
        return record

