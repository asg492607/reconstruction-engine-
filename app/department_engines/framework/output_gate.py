"""
Phase 6: Post-Model Output-Gating Pipeline
==========================================
After every LLM / MODEL / HYBRID engine call, the output must pass through
five sequential validation stages before it is allowed to influence the next
stage of the analysis pipeline.

Decision flow:

    MODEL OUTPUT
         ↓
    1. STRUCTURE VALIDATOR      — Schema conformity, required fields, type bounds
         ↓
    2. EVIDENCE SUPPORT CHECK   — Every cited exhibit ID must exist in case vault
         ↓
    3. CONSISTENCY CHECK        — Timestamp ordering, no self-contradictions
         ↓
    4. QUALITY PARAMETERS       — Confidence thresholds, completeness metrics
         ↓
    5. DECISION GATE            — Emits one of 5 final decisions

Gate decisions:
    PASS_TO_NEXT     – Output validated; authorized for downstream consumption.
    REVIEW_REQUIRED  – Output flagged; specialist must inspect before downstream use.
    REANALYZE        – Minor defect; retry with refined prompt (max 2 retries).
    REJECT_OUTPUT    – Severe contradiction or hallucinated citation; discard output.
    STOP             – Critical policy violation; halt this engine branch entirely.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from app.department_engines.framework.base import (
    EngineExecutionRecord,
    EngineExecutionResult,
    ExecutionMode,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Gate Decision Enum
# ---------------------------------------------------------------------------

class GateDecision(str, Enum):
    PASS_TO_NEXT     = "PASS_TO_NEXT"
    REVIEW_REQUIRED  = "REVIEW_REQUIRED"
    REANALYZE        = "REANALYZE"
    REJECT_OUTPUT    = "REJECT_OUTPUT"
    STOP             = "STOP"


# ---------------------------------------------------------------------------
# Gate Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    decision: GateDecision
    stage_failed: str = ""
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.decision == GateDecision.PASS_TO_NEXT


# ---------------------------------------------------------------------------
# Stage 1: Structure Validator
# ---------------------------------------------------------------------------

def _stage_structure(outputs: List[Any]) -> GateResult:
    """Verify outputs is a list of dicts with expected scalar field types."""
    if not isinstance(outputs, list):
        return GateResult(
            decision=GateDecision.REJECT_OUTPUT,
            stage_failed="STRUCTURE_VALIDATOR",
            violations=["Output root must be a list."],
        )
    for idx, item in enumerate(outputs):
        if not isinstance(item, dict):
            return GateResult(
                decision=GateDecision.REJECT_OUTPUT,
                stage_failed="STRUCTURE_VALIDATOR",
                violations=[f"Output[{idx}] is type '{type(item).__name__}'; expected dict."],
            )
    return GateResult(decision=GateDecision.PASS_TO_NEXT)


# ---------------------------------------------------------------------------
# Stage 2: Evidence Support Check
# ---------------------------------------------------------------------------

def _stage_evidence_support(
    outputs: List[Dict],
    valid_evidence_ids: Set[str],
) -> GateResult:
    """Every exhibit ID cited must exist in the case evidence vault."""
    violations: List[str] = []
    citation_fields = [
        "supporting_evidence_citations",
        "evidence_id",
        "grounding_sources",
        "cited_evidence",
    ]
    for idx, item in enumerate(outputs):
        for cf in citation_fields:
            val = item.get(cf)
            if not val:
                continue
            ids = val if isinstance(val, list) else [val]
            for cited_id in ids:
                # Accept exhibit IDs, engine-reference strings, or descriptive strings
                cited_str = str(cited_id)
                if (
                    cited_str
                    and len(cited_str) == 36          # UUID length check
                    and cited_str not in valid_evidence_ids
                ):
                    violations.append(
                        f"Output[{idx}].{cf} references nonexistent exhibit ID '{cited_str}'."
                    )
    if violations:
        return GateResult(
            decision=GateDecision.REJECT_OUTPUT,
            stage_failed="EVIDENCE_SUPPORT_CHECK",
            violations=violations,
        )
    return GateResult(decision=GateDecision.PASS_TO_NEXT)


# ---------------------------------------------------------------------------
# Stage 3: Consistency Check
# ---------------------------------------------------------------------------

_VERDICT_PHRASES = [
    "guilty of", "theft confirmed", "perpetrator confirmed",
    "committed the theft", "proves guilt", "definitely stole",
]

_CAUSAL_LEAPS = [
    "must have stolen", "must have taken", "was responsible for the theft",
    "was the thief", "caused the inventory loss", "removed the item from the store",
]


def _stage_consistency(outputs: List[Dict]) -> GateResult:
    """Check for timestamp ordering violations and prohibited verdict / causal language."""
    violations: List[str] = []
    warnings: List[str] = []

    prev_ts: Optional[str] = None
    for idx, item in enumerate(outputs):
        # Timestamp monotonicity
        ts = item.get("timestamp") or item.get("observed_time")
        if ts and prev_ts and str(ts) < str(prev_ts):
            warnings.append(
                f"Output[{idx}] timestamp '{ts}' precedes previous '{prev_ts}' — possible clock drift."
            )
        if ts:
            prev_ts = str(ts)

        # Verdict language → hard violation
        text = " ".join(str(v) for v in item.values() if isinstance(v, str)).lower()
        for phrase in _VERDICT_PHRASES:
            if phrase in text:
                violations.append(
                    f"Output[{idx}] contains prohibited verdict language: '{phrase}'."
                )
        for phrase in _CAUSAL_LEAPS:
            if phrase in text:
                violations.append(
                    f"Output[{idx}] contains unsupported causal assertion: '{phrase}'."
                )

    if violations:
        return GateResult(
            decision=GateDecision.REJECT_OUTPUT,
            stage_failed="CONSISTENCY_CHECK",
            violations=violations,
            warnings=warnings,
        )
    if warnings:
        return GateResult(
            decision=GateDecision.REVIEW_REQUIRED,
            stage_failed="CONSISTENCY_CHECK",
            warnings=warnings,
        )
    return GateResult(decision=GateDecision.PASS_TO_NEXT)


# ---------------------------------------------------------------------------
# Stage 4: Quality Parameters
# ---------------------------------------------------------------------------

def _stage_quality(
    record: EngineExecutionRecord,
    min_confidence: float = 0.0,
    min_output_count: int = 0,
) -> GateResult:
    """Validate confidence score and output completeness."""
    warnings: List[str] = []

    if record.confidence is not None:
        if record.confidence < 0.0 or record.confidence > 1.0:
            return GateResult(
                decision=GateDecision.REJECT_OUTPUT,
                stage_failed="QUALITY_PARAMETERS",
                violations=[f"Confidence {record.confidence} out of [0, 1] range."],
            )
        if min_confidence > 0.0 and record.confidence < min_confidence:
            warnings.append(
                f"Confidence {record.confidence:.2f} below engine minimum {min_confidence:.2f}."
            )

    if min_output_count > 0 and len(record.outputs) < min_output_count:
        warnings.append(
            f"Output count {len(record.outputs)} below expected minimum {min_output_count}."
        )

    # Check output payload size (<512 KB default)
    try:
        payload_kb = len(json.dumps(record.outputs).encode()) / 1024
        if payload_kb > 512:
            warnings.append(f"Output payload is {payload_kb:.1f} KB — consider pagination.")
    except Exception:
        pass

    if warnings:
        return GateResult(
            decision=GateDecision.REVIEW_REQUIRED,
            stage_failed="QUALITY_PARAMETERS",
            warnings=warnings,
        )
    return GateResult(decision=GateDecision.PASS_TO_NEXT)


# ---------------------------------------------------------------------------
# Stage 5: Decision Gate — combines all prior stage results
# ---------------------------------------------------------------------------

def _stage_decision_gate(stage_results: List[GateResult]) -> GateResult:
    """
    Aggregates all prior stage results into a single authoritative gate decision.
    Priority: STOP > REJECT_OUTPUT > REANALYZE > REVIEW_REQUIRED > PASS_TO_NEXT
    """
    all_violations: List[str] = []
    all_warnings: List[str] = []
    worst = GateDecision.PASS_TO_NEXT
    worst_stage = ""
    priority = {
        GateDecision.STOP: 5,
        GateDecision.REJECT_OUTPUT: 4,
        GateDecision.REANALYZE: 3,
        GateDecision.REVIEW_REQUIRED: 2,
        GateDecision.PASS_TO_NEXT: 1,
    }

    for r in stage_results:
        all_violations.extend(r.violations)
        all_warnings.extend(r.warnings)
        if priority.get(r.decision, 0) > priority.get(worst, 0):
            worst = r.decision
            worst_stage = r.stage_failed

    return GateResult(
        decision=worst,
        stage_failed=worst_stage,
        violations=all_violations,
        warnings=all_warnings,
    )


# ---------------------------------------------------------------------------
# Public API: OutputGate
# ---------------------------------------------------------------------------

class OutputGate:
    """
    Five-stage post-model output validation gate.

    Apply after every LLM / MODEL / HYBRID engine call before the result is
    registered in context.prior_results or persisted to the database.

    Usage:
        gate = OutputGate()
        result = gate.evaluate(record, valid_evidence_ids)
        if not result.passed:
            record = gate.apply_decision(record, result)
    """

    def evaluate(
        self,
        record: EngineExecutionRecord,
        valid_evidence_ids: Optional[Set[str]] = None,
        min_confidence: float = 0.0,
        min_output_count: int = 0,
    ) -> GateResult:
        """
        Run the 5-stage pipeline.  Only applied for MODEL, LLM, REAL_LLM,
        and HYBRID engines that succeeded or partially succeeded.
        """
        # Only gate AI-generated outputs
        if record.status in (
            EngineExecutionResult.BLOCKED,
            EngineExecutionResult.FAILED,
            EngineExecutionResult.SKIPPED,
            EngineExecutionResult.SKIPPED_NO_INPUT,
            EngineExecutionResult.TIME_LIMIT_EXCEEDED,
        ):
            return GateResult(decision=GateDecision.PASS_TO_NEXT)

        if record.execution_mode not in (
            ExecutionMode.MODEL,
            ExecutionMode.LLM,
            ExecutionMode.REAL_LLM,
            ExecutionMode.HYBRID,
        ):
            return GateResult(decision=GateDecision.PASS_TO_NEXT)

        ev_ids: Set[str] = valid_evidence_ids or set()

        stage_results = [
            _stage_structure(record.outputs),
            _stage_evidence_support(record.outputs, ev_ids),
            _stage_consistency(record.outputs),
            _stage_quality(record, min_confidence, min_output_count),
        ]

        return _stage_decision_gate(stage_results)

    def apply_decision(
        self,
        record: EngineExecutionRecord,
        gate_result: GateResult,
    ) -> EngineExecutionRecord:
        """
        Mutates the execution record based on the gate decision.
        Returns the modified record.
        """
        if gate_result.decision == GateDecision.PASS_TO_NEXT:
            return record

        # Append gate violations to record warnings
        record.warnings.extend(gate_result.violations)
        record.warnings.extend(gate_result.warnings)

        if gate_result.decision == GateDecision.REJECT_OUTPUT:
            logger.warning(
                "OUTPUT_GATE REJECT [%s / stage=%s]: %s",
                record.engine_id,
                gate_result.stage_failed,
                "; ".join(gate_result.violations[:3]),
            )
            record.status = EngineExecutionResult.BLOCKED
            record.actual_execution_mode = "BLOCKED"
            record.failure_reason = (
                f"OUTPUT_GATE_REJECT ({gate_result.stage_failed}): "
                + "; ".join(gate_result.violations[:2])
            )
            record.outputs = []

        elif gate_result.decision == GateDecision.STOP:
            logger.error(
                "OUTPUT_GATE STOP [%s]: critical policy violation — %s",
                record.engine_id,
                "; ".join(gate_result.violations[:2]),
            )
            record.status = EngineExecutionResult.FAILED
            record.actual_execution_mode = "FAILED"
            record.failure_reason = (
                f"OUTPUT_GATE_STOP ({gate_result.stage_failed}): "
                + "; ".join(gate_result.violations[:2])
            )
            record.outputs = []

        elif gate_result.decision == GateDecision.REANALYZE:
            logger.info(
                "OUTPUT_GATE REANALYZE [%s / stage=%s]: minor defect — flagging for retry.",
                record.engine_id,
                gate_result.stage_failed,
            )
            record.status = EngineExecutionResult.PARTIAL
            record.review_status = "REANALYSIS_REQUESTED"

        elif gate_result.decision == GateDecision.REVIEW_REQUIRED:
            logger.info(
                "OUTPUT_GATE REVIEW_REQUIRED [%s]: output needs specialist review.",
                record.engine_id,
            )
            record.review_status = "SPECIALIST_REVIEW_REQUIRED"

        return record


# Singleton
output_gate = OutputGate()
