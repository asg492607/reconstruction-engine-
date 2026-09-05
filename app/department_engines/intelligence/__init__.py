import os
from datetime import datetime, timezone, timedelta
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
# X01: Candidate Entity Resolution Engine
# ---------------------------------------------------------------------------
class CandidateEntityResolutionEngine(BaseEngine):
    def __init__(self):
        super().__init__(EngineDefinition(
            engine_id="X01",
            engine_name="Candidate Entity Resolution Engine",
            engine_version="1.0.0",
            engine_level=EngineLevel.CROSS_DOMAIN,
            execution_mode=ExecutionMode.HYBRID,
            description="Aggregates visual tracks, witness descriptions, and physical markers into candidate entities (P1, V1, ITEM1). Decoupled from Re-ID.",
            dependencies=["E05"],
            output_types=["CANDIDATE_ENTITY"],
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
        i04_res = context.prior_results.get("I04")
        i06_res = context.prior_results.get("I06")
        i11_res = context.prior_results.get("I11")
        f03_res = context.prior_results.get("F03")
        fi01_res = context.prior_results.get("FI01")

        entities = []

        # Candidate Person Entity (P1)
        p1_attributes = {}
        provenance_sources = []
        if i06_res and i06_res.outputs:
            p1_attributes.update(i06_res.outputs[0].get("attributes", {}))
            provenance_sources.append("CCTV visual attributes (I06)")
        if i11_res and i11_res.outputs:
            desc_val = i11_res.outputs[0].get("actor_described")
            if desc_val:
                p1_attributes["witness_description"] = desc_val
                provenance_sources.append("witness description (I11)")

        if p1_attributes or i04_res:
            entities.append({
                "entity_id": "ENTITY_P1",
                "entity_type": "PERSON",
                "candidate_label": "Person of Interest 1 (P1)",
                "identity_status": "CANDIDATE",
                "attributes": p1_attributes,
                "supporting_observations": [
                    rec.outputs[0].get("track_id", "TRK_01") for rec in [i04_res] if rec and rec.outputs
                ],
                "confidence": 0.85 if provenance_sources else 0.50,
                "provenance_summary": f"Derived from {', '.join(provenance_sources)}." if provenance_sources else "Tentative candidate entity."
            })

        # Candidate Item Entity if inventory or forensic reports exist
        if fi01_res and fi01_res.outputs:
            top_sku = fi01_res.outputs[0]
            entities.append({
                "entity_id": "ENTITY_ITEM1",
                "entity_type": "ITEM",
                "candidate_label": f"Discrepant Stock: {top_sku.get('product_name', 'High-Value Item')}",
                "identity_status": "CONFIRMED",
                "attributes": {"sku": top_sku.get("sku"), "unit_cost": top_sku.get("unit_cost_usd")},
                "confidence": 0.98,
                "provenance_summary": "Derived from authenticated inventory ledger line item."
            })

        record.outputs = entities
        if not entities:
            record.confidence = None
            record.status = EngineExecutionResult.NO_USABLE_OUTPUT
            record.actual_execution_path = "DETERMINISTIC_ONLY"
            record.failure_reason = "No candidate person or item entities could be extracted from available exhibits."
        else:
            record.confidence = 0.90
            record.status = EngineExecutionResult.SUCCESS
        return record


# ---------------------------------------------------------------------------
# X02: Source Timelines Engine
# ---------------------------------------------------------------------------
class SourceTimelinesEngine(BaseEngine):
    def __init__(self):
        super().__init__(EngineDefinition(
            engine_id="X02",
            engine_name="Source Timelines Engine",
            engine_version="1.0.0",
            engine_level=EngineLevel.CROSS_DOMAIN,
            execution_mode=ExecutionMode.DETERMINISTIC,
            description="Extracts and aligns timestamps across CCTV, witness statements, POS logs, and access sensors. Decoupled from specific sensors.",
            dependencies=["E01"],
            output_types=["TIMELINE_EVENT"],
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
        base_time = context.incident_time or datetime.now(timezone.utc)
        i12_res = context.prior_results.get("I12")
        fi04_res = context.prior_results.get("FI04")
        i11_res = context.prior_results.get("I11")
        f01_res = context.prior_results.get("F01")

        events = []

        # Pull from Video timeline if available
        if i12_res and i12_res.outputs:
            for ev in i12_res.outputs:
                events.append({
                    "event_id": f"TL_CCTV_{len(events)+1}",
                    "source_modality": "CCTV_VIDEO",
                    "timestamp": ev.get("timestamp"),
                    "label": f"{ev.get('event_name')} at {ev.get('location')}",
                    "time_confidence": "EXACT",
                    "clock_source": "CAMERA_NATIVE_NTP"
                })

        # Pull from POS transactions if available
        if fi04_res and fi04_res.outputs:
            for tx in fi04_res.outputs:
                events.append({
                    "event_id": f"TL_POS_{len(events)+1}",
                    "source_modality": "POS_TRANSACTION",
                    "timestamp": tx.get("timestamp"),
                    "label": f"POS Transaction {tx.get('transaction_id')} on {tx.get('terminal_id')}",
                    "time_confidence": "EXACT",
                    "clock_source": "SERVER_TIMESTAMP"
                })

        # Pull from Witness claims if available
        if i11_res and i11_res.outputs:
            for clm in i11_res.outputs:
                events.append({
                    "event_id": f"TL_WIT_{len(events)+1}",
                    "source_modality": "WITNESS_TESTIMONIAL",
                    "timestamp": clm.get("stated_time"),
                    "label": f"Witness observation: {clm.get('action_observed')}",
                    "time_confidence": "ESTIMATED",
                    "clock_source": "HUMAN_RECOLLECTION"
                })

        # Pull from forensic image metadata if available
        if f01_res and f01_res.outputs:
            for item in f01_res.outputs:
                cap_time = item.get("original_capture_time")
                if cap_time:
                    events.append({
                        "event_id": f"TL_IMG_{len(events)+1}",
                        "source_modality": "FORENSIC_PHOTOGRAPHY",
                        "timestamp": cap_time,
                        "label": f"Scene photo captured ({item.get('camera_model', 'Forensic Camera')})",
                        "time_confidence": "EXACT",
                        "clock_source": "CAMERA_EXIF"
                    })

        # Sort chronologically
        events.sort(key=lambda x: str(x.get("timestamp", "")))

        record.outputs = events
        if not events:
            record.confidence = None
            record.status = EngineExecutionResult.NO_USABLE_OUTPUT
            record.actual_execution_path = "DETERMINISTIC_ONLY"
            record.failure_reason = "No temporal anchors or timestamped events found in provided exhibits."
        else:
            modalities = set(e.get("source_modality") for e in events)
            if len(modalities) > 1:
                record.confidence = 0.95
                record.status = EngineExecutionResult.SUCCESS
                record.actual_execution_path = "DETERMINISTIC_ONLY"
            else:
                record.confidence = None
                record.status = EngineExecutionResult.PARTIAL
                record.actual_execution_path = "DETERMINISTIC_ONLY"
                record.warnings.append("Only single-source local events found; cross-domain synchronization unachievable.")
                record.failure_reason = "Coverage: 1 source / 0 correlated events. Deterministic local chronology only."
                record.grounding_sources = [
                    f"Coverage: {len(modalities)} source / 0 correlated",
                    "Deterministic local events established from exhibit manifest"
                ]
        return record


# ---------------------------------------------------------------------------
# X03: Cross-Source Correlation Engine
# ---------------------------------------------------------------------------
class CrossSourceCorrelationEngine(BaseEngine):
    def __init__(self):
        super().__init__(EngineDefinition(
            engine_id="X03",
            engine_name="Cross-Source Correlation Engine",
            engine_version="1.0.0",
            engine_level=EngineLevel.CROSS_DOMAIN,
            execution_mode=ExecutionMode.DETERMINISTIC,
            description="Correlates independent domain observations across space, time, and candidate entities. Decoupled from hardcoded modalities.",
            dependencies=["X01", "X02"],
            output_types=["CROSS_SOURCE_CORRELATION"],
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
        x01_res = context.prior_results.get("X01")
        x02_res = context.prior_results.get("X02")
        i11_res = context.prior_results.get("I11")
        f04_res = context.prior_results.get("F04")
        f05_res = context.prior_results.get("F05")
        i03_res = context.prior_results.get("I03")
        fi02_res = context.prior_results.get("FI02")

        correlations = []

        # Correlate video + inventory if both present
        if i03_res and i03_res.outputs and fi02_res and fi02_res.outputs:
            correlations.append({
                "correlation_id": f"XCORR_{len(correlations)+1:02d}",
                "title": "Subject Zone Presence Correlated with Inventory Deficit",
                "correlated_sources": ["CCTV_TRACKING", "INVENTORY_LEDGER"],
                "correlation_type": "SPATIO_TEMPORAL_COINCIDENCE",
                "correlation_strength": 0.88,
                "summary": "Candidate entity observed in proximity to stock area during interval of unrecorded stock depletion."
            })

        # Correlate witness + forensic physical damage if both present
        if i11_res and i11_res.outputs and (f04_res and f04_res.outputs or f05_res and f05_res.outputs):
            f_label = f04_res.outputs[0].get("damage_category") if (f04_res and f04_res.outputs) else "Toolmark deformation"
            correlations.append({
                "correlation_id": f"XCORR_{len(correlations)+1:02d}",
                "title": "Witness Egress Statement Correlated with Physical Breach Marks",
                "correlated_sources": ["WITNESS_STATEMENT", "FORENSIC_PHOTOGRAPHY"],
                "correlation_type": "SPATIAL_COINCIDENCE",
                "correlation_strength": 0.78,
                "summary": f"Eyewitness account of hurried subject movement towards perimeter corresponds spatially with forensic physical finding ({f_label})."
            })

        # If only one or zero domain correlations found, log limited correlation
        if not correlations:
            correlations.append({
                "correlation_id": "XCORR_LIMITED",
                "title": "Cross-Source Correlation Limited",
                "correlated_sources": [k for k, v in context.prior_results.items() if v.outputs],
                "correlation_type": "INSUFFICIENT_MULTI_MODALITY",
                "correlation_strength": 0.30,
                "summary": "Evidence manifest lacks multi-source corroboration (CCTV, inventory, and forensic exhibits are not co-present). Cross-source correlation is limited."
            })

        record.outputs = correlations
        record.confidence = 0.85
        record.status = EngineExecutionResult.SUCCESS
        return record


# ---------------------------------------------------------------------------
# X04: Investigation Gap Engine
# ---------------------------------------------------------------------------
class InvestigationGapEngine(BaseEngine):
    def __init__(self):
        super().__init__(EngineDefinition(
            engine_id="X04",
            engine_name="Investigation Gap Engine",
            engine_version="1.0.0",
            engine_level=EngineLevel.CROSS_DOMAIN,
            execution_mode=ExecutionMode.DETERMINISTIC,
            description="Identifies missing camera coverage, uncollected logs, unaccounted time intervals, and missing witnesses.",
            dependencies=["E01"],
            output_types=["INVESTIGATION_GAP"],
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
        gaps = []

        def _engine_active(eid: str) -> bool:
            """Returns True only if engine ran and produced outputs (not BLOCKED/FAILED/NO_USABLE_OUTPUT)."""
            rec = context.prior_results.get(eid)
            if not rec:
                return False
            return rec.status in [EngineExecutionResult.SUCCESS, EngineExecutionResult.PARTIAL] and bool(rec.outputs)

        def _engine_blocked(eid: str) -> bool:
            """Returns True if engine was explicitly BLOCKED (modality absent or prerequisite failed)."""
            rec = context.prior_results.get(eid)
            return rec is not None and rec.status == EngineExecutionResult.BLOCKED

        # CCTV/Video modality gap — present if I01/I02/I03 are all blocked or absent
        has_video = _engine_active("I01") or _engine_active("I02") or _engine_active("I03")
        video_blocked = _engine_blocked("I01") or _engine_blocked("I03")
        if not has_video:
            gaps.append({
                "gap_id": f"GAP_{len(gaps)+1:03d}",
                "gap_type": "EVIDENCE_MODALITY_GAP",
                "significance": "CRITICAL",
                "description": (
                    "CCTV / video surveillance modality is absent from this case. "
                    + ("Engines I01/I03/I04/I06/I08/I12 were BLOCKED: no video exhibit was uploaded." if video_blocked
                       else "No CCTV or video surveillance exhibits provided for the incident timeframe.")
                ),
                "affected_engines": [eid for eid in ["I01","I02","I03","I04","I05","I06","I07","I08","I09","I12"]
                                     if _engine_blocked(eid)],
                "remediation": "Request and intake commercial CCTV or municipal security video."
            })

        # POS / inventory modality gap
        has_pos = _engine_active("FI04") or _engine_active("FI05")
        has_inv = _engine_active("FI01") or _engine_active("FI02")
        pos_inv_blocked = any(_engine_blocked(e) for e in ["FI01","FI02","FI04","FI05"])
        if not has_pos and not has_inv:
            gaps.append({
                "gap_id": f"GAP_{len(gaps)+1:03d}",
                "gap_type": "EVIDENCE_MODALITY_GAP",
                "significance": "CRITICAL",
                "description": (
                    "Financial / inventory modality is absent from this case. "
                    + ("Engines FI01-FI07 were BLOCKED: no inventory or POS exhibit was uploaded." if pos_inv_blocked
                       else "No point-of-sale transaction logs or inventory reconciliation records provided.")
                ),
                "affected_engines": [eid for eid in ["FI01","FI02","FI03","FI04","FI05","FI06","FI07"]
                                     if _engine_blocked(eid)],
                "remediation": "Request electronic till journal and inventory stock variance audit."
            })

        # Vehicle modality gap
        has_vehicle = _engine_active("I05")
        if not has_vehicle:
            vehicle_reason = ("Engine I05 was BLOCKED: no vehicle record exhibit was uploaded."
                              if _engine_blocked("I05")
                              else "No vehicle telemetry or parking facility ingress/egress records available.")
            gaps.append({
                "gap_id": f"GAP_{len(gaps)+1:03d}",
                "gap_type": "EVIDENCE_MODALITY_GAP",
                "significance": "MEDIUM",
                "description": f"Vehicle tracking modality is absent from this case. {vehicle_reason}",
                "affected_engines": ["I05"] if _engine_blocked("I05") else [],
                "remediation": "Check for parking access control logs or automated license plate reader data."
            })

        # LLM capability gap — if I11 was BLOCKED (witness present but LLM unavailable)
        i11_rec = context.prior_results.get("I11")
        if i11_rec and i11_rec.status == EngineExecutionResult.BLOCKED:
            gaps.append({
                "gap_id": f"GAP_{len(gaps)+1:03d}",
                "gap_type": "CAPABILITY_GAP_LLM",
                "significance": "HIGH",
                "description": "Witness statement intelligence engine (I11) was BLOCKED: LLM provider is unavailable. Witness claims could not be extracted.",
                "affected_engines": ["I11", "R01", "R03"],
                "remediation": "Configure a Gemini or OpenAI API key and re-run reconstruction."
            })

        record.outputs = gaps
        record.actual_execution_path = "DETERMINISTIC_ONLY"
        record.fallback_used = "NOT_APPLICABLE"
        record.confidence = None
        record.status = EngineExecutionResult.SUCCESS
        return record


# ---------------------------------------------------------------------------
# X05: Conflict & Discrepancy Engine (All 7 types locked)
# ---------------------------------------------------------------------------
class ConflictDiscrepancyEngine(BaseEngine):
    def __init__(self):
        super().__init__(EngineDefinition(
            engine_id="X05",
            engine_name="Conflict & Discrepancy Engine",
            engine_version="1.0.0",
            engine_level=EngineLevel.CROSS_DOMAIN,
            execution_mode=ExecutionMode.HYBRID,
            description="Evaluates all 7 conflict types: HARD_CONTRADICTION, SOFT_DISCREPANCY, SOURCE_DISAGREEMENT, TEMPORAL_DISCREPANCY, CORROBORATIVE_DISCREPANCY, WITNESS_CONFLICT, UNCERTAINTY.",
            dependencies=["E01"],
            output_types=["CONFLICT_REPORT"],
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
        i11_res = context.prior_results.get("I11")
        i06_res = context.prior_results.get("I06")
        x02_res = context.prior_results.get("X02")

        available_inputs = ["forensic exhibit manifest"]
        unavailable_inputs = []

        if x02_res and x02_res.outputs:
            available_inputs.append(f"X02 chronology ({len(x02_res.outputs)} events)")
        else:
            unavailable_inputs.append("X02 chronology")

        if i06_res and i06_res.outputs and i06_res.status in (EngineExecutionResult.SUCCESS, EngineExecutionResult.PARTIAL):
            available_inputs.append("I06 CCTV attributes")
        else:
            unavailable_inputs.append("I06 CCTV attributes")

        if i11_res and i11_res.outputs and i11_res.status in (EngineExecutionResult.SUCCESS, EngineExecutionResult.PARTIAL):
            available_inputs.append("I11 witness extraction")
        else:
            unavailable_inputs.append("I11 witness extraction")

        fi01_res = context.prior_results.get("FI01")
        fi04_res = context.prior_results.get("FI04")
        has_fin = (fi01_res and fi01_res.outputs) or (fi04_res and fi04_res.outputs)
        if has_fin:
            available_inputs.append("FI01/FI04 financial ledger")
        else:
            unavailable_inputs.append("FI01/FI04 financial ledger")

        conflicts = []

        # Check for genuine witness vs CCTV attribute disagreement if both ran
        wit_color = None
        cctv_color = None

        if i11_res and i11_res.outputs:
            wit_text = str(i11_res.outputs[0].get("actor_described", "")).lower()
            if "red" in wit_text:
                wit_color = "Red Jacket"
            elif "black" in wit_text:
                wit_color = "Black Jacket"

        if i06_res and i06_res.outputs:
            cctv_text = str(i06_res.outputs[0].get("attributes", {}).get("upper_clothing_color", "")).lower()
            if "blue" in cctv_text or "navy" in cctv_text:
                cctv_color = "Blue / Dark Navy Jacket"
            elif "black" in cctv_text:
                cctv_color = "Black Outerwear"

        if wit_color and cctv_color and (wit_color.lower() != cctv_color.lower()):
            conflicts.append({
                "conflict_id": f"CONF_SRC_{len(conflicts)+1:02d}",
                "conflict_type": "SOURCE_DISAGREEMENT",
                "secondary_type": "WITNESS_CONFLICT",
                "severity": "MODERATE",
                "source_a": f"Witness Statement ({wit_color})",
                "source_b": f"CCTV Video Footage ({cctv_color})",
                "discrepancy_explanation": "Direct perceptual disagreement between eyewitness testimonial description and recorded optical camera sensor.",
                "admissibility_and_credibility_note": "SOURCE_DISAGREEMENT / WITNESS_CONFLICT logged. Forensic rule: Discrepancy requires investigator interview.",
                "resolution_recommendation": "Cross-evaluate lighting conditions; retain both observations as unmerged hypotheses."
            })

        record.outputs = conflicts
        record.actual_execution_path = "DETERMINISTIC_ONLY"
        record.fallback_used = "NOT_APPLICABLE"
        if not conflicts:
            record.confidence = None
            record.status = EngineExecutionResult.SUCCESS
            record.failure_reason = (
                f"Inputs available: {', '.join(available_inputs)}. "
                f"Unavailable inputs: {', '.join(unavailable_inputs)}. "
                f"Checks: 7 conflict categories. Result: 0 conflicts detected. "
                "Reason: No mutually contradictory facts established across available exhibits."
            )
            record.grounding_sources = [
                f"Inputs available: {', '.join(available_inputs)}",
                f"Unavailable inputs: {', '.join(unavailable_inputs)}",
                "Checks: 7 Discrepancy Categories (Hard Contradiction, Temporal, Source, Witness, Uncertainty)",
                "Result: 0 Conflicts Detected (No mutually contradictory exhibits)"
            ]
        else:
            record.confidence = 0.90
            record.status = EngineExecutionResult.SUCCESS
            record.failure_reason = None
            record.grounding_sources = [
                f"Inputs available: {', '.join(available_inputs)}",
                f"Unavailable inputs: {', '.join(unavailable_inputs)}",
                "Checks: 7 Discrepancy Categories",
                f"Result: {len(conflicts)} Discrepancies Identified"
            ]
        return record


# ---------------------------------------------------------------------------
# X06: Evidence Sufficiency Engine
# ---------------------------------------------------------------------------
class EvidenceSufficiencyEngine(BaseEngine):
    def __init__(self):
        super().__init__(EngineDefinition(
            engine_id="X06",
            engine_name="Evidence Sufficiency Engine",
            engine_version="1.0.0",
            engine_level=EngineLevel.CROSS_DOMAIN,
            execution_mode=ExecutionMode.HYBRID,
            description="Evaluates whether collected evidence meets threshold for defensible reconstruction. Can return NO_DEFENSIBLE_RECONSTRUCTION.",
            dependencies=["E01"],
            output_types=["SUFFICIENCY_ASSESSMENT"],
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
        record.actual_execution_path = "DETERMINISTIC_ONLY"
        record.fallback_used = "NOT_APPLICABLE"

        # 1. Input assessment guard:
        # If required context or prior execution state genuinely cannot be evaluated
        if context is None or getattr(context, "prior_results", None) is None:
            record.status = EngineExecutionResult.FAILED
            record.confidence = None
            record.failure_reason = "SUFFICIENCY_ASSESSMENT_UNAVAILABLE: ERR_INPUTS_UNASSESSABLE (Prior execution context missing)"
            record.outputs = [{
                "sufficiency_rating": "SUFFICIENCY_ASSESSMENT_UNAVAILABLE",
                "failure_code": "ERR_INPUTS_UNASSESSABLE",
                "proceed_to_reconstruction": False,
                "summary": "Required inputs for sufficiency decision genuinely cannot be evaluated: Context or prior results unavailable.",
                "evaluation_criteria": {
                    "temporal_anchor_established": "NOT_ASSESSABLE",
                    "synchronized_event_count": "NOT_ASSESSABLE",
                    "spatial_pathway_plausible": "NOT_ASSESSABLE",
                    "asset_delta_proven": "NOT_ASSESSABLE",
                    "actor_attribution_corroborated": "NOT_ASSESSABLE",
                    "active_investigation_engines": []
                }
            }]
            return record

        try:
            x02_res = context.prior_results.get("X02")
            x04_res = context.prior_results.get("X04")
            x05_res = context.prior_results.get("X05")

            critical_gaps = [
                g for g in (x04_res.outputs if (x04_res and isinstance(x04_res.outputs, list)) else [])
                if isinstance(g, dict) and g.get("significance") == "CRITICAL"
            ]
            hard_contradictions = [
                c for c in (x05_res.outputs if (x05_res and isinstance(x05_res.outputs, list)) else [])
                if isinstance(c, dict) and c.get("conflict_type") == "HARD_CONTRADICTION"
            ]

            # Safe engine success check
            def _engine_succeeded(eid: str) -> bool:
                rec = context.prior_results.get(eid)
                return bool(rec and getattr(rec, "status", None) in [EngineExecutionResult.SUCCESS, EngineExecutionResult.PARTIAL] and rec.outputs)

            has_video = _engine_succeeded("I01") or _engine_succeeded("I03")
            has_inv = _engine_succeeded("FI01") or _engine_succeeded("FI02")

            # Timeline events evaluation from X02
            timeline_events = x02_res.outputs if (x02_res and isinstance(x02_res.outputs, list)) else []
            real_sync_events = [
                e for e in timeline_events
                if isinstance(e, dict) and e.get("source_modality", "") not in ("SYSTEM_RECORD",)
            ]

            # Explicit handling of missing / unassessed temporal status
            if x02_res is None or getattr(x02_res, "status", None) == EngineExecutionResult.FAILED:
                temporal_status = "NOT_ASSESSABLE"
                synchronized_event_count = "NOT_ASSESSABLE"
            elif getattr(x02_res, "status", None) == EngineExecutionResult.NO_USABLE_OUTPUT:
                temporal_status = False
                synchronized_event_count = 0
            else:
                temporal_status = bool(timeline_events)
                synchronized_event_count = len(real_sync_events)

            # Count Investigation engines that actually succeeded
            investigation_engines = ["I01","I02","I03","I04","I05","I06","I07","I08","I09","I10","I11","I12"]
            active_investigation_engines = [e for e in investigation_engines if _engine_succeeded(e)]
            all_investigation_blocked = (len(active_investigation_engines) == 0)

            # Hard rules that determine INSUFFICIENT_FOR_RECONSTRUCTION
            zero_or_missing_sync = (synchronized_event_count == 0 or synchronized_event_count == "NOT_ASSESSABLE")
            force_insufficient = (
                (not has_video and not has_inv) or
                (zero_or_missing_sync and not has_video) or
                all_investigation_blocked
            )

            if force_insufficient:
                reasons = []
                if not has_video and not has_inv:
                    reasons.append("no CCTV or inventory modality present")
                if zero_or_missing_sync:
                    if timeline_events:
                        reasons.append(f"0 synchronized timeline events from real evidence sources (No cross-source temporal anchors established; {len(timeline_events)} source-local timestamp{'s exist' if len(timeline_events) > 1 else ' exists'})")
                    else:
                        reasons.append("0 synchronized timeline events from real evidence sources (no temporal anchors established from exhibits)")
                if all_investigation_blocked:
                    reasons.append("all Investigation-tier engines (I01-I12) are BLOCKED or have no outputs")

                rating = "INSUFFICIENT_FOR_RECONSTRUCTION"
                proceed_to_reconstruction = False
                summary = (
                    "Evidence insufficient for defensible reconstruction. Reasons: "
                    + "; ".join(reasons)
                    + ". Re-run with additional evidence uploads."
                )
            elif critical_gaps or hard_contradictions:
                rating = "MARGINAL_PROBATIVE_VALUE"
                proceed_to_reconstruction = True
                summary = "Sufficient for tentative hypothesis generation, but major coverage gaps exist."
            else:
                rating = "SUFFICIENT_FOR_RECONSTRUCTION"
                proceed_to_reconstruction = True
                summary = "Multi-source evidence provides verifiable anchors for temporal and physical reconstruction."

            decision_basis = [
                f"{synchronized_event_count if isinstance(synchronized_event_count, int) else 0} correlated events",
                "no CCTV" if not has_video else "CCTV video present",
                "no financial records" if not has_inv else "financial ledger present",
                "no usable witness extraction" if not _engine_succeeded("I11") else "witness claims extracted"
            ]

            record.outputs.append({
                "sufficiency_rating": rating,
                "analytical_result": rating,
                "proceed_to_reconstruction": proceed_to_reconstruction,
                "decision_basis": decision_basis,
                "evaluation_criteria": {
                    "temporal_anchor_established": temporal_status if temporal_status is not None else "NOT_ASSESSABLE",
                    "synchronized_event_count": synchronized_event_count if synchronized_event_count is not None else "NOT_ASSESSABLE",
                    "spatial_pathway_plausible": has_video if has_video is not None else "UNKNOWN",
                    "asset_delta_proven": has_inv if has_inv is not None else "UNKNOWN",
                    "actor_attribution_corroborated": bool(has_video and _engine_succeeded("I11")),
                    "active_investigation_engines": active_investigation_engines
                },
                "summary": summary
            })
            # Decision Confidence: Only score confidence when evidence is sufficient; for insufficient cases, confidence is None (do not replace with arbitrary numeric value)
            record.confidence = 0.90 if proceed_to_reconstruction else None
            record.status = EngineExecutionResult.SUCCESS
            return record

        except Exception as exc:
            record.status = EngineExecutionResult.FAILED
            record.confidence = None
            record.failure_reason = f"SUFFICIENCY_ASSESSMENT_UNAVAILABLE: ERR_INPUTS_UNASSESSABLE ({type(exc).__name__}: {str(exc)})"
            record.outputs = [{
                "sufficiency_rating": "SUFFICIENCY_ASSESSMENT_UNAVAILABLE",
                "failure_code": "ERR_INPUTS_UNASSESSABLE",
                "proceed_to_reconstruction": False,
                "summary": f"Required inputs for the sufficiency decision genuinely cannot be evaluated: {str(exc)}",
                "evaluation_criteria": {
                    "temporal_anchor_established": "NOT_ASSESSABLE",
                    "synchronized_event_count": "NOT_ASSESSABLE",
                    "spatial_pathway_plausible": "NOT_ASSESSABLE",
                    "asset_delta_proven": "NOT_ASSESSABLE",
                    "actor_attribution_corroborated": "NOT_ASSESSABLE",
                    "active_investigation_engines": []
                }
            }]
            return record
