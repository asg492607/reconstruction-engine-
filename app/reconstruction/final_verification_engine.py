"""
Phase 7: Independent Final Verification Engine
===============================================
Executes as the final technical gate BEFORE human specialist review.

It is deliberately independent from all generation logic — it only reads,
never writes to the engine outputs, and never modifies the analytical graph.

Checks performed:
  1.  Nonexistent evidence references (exhibit IDs not in case vault)
  2.  Unsupported factual claims (assertions without grounded observations)
  3.  Conflicting timestamps between events
  4.  Candidate entity inconsistency (same entity in two places simultaneously)
  5.  Item-count inconsistency (financial shortage vs. visual/physical count)
  6.  Scenario vs. reconstruction mismatch (hypothesis steps unsupported by X03)
  7.  Unexplained breaks or gaps
  8.  Unsupported causal inferences
  9.  Provenance completeness (every finding traces to an exhibit)
  10. Historical-knowledge contamination (prior case data cited as current evidence)
  11. Cross-engine output contradictions

Possible determinations:
  VERIFIED                — All checks passed with no issues.
  VERIFIED_WITH_WARNINGS  — Minor issues; safe to proceed with review notes.
  CONFLICT_FOUND          — Hard contradiction between engine outputs.
  UNSUPPORTED_OUTPUT      — Claim(s) without evidentiary grounding.
  REANALYSIS_REQUIRED     — Structural failures; recommend re-running affected engines.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Verification Determination Enum
# ---------------------------------------------------------------------------

class FinalVerificationDetermination(str, Enum):
    VERIFIED                = "VERIFIED"
    VERIFIED_WITH_WARNINGS  = "VERIFIED_WITH_WARNINGS"
    CONFLICT_FOUND          = "CONFLICT_FOUND"
    UNSUPPORTED_OUTPUT      = "UNSUPPORTED_OUTPUT"
    REANALYSIS_REQUIRED     = "REANALYSIS_REQUIRED"
    HARD_INTEGRITY_VIOLATION = "HARD_INTEGRITY_VIOLATION"



# ---------------------------------------------------------------------------
# Verification Issue dataclass
# ---------------------------------------------------------------------------

@dataclass
class VerificationIssue:
    check_id: str               # e.g. "CHECK_01_EVIDENCE_REFS"
    severity: str               # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    description: str
    affected_engines: List[str] = field(default_factory=list)
    affected_outputs: List[str] = field(default_factory=list)
    target_stage_for_reanalysis: str = ""
    reanalysis_target_engines: List[str] = field(default_factory=list)
    recommendation: str = ""


# ---------------------------------------------------------------------------
# Final Verification Result
# ---------------------------------------------------------------------------

@dataclass
class FinalVerificationResult:
    determination: FinalVerificationDetermination
    issues: List[VerificationIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    reanalysis_plan: Dict[str, List[str]] = field(default_factory=dict)
    recommended_reanalysis_engines: List[str] = field(default_factory=list)
    verification_timestamp: Optional[str] = None
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        from datetime import datetime, timezone
        rec_engines = set(self.recommended_reanalysis_engines)
        for i in self.issues:
            rec_engines.update(i.reanalysis_target_engines or i.affected_engines)

        return {
            "determination": self.determination.value,
            "summary": self.summary,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "issue_count": len(self.issues),
            "warning_count": len(self.warnings),
            "reanalysis_plan": self.reanalysis_plan,
            "recommended_reanalysis_engines": sorted(list(rec_engines)),
            "issues": [
                {
                    "check_id": i.check_id,
                    "severity": i.severity,
                    "description": i.description,
                    "affected_engines": i.affected_engines,
                    "target_stage_for_reanalysis": i.target_stage_for_reanalysis or "DEPARTMENTAL_ANALYSIS",
                    "reanalysis_target_engines": i.reanalysis_target_engines or i.affected_engines,
                    "recommendation": i.recommendation,
                }
                for i in self.issues
            ],
            "warnings": self.warnings,
            "verification_timestamp": (
                self.verification_timestamp or datetime.now(timezone.utc).isoformat()
            ),
            "fabrication_guard": (
                "INDEPENDENT_AUDITOR: This verification was performed by an engine "
                "that has read-only access. No engine outputs have been modified."
            ),
        }


# ---------------------------------------------------------------------------
# Unsupported causal language patterns
# ---------------------------------------------------------------------------

_CAUSAL_PHRASES = [
    "must have stolen", "must have taken", "was the thief",
    "proves guilt", "confirms theft", "committed the theft",
    "was responsible for the loss", "caused the inventory shortage",
    "removed the item from", "definitely stole",
]

_HISTORICAL_CONTAMINATION_PHRASES = [
    "in previous cases", "historically", "past incidents show",
    "prior investigations indicate", "similar past cases",
    "based on prior knowledge",
]


# ---------------------------------------------------------------------------
# Final Verification Engine
# ---------------------------------------------------------------------------

class FinalVerificationEngine:
    """
    Independent read-only auditor of the complete engine output graph.

    Usage:
        fve = FinalVerificationEngine()
        result = fve.verify(
            engine_outputs=context.prior_results,
            valid_evidence_ids={ev.id for ev in evidence_list},
            case_id=case.id
        )
    """

    def verify(
        self,
        engine_outputs: Dict[str, Any],   # engine_id → EngineExecutionRecord
        valid_evidence_ids: Set[str],
        case_id: str,
        analysis_version: int = 1,
    ) -> FinalVerificationResult:
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        checks_passed: List[str] = []
        checks_failed: List[str] = []

        # Collect all outputs as flat list for cross-check convenience
        all_outputs: List[Dict[str, Any]] = []
        engine_output_map: Dict[str, List[Dict]] = {}
        for eid, rec in engine_outputs.items():
            outs = getattr(rec, "outputs", None) or []
            engine_output_map[eid] = [o for o in outs if isinstance(o, dict)]
            all_outputs.extend(engine_output_map.get(eid, []))

        # --- INTEGRITY CHECK: Case Scope Mismatch ---
        issues_scope, warn_scope = self._check_case_scope(engine_outputs, case_id)
        _record(issues, warnings, checks_passed, checks_failed, "CASE_SCOPE_MISMATCH", issues_scope, warn_scope)

        # --- INTEGRITY CHECK: Analysis Version Mismatch ---
        issues_ver, warn_ver = self._check_analysis_version(engine_outputs, analysis_version)
        _record(issues, warnings, checks_passed, checks_failed, "ANALYSIS_VERSION_MISMATCH", issues_ver, warn_ver)

        # --- INTEGRITY CHECK: Correlation Count Invariant (X06 vs X03) ---
        issues_corr, warn_corr = self._check_correlation_count_integrity(engine_output_map, case_id, analysis_version)
        _record(issues, warnings, checks_passed, checks_failed, "CORRELATION_COUNT_MISMATCH", issues_corr, warn_corr)

        # --- INTEGRITY CHECK: Unknown Entity References (R01 vs X01) ---
        issues_ent, warn_ent = self._check_unknown_entity_references(engine_output_map)
        _record(issues, warnings, checks_passed, checks_failed, "UNKNOWN_ENTITY_REFERENCE", issues_ent, warn_ent)

        # --- INTEGRITY CHECK: Stale Engine Output ---
        issues_stale, warn_stale = self._check_stale_engine_outputs(engine_outputs, analysis_version)
        _record(issues, warnings, checks_passed, checks_failed, "STALE_ENGINE_OUTPUT", issues_stale, warn_stale)

        # --- INTEGRITY CHECK: Cross-Case Evidence Reference ---
        issues_ccev, warn_ccev = self._check_cross_case_evidence_refs(engine_output_map, valid_evidence_ids)
        _record(issues, warnings, checks_passed, checks_failed, "CROSS_CASE_EVIDENCE_REFERENCE", issues_ccev, warn_ccev)

        # --- INTEGRITY CHECK: Modality Availability vs Engine Success ---
        issues_mod, warn_mod = self._check_evidence_modality_contradiction(engine_output_map, engine_outputs)
        _record(issues, warnings, checks_passed, checks_failed, "EVIDENCE_MODALITY_CONTRADICTION", issues_mod, warn_mod)

        # --- CHECK 01: Nonexistent Evidence References ---
        issues01, warn01 = self._check_evidence_refs(engine_output_map, valid_evidence_ids)
        _record(issues, warnings, checks_passed, checks_failed, "CHECK_01_EVIDENCE_REFS", issues01, warn01)

        # --- CHECK 02: Unsupported Factual Claims ---
        issues02, warn02 = self._check_unsupported_claims(engine_output_map)
        _record(issues, warnings, checks_passed, checks_failed, "CHECK_02_UNSUPPORTED_CLAIMS", issues02, warn02)

        # --- CHECK 03: Conflicting Timestamps ---
        issues03, warn03 = self._check_timestamp_conflicts(engine_output_map)
        _record(issues, warnings, checks_passed, checks_failed, "CHECK_03_TIMESTAMP_CONFLICTS", issues03, warn03)

        # --- CHECK 04: Entity Inconsistency (simultaneous location) ---
        issues04, warn04 = self._check_entity_consistency(all_outputs)
        _record(issues, warnings, checks_passed, checks_failed, "CHECK_04_ENTITY_CONSISTENCY", issues04, warn04)

        # --- CHECK 05: Item Count Inconsistency ---
        issues05, warn05 = self._check_item_count(engine_output_map)
        _record(issues, warnings, checks_passed, checks_failed, "CHECK_05_ITEM_COUNT", issues05, warn05)

        # --- CHECK 06: Scenario vs. Reconstruction Mismatch ---
        issues06, warn06 = self._check_scenario_reconstruction_alignment(engine_output_map)
        _record(issues, warnings, checks_passed, checks_failed, "CHECK_06_SCENARIO_ALIGNMENT", issues06, warn06)

        # --- CHECK 07: Unexplained Gaps ---
        issues07, warn07 = self._check_unexplained_gaps(engine_output_map)
        _record(issues, warnings, checks_passed, checks_failed, "CHECK_07_UNEXPLAINED_GAPS", issues07, warn07)

        # --- CHECK 08: Unsupported Causal Inferences ---
        issues08, warn08 = self._check_causal_inference(engine_output_map)
        _record(issues, warnings, checks_passed, checks_failed, "CHECK_08_CAUSAL_INFERENCE", issues08, warn08)

        # --- CHECK 09: Provenance Completeness ---
        issues09, warn09 = self._check_provenance_completeness(engine_output_map, valid_evidence_ids)
        _record(issues, warnings, checks_passed, checks_failed, "CHECK_09_PROVENANCE", issues09, warn09)

        # --- CHECK 10: Historical Knowledge Contamination ---
        issues10, warn10 = self._check_historical_contamination(engine_output_map)
        _record(issues, warnings, checks_passed, checks_failed, "CHECK_10_CONTAMINATION", issues10, warn10)

        # --- CHECK 11: Cross-Engine Contradiction ---
        issues11, warn11 = self._check_cross_engine_contradictions(engine_output_map)
        _record(issues, warnings, checks_passed, checks_failed, "CHECK_11_CROSS_ENGINE", issues11, warn11)

        # --- Determine final verdict and reanalysis plan ---
        determination, summary = _determine_verdict(issues, warnings)

        reanalysis_plan: Dict[str, List[str]] = {}
        rec_engines: Set[str] = set()
        for issue in issues:
            targets = issue.reanalysis_target_engines or issue.affected_engines
            rec_engines.update(targets)
            stage = issue.target_stage_for_reanalysis or "DEPARTMENTAL_ANALYSIS"
            reanalysis_plan.setdefault(stage, []).extend(targets)

        reanalysis_plan = {k: sorted(list(set(v))) for k, v in reanalysis_plan.items()}

        return FinalVerificationResult(
            determination=determination,
            issues=issues,
            warnings=warnings,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            reanalysis_plan=reanalysis_plan,
            recommended_reanalysis_engines=sorted(list(rec_engines)),
            summary=summary,
        )

    # -----------------------------------------------------------------------
    # Integrity Check implementations (Case Scope, Version, Accounting)
    # -----------------------------------------------------------------------

    def _check_case_scope(
        self,
        engine_outputs: Dict[str, Any],
        target_case_id: str
    ) -> tuple[List[VerificationIssue], List[str]]:
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        for eid, rec in engine_outputs.items():
            r_case_id = getattr(rec, "case_id", None)
            if r_case_id and r_case_id != target_case_id:
                issues.append(VerificationIssue(
                    check_id="CASE_SCOPE_MISMATCH",
                    severity="CRITICAL",
                    description=f"Engine record for '{eid}' belongs to foreign case '{r_case_id}', expected '{target_case_id}'.",
                    affected_engines=[eid],
                    reanalysis_target_engines=[eid],
                    recommendation="Purge cross-case artifact and re-run analysis in isolated case context."
                ))
            outs = getattr(rec, "outputs", []) or []
            for out in outs:
                if isinstance(out, dict):
                    o_case_id = out.get("case_id")
                    if o_case_id and o_case_id != target_case_id:
                        issues.append(VerificationIssue(
                            check_id="CASE_SCOPE_MISMATCH",
                            severity="CRITICAL",
                            description=f"Engine '{eid}' output contains item from foreign case '{o_case_id}'.",
                            affected_engines=[eid],
                            reanalysis_target_engines=[eid],
                            recommendation="Purge cross-case artifact and re-run analysis in isolated case context."
                        ))
        return issues, warnings

    def _check_analysis_version(
        self,
        engine_outputs: Dict[str, Any],
        target_analysis_version: int
    ) -> tuple[List[VerificationIssue], List[str]]:
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        for eid, rec in engine_outputs.items():
            r_version = getattr(rec, "analysis_version", None)
            if r_version is not None and r_version != target_analysis_version:
                issues.append(VerificationIssue(
                    check_id="ANALYSIS_VERSION_MISMATCH",
                    severity="CRITICAL",
                    description=f"Engine record for '{eid}' has analysis_version {r_version}, expected active version {target_analysis_version}.",
                    affected_engines=[eid],
                    reanalysis_target_engines=[eid],
                    recommendation="Stale analysis version detected. Discard prior version results and re-run analysis."
                ))
            outs = getattr(rec, "outputs", []) or []
            for out in outs:
                if isinstance(out, dict):
                    o_version = out.get("analysis_version")
                    if o_version is not None and o_version != target_analysis_version:
                        issues.append(VerificationIssue(
                            check_id="ANALYSIS_VERSION_MISMATCH",
                            severity="CRITICAL",
                            description=f"Engine '{eid}' output has stale analysis_version {o_version}, expected active version {target_analysis_version}.",
                            affected_engines=[eid],
                            reanalysis_target_engines=[eid],
                            recommendation="Stale analysis version detected in payload. Discard prior version results."
                        ))
        return issues, warnings

    def _check_correlation_count_integrity(
        self,
        engine_output_map: Dict[str, List[Dict]],
        case_id: str,
        analysis_version: int
    ) -> tuple[List[VerificationIssue], List[str]]:
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        x06_outs = engine_output_map.get("X06", [])
        x03_outs = engine_output_map.get("X03", [])
        if x06_outs:
            x06_corr = x06_outs[0].get("correlated_event_count")
            x03_valid = [
                c for c in x03_outs
                if isinstance(c, dict) and c.get("correlation_type") not in ("INSUFFICIENT_MULTI_MODALITY", "TIMELINE_BREAK")
            ]
            x03_corr = len(x03_valid)
            if x06_corr is not None and x06_corr != x03_corr:
                issues.append(VerificationIssue(
                    check_id="CORRELATION_COUNT_MISMATCH",
                    severity="CRITICAL",
                    description=(
                        f"Accounting contradiction: X06 recorded {x06_corr} correlated events, "
                        f"but X03 produced {x03_corr} for case '{case_id}' version {analysis_version}."
                    ),
                    affected_engines=["X06", "X03"],
                    reanalysis_target_engines=["X06"],
                    recommendation="Reconcile X06 sufficiency input with X03 output and re-run X06."
                ))
        return issues, warnings

    def _check_unknown_entity_references(
        self,
        engine_output_map: Dict[str, List[Dict]]
    ) -> tuple[List[VerificationIssue], List[str]]:
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        x01_outs = engine_output_map.get("X01", [])
        known_entity_ids = set()
        known_entity_tokens = set()
        for ent in x01_outs:
            eid = ent.get("entity_id")
            if eid:
                known_entity_ids.add(eid)
                known_entity_tokens.add(eid)
            label = ent.get("candidate_label", "")
            for tok in ["P1", "P2", "V1", "V2", "ITEM1", "ITEM2"]:
                if tok in label or (eid and tok in eid):
                    known_entity_tokens.add(tok)

        for eid in ("R01", "R02", "R03", "R04"):
            outs = engine_output_map.get(eid, [])
            for out in outs:
                deps = out.get("entity_link_dependence") or []
                for dep in deps:
                    if dep not in known_entity_ids and dep not in known_entity_tokens:
                        issues.append(VerificationIssue(
                            check_id="UNKNOWN_ENTITY_REFERENCE",
                            severity="CRITICAL",
                            description=(
                                f"Engine '{eid}' references candidate entity '{dep}' "
                                "which does not exist in X01 candidate entities output."
                            ),
                            affected_engines=[eid],
                            reanalysis_target_engines=[eid],
                            recommendation="Remove unverified entity reference and bind only to candidate entities resolved by X01."
                        ))

                narrative = str(out.get("narrative") or "")
                lower_narr = narrative.lower()
                for tok in ["P1", "V1", "ITEM1"]:
                    if tok not in known_entity_tokens:
                        tok_lower = tok.lower()
                        if (
                            f"entity {tok_lower}" in lower_narr
                            or f"candidate entity {tok_lower}" in lower_narr
                            or f"({tok_lower})" in lower_narr
                            or f"({tok})" in narrative
                            or f" {tok} " in narrative
                            or f" {tok}," in narrative
                            or f" {tok}." in narrative
                        ):
                            issues.append(VerificationIssue(
                                check_id="UNKNOWN_ENTITY_REFERENCE",
                                severity="CRITICAL",
                                description=(
                                    f"Engine '{eid}' narrative references unextracted entity '{tok}' "
                                    "which was not generated by X01."
                                ),
                                affected_engines=[eid],
                                reanalysis_target_engines=[eid],
                                recommendation="Remove unextracted entity reference from hypothesis narrative."
                            ))
                            break
        return issues, warnings

    def _check_stale_engine_outputs(
        self,
        engine_outputs: Dict[str, Any],
        target_analysis_version: int
    ) -> tuple[List[VerificationIssue], List[str]]:
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        for eid, rec in engine_outputs.items():
            r_ver = getattr(rec, "analysis_version", target_analysis_version)
            if r_ver < target_analysis_version:
                issues.append(VerificationIssue(
                    check_id="STALE_ENGINE_OUTPUT",
                    severity="CRITICAL",
                    description=f"Stale output: Engine '{eid}' result is from analysis version {r_ver} (current is {target_analysis_version}).",
                    affected_engines=[eid],
                    reanalysis_target_engines=[eid],
                    recommendation="Re-run engine under active analysis version."
                ))
        return issues, warnings

    def _check_cross_case_evidence_refs(
        self,
        engine_output_map: Dict[str, List[Dict]],
        valid_evidence_ids: Set[str]
    ) -> tuple[List[VerificationIssue], List[str]]:
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        for eid, outputs in engine_output_map.items():
            for out in outputs:
                for field_name in ("evidence_id", "supporting_evidence_citations", "cited_evidence", "evidence_ids"):
                    raw = out.get(field_name)
                    if not raw:
                        continue
                    refs = raw if isinstance(raw, list) else [raw]
                    for ref in refs:
                        ref_str = str(ref)
                        if len(ref_str) == 36 and ref_str not in valid_evidence_ids:
                            issues.append(VerificationIssue(
                                check_id="CROSS_CASE_EVIDENCE_REFERENCE",
                                severity="CRITICAL",
                                description=f"Engine '{eid}' references foreign or nonexistent exhibit '{ref_str}'.",
                                affected_engines=[eid],
                                reanalysis_target_engines=[eid],
                                recommendation="Remove cross-case evidence reference and restrict to active case exhibits."
                            ))
        return issues, warnings

    def _check_evidence_modality_contradiction(
        self,
        engine_output_map: Dict[str, List[Dict]],
        engine_outputs: Dict[str, Any]
    ) -> tuple[List[VerificationIssue], List[str]]:
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        x04_outs = engine_output_map.get("X04", [])
        
        has_fin_gap = any(
            isinstance(g, dict) and "financial" in str(g.get("description", "")).lower() and "absent" in str(g.get("description", "")).lower()
            for g in x04_outs
        )
        fi_succeeded = any(
            rec and getattr(rec, "status", None) in ("SUCCESS", "PARTIAL")
            for eid, rec in engine_outputs.items() if eid.startswith("FI")
        )
        if has_fin_gap and fi_succeeded:
            issues.append(VerificationIssue(
                check_id="EVIDENCE_MODALITY_CONTRADICTION",
                severity="CRITICAL",
                description="Hard state contradiction: X04 reports financial modality absent, but financial engines (FI01-FI06) completed successfully in the same run.",
                affected_engines=["X04", "FI01", "FI02"],
                reanalysis_target_engines=["X04"],
                recommendation="Derive modality availability from authoritative AnalysisRunContext manifest."
            ))
        return issues, warnings
    # -----------------------------------------------------------------------

    def _check_evidence_refs(
        self,
        engine_output_map: Dict[str, List[Dict]],
        valid_ids: Set[str],
    ) -> tuple[List[VerificationIssue], List[str]]:
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        for eid, outputs in engine_output_map.items():
            for out in outputs:
                for field_name in ("evidence_id", "supporting_evidence_citations", "cited_evidence"):
                    raw = out.get(field_name)
                    if not raw:
                        continue
                    refs = raw if isinstance(raw, list) else [raw]
                    for ref in refs:
                        ref_str = str(ref)
                        # Only UUID-shaped strings are treated as exhibit IDs
                        if len(ref_str) == 36 and ref_str not in valid_ids:
                            issues.append(VerificationIssue(
                                check_id="CHECK_01_EVIDENCE_REFS",
                                severity="CRITICAL",
                                description=f"Engine '{eid}' references nonexistent exhibit '{ref_str}'.",
                                affected_engines=[eid],
                                recommendation="Remove or correct the invalid evidence reference.",
                            ))
        return issues, warnings

    def _check_unsupported_claims(
        self, engine_output_map: Dict[str, List[Dict]]
    ) -> tuple[List[VerificationIssue], List[str]]:
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        for eid, outputs in engine_output_map.items():
            if eid not in ("R01", "R02", "R03"):
                continue
            for out in outputs:
                citations = (
                    out.get("supporting_evidence_citations") or
                    out.get("supporting_claims") or []
                )
                if not citations:
                    issues.append(VerificationIssue(
                        check_id="CHECK_02_UNSUPPORTED_CLAIMS",
                        severity="HIGH",
                        description=(
                            f"Engine '{eid}' produced a claim/hypothesis without "
                            "any supporting evidence citations."
                        ),
                        affected_engines=[eid],
                        recommendation="Ensure R01 hypothesis generator cites verified observations.",
                    ))
        return issues, warnings

    def _check_timestamp_conflicts(
        self, engine_output_map: Dict[str, List[Dict]]
    ) -> tuple[List[VerificationIssue], List[str]]:
        """Flag major retrograde timestamp jumps within the same engine's outputs."""
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        for eid, outputs in engine_output_map.items():
            prev_ts_str = None
            for idx, out in enumerate(outputs):
                ts = str(out.get("timestamp") or out.get("observed_time") or "")
                if ts and prev_ts_str and ts < prev_ts_str:
                    warnings.append(
                        f"Engine '{eid}' output[{idx}] timestamp '{ts}' precedes "
                        f"previous '{prev_ts_str}' — possible clock drift or ordering error."
                    )
                if ts:
                    prev_ts_str = ts
        return issues, warnings

    def _check_entity_consistency(
        self, all_outputs: List[Dict]
    ) -> tuple[List[VerificationIssue], List[str]]:
        """Detect if the same entity ID appears in two different locations at the same timestamp."""
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        entity_location_map: Dict[str, Dict[str, str]] = {}  # entity_id → {ts: location}
        for out in all_outputs:
            entity_id = out.get("entity_id")
            ts = str(out.get("timestamp") or out.get("observed_time") or "")
            location = out.get("zone") or out.get("location") or ""
            if entity_id and ts and location:
                existing = entity_location_map.get(entity_id, {})
                if ts in existing and existing[ts] != location:
                    issues.append(VerificationIssue(
                        check_id="CHECK_04_ENTITY_CONSISTENCY",
                        severity="HIGH",
                        description=(
                            f"Entity '{entity_id}' recorded at two different locations "
                            f"('{existing[ts]}' and '{location}') at timestamp '{ts}'."
                        ),
                        recommendation="Review camera synchronization or Re-ID assignment for this entity.",
                    ))
                existing[ts] = location
                entity_location_map[entity_id] = existing
        return issues, warnings

    def _check_item_count(
        self, engine_output_map: Dict[str, List[Dict]]
    ) -> tuple[List[VerificationIssue], List[str]]:
        """Check FI02 shortage counts against any visual item counts from F03/I09."""
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        fi02_outputs = engine_output_map.get("FI02", [])
        for fi in fi02_outputs:
            shortage = fi.get("shortage_units") or fi.get("missing_units")
            sku = fi.get("sku") or fi.get("item_id")
            if shortage is not None and sku:
                # Look for visual count in F03 or I09
                for visual_eid in ("F03", "I09"):
                    for out in engine_output_map.get(visual_eid, []):
                        if str(sku) in str(out):
                            visual_count = out.get("item_count") or out.get("count")
                            if visual_count is not None and abs(visual_count - shortage) > 5:
                                warnings.append(
                                    f"SKU '{sku}': Financial shortage={shortage} units "
                                    f"vs. visual count from {visual_eid}={visual_count}. "
                                    "Reconciliation advised."
                                )
        return issues, warnings

    def _check_scenario_reconstruction_alignment(
        self, engine_output_map: Dict[str, List[Dict]]
    ) -> tuple[List[VerificationIssue], List[str]]:
        """Verify that R01 hypothesis steps cite X03 correlations where corroborated."""
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        r01_outputs = engine_output_map.get("R01", [])
        x03_corr_ids = {
            out.get("correlation_id") for out in engine_output_map.get("X03", [])
            if out.get("correlation_id")
        }
        for hyp in r01_outputs:
            seq = hyp.get("sequence") or hyp.get("steps") or []
            for step in seq:
                cited_corr = step.get("correlation_ref")
                if cited_corr and cited_corr not in x03_corr_ids:
                    issues.append(VerificationIssue(
                        check_id="CHECK_06_SCENARIO_ALIGNMENT",
                        severity="MEDIUM",
                        description=(
                            f"Hypothesis step references correlation '{cited_corr}' "
                            "not present in X03 outputs."
                        ),
                        affected_engines=["R01", "X03"],
                        recommendation="Ensure hypothesis steps only reference verified X03 correlations.",
                    ))
        return issues, warnings

    def _check_unexplained_gaps(
        self, engine_output_map: Dict[str, List[Dict]]
    ) -> tuple[List[VerificationIssue], List[str]]:
        """Warn if X04 found gaps that no hypothesis or gap-conflict record addresses."""
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        x04_outputs = engine_output_map.get("X04", [])
        critical_gaps = [g for g in x04_outputs if g.get("significance") == "CRITICAL"]
        if critical_gaps and not engine_output_map.get("R01"):
            for g in critical_gaps:
                warnings.append(
                    f"Critical gap '{g.get('gap_id', 'UNKNOWN')}' ({g.get('description', '')}) "
                    "was detected by X04 but no reconstruction hypotheses address it."
                )
        return issues, warnings

    def _check_causal_inference(
        self, engine_output_map: Dict[str, List[Dict]]
    ) -> tuple[List[VerificationIssue], List[str]]:
        """Detect prohibited causal phrases in any engine outputs."""
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        for eid, outputs in engine_output_map.items():
            for out in outputs:
                text = " ".join(str(v) for v in out.values() if isinstance(v, str)).lower()
                for phrase in _CAUSAL_PHRASES:
                    if phrase in text:
                        issues.append(VerificationIssue(
                            check_id="CHECK_08_CAUSAL_INFERENCE",
                            severity="HIGH",
                            description=(
                                f"Engine '{eid}' output contains unsupported causal assertion: '{phrase}'."
                            ),
                            affected_engines=[eid],
                            recommendation="Remove or reclassify the assertion as a speculative observation.",
                        ))
                        break
        return issues, warnings

    def _check_provenance_completeness(
        self,
        engine_output_map: Dict[str, List[Dict]],
        valid_ids: Set[str],
    ) -> tuple[List[VerificationIssue], List[str]]:
        """Every output from R01 must carry at least one evidence citation."""
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        for eid in ("R01",):
            for out in engine_output_map.get(eid, []):
                has_provenance = bool(
                    out.get("supporting_evidence_citations") or
                    out.get("provenance") or
                    out.get("supporting_claims")
                )
                if not has_provenance:
                    issues.append(VerificationIssue(
                        check_id="CHECK_09_PROVENANCE",
                        severity="HIGH",
                        description=(
                            f"Engine '{eid}' produced an output with no provenance record. "
                            "Every finding must trace to at least one exhibit."
                        ),
                        affected_engines=[eid],
                        recommendation="Ensure reconstruction engine cites all source observations.",
                    ))
        return issues, warnings

    def _check_historical_contamination(
        self, engine_output_map: Dict[str, List[Dict]]
    ) -> tuple[List[VerificationIssue], List[str]]:
        """Detect language indicating historical case knowledge used as current evidence."""
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        for eid, outputs in engine_output_map.items():
            for out in outputs:
                text = " ".join(str(v) for v in out.values() if isinstance(v, str)).lower()
                for phrase in _HISTORICAL_CONTAMINATION_PHRASES:
                    if phrase in text:
                        issues.append(VerificationIssue(
                            check_id="CHECK_10_CONTAMINATION",
                            severity="CRITICAL",
                            description=(
                                f"Engine '{eid}' output contains historical case knowledge reference: '{phrase}'. "
                                "Historical patterns must not be cited as evidence in the current case."
                            ),
                            affected_engines=[eid],
                            recommendation="Remove all references to prior case data from analytical outputs.",
                        ))
                        break
        return issues, warnings

    def _check_cross_engine_contradictions(
        self, engine_output_map: Dict[str, List[Dict]]
    ) -> tuple[List[VerificationIssue], List[str]]:
        """Flag if X05 found HARD_CONTRADICTION class conflicts that R01 ignored."""
        issues: List[VerificationIssue] = []
        warnings: List[str] = []
        x05_outputs = engine_output_map.get("X05", [])
        hard_contradictions = [
            c for c in x05_outputs
            if c.get("conflict_class") == "HARD_CONTRADICTION"
        ]
        r01_outputs = engine_output_map.get("R01", [])
        if hard_contradictions and r01_outputs:
            for hc in hard_contradictions:
                hc_id = hc.get("conflict_id") or hc.get("description", "")[:50]
                cited_in_r01 = any(
                    hc_id in str(hyp.get("unresolved_conflicts", []))
                    for hyp in r01_outputs
                )
                if not cited_in_r01:
                    warnings.append(
                        f"HARD_CONTRADICTION '{hc_id}' from X05 was not addressed "
                        "in any R01 hypothesis as an unresolved conflict."
                    )
        return issues, warnings


# ---------------------------------------------------------------------------
# Verdict determination
# ---------------------------------------------------------------------------

def _determine_verdict(
    issues: List[VerificationIssue],
    warnings: List[str],
) -> tuple[FinalVerificationDetermination, str]:
    critical = [i for i in issues if i.severity == "CRITICAL"]
    high = [i for i in issues if i.severity == "HIGH"]
    medium = [i for i in issues if i.severity == "MEDIUM"]

    hard_invariants = {
        "CASE_SCOPE_MISMATCH",
        "ANALYSIS_VERSION_MISMATCH",
        "CORRELATION_COUNT_MISMATCH",
        "UNKNOWN_ENTITY_REFERENCE",
        "STALE_ENGINE_OUTPUT",
        "CROSS_CASE_EVIDENCE_REFERENCE",
        "EVIDENCE_MODALITY_CONTRADICTION",
    }
    hard_violations = [i for i in critical if i.check_id in hard_invariants]
    if hard_violations:
        return (
            FinalVerificationDetermination.HARD_INTEGRITY_VIOLATION,
            f"{len(hard_violations)} hard integrity violation(s) detected: {'; '.join(v.description for v in hard_violations)}. Report publication blocked.",
        )

    if critical:
        return (
            FinalVerificationDetermination.REANALYSIS_REQUIRED,
            f"{len(critical)} critical issue(s) detected. Reanalysis of affected engines required.",
        )
    if any(i.check_id in ("CHECK_10_CONTAMINATION", "CHECK_01_EVIDENCE_REFS") for i in high):
        return (
            FinalVerificationDetermination.REANALYSIS_REQUIRED,
            "Evidence reference or contamination failure requires reanalysis.",
        )
    if any(i.check_id == "CHECK_04_ENTITY_CONSISTENCY" for i in issues):
        return (
            FinalVerificationDetermination.CONFLICT_FOUND,
            "Entity location inconsistency detected between engine outputs.",
        )
    if high:
        return (
            FinalVerificationDetermination.UNSUPPORTED_OUTPUT,
            f"{len(high)} high-severity issue(s); outputs contain unsupported claims.",
        )
    if medium or warnings:
        return (
            FinalVerificationDetermination.VERIFIED_WITH_WARNINGS,
            f"Output verified with {len(medium)} medium issues and {len(warnings)} warning(s).",
        )
    return (
        FinalVerificationDetermination.VERIFIED,
        "All 11 verification checks passed. Output is ready for human specialist review.",
    )


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _record(
    all_issues: List[VerificationIssue],
    all_warnings: List[str],
    passed: List[str],
    failed: List[str],
    check_name: str,
    new_issues: List[VerificationIssue],
    new_warnings: List[str],
) -> None:
    all_issues.extend(new_issues)
    all_warnings.extend(new_warnings)
    if new_issues:
        failed.append(check_name)
    else:
        passed.append(check_name)


# Singleton
final_verification_engine = FinalVerificationEngine()
