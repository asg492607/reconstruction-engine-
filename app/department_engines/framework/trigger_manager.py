"""
Phase 1: Engine Condition Trigger Manager
=========================================
Every engine carries an EngineTriggerCondition that declaratively specifies
the conditions under which it should move from NOT_REQUIRED → WAITING → READY.

EngineLifecycleState tracks every engine's runtime state per analysis run,
replacing implicit BLOCKED/SKIPPED distinctions with 10 precise states:

    NOT_REQUIRED          – Planner determined engine has no applicable evidence/context.
    WAITING               – Prerequisites not yet complete; engine is queued.
    READY                 – All prerequisites satisfied; awaiting dispatch slot.
    RUNNING               – Engine.execute() is active.
    COMPLETED             – Engine produced SUCCESS or PARTIAL output.
    SKIPPED_NO_INPUT      – Required evidence modality absent; engine cleanly skipped.
    BLOCKED               – Prerequisite engine failed/blocked; downstream cascaded.
    NO_USABLE_OUTPUT      – Engine ran; no target features detected in evidence.
    FAILED                – Engine raised an exception or internal error.
    TIME_LIMIT_EXCEEDED   – Wall-clock budget exhausted before completion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Engine Lifecycle State Enum  (10 states)
# ---------------------------------------------------------------------------

class EngineLifecycleState(str, Enum):
    NOT_REQUIRED        = "NOT_REQUIRED"
    WAITING             = "WAITING"
    READY               = "READY"
    RUNNING             = "RUNNING"
    COMPLETED           = "COMPLETED"
    SKIPPED_NO_INPUT    = "SKIPPED_NO_INPUT"
    BLOCKED             = "BLOCKED"
    NO_USABLE_OUTPUT    = "NO_USABLE_OUTPUT"
    FAILED              = "FAILED"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"


# ---------------------------------------------------------------------------
# Trigger Condition dataclass
# ---------------------------------------------------------------------------

@dataclass
class EngineTriggerCondition:
    """
    Declarative specification of when an engine should execute.

    Fields
    ------
    required_evidence_types : Set[str]
        Evidence type strings (from EvidenceType enum values) that MUST be
        present in the case for this engine to leave SKIPPED_NO_INPUT.
        Empty set = no modality restriction (always potentially eligible).

    required_upstream_states : Dict[str, Set[EngineLifecycleState]]
        Mapping of prerequisite engine_id → acceptable lifecycle states.
        Engine only becomes READY when all listed prerequisites are in one
        of their accepted states.  Default rule: upstream must be COMPLETED.

    minimum_quality : str
        Minimum evidence quality level required to proceed.
        Compared against EvidenceQuality enum: "POOR" < "LOW" < "MEDIUM" < "HIGH".
        Empty string = no quality gate.

    required_departments : Set[str]
        If non-empty, the requesting user's department must be in this set.
        Empty set = no department restriction.

    objective_relevance_keywords : List[str]
        Case investigative_objectives are matched against these keywords.
        If the list is non-empty and zero keywords match, engine is NOT_REQUIRED
        unless it is in the always_run_engine_ids override on the trigger manager.

    always_eligible : bool
        When True, the engine always transitions to READY regardless of
        evidence/modality checks (used for E01–E07 foundation layer).
    """
    required_evidence_types: Set[str] = field(default_factory=set)
    required_upstream_states: Dict[str, Set[EngineLifecycleState]] = field(default_factory=dict)
    minimum_quality: str = ""
    required_departments: Set[str] = field(default_factory=set)
    objective_relevance_keywords: List[str] = field(default_factory=list)
    always_eligible: bool = False


# ---------------------------------------------------------------------------
# Per-Run Engine Lifecycle Record
# ---------------------------------------------------------------------------

@dataclass
class EngineLifecycleRecord:
    """
    Tracks the real-time lifecycle state of a single engine during one analysis run.
    """
    engine_id: str
    state: EngineLifecycleState = EngineLifecycleState.NOT_REQUIRED
    transitioned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = ""
    time_budget_ms: int = 0           # 0 = no limit
    elapsed_ms: int = 0

    def transition(self, new_state: EngineLifecycleState, reason: str = "") -> None:
        self.state = new_state
        self.transitioned_at = datetime.now(timezone.utc)
        self.reason = reason


# ---------------------------------------------------------------------------
# Condition Trigger Manager
# ---------------------------------------------------------------------------

_QUALITY_ORDER = {"POOR": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "": -1}


class ConditionTriggerManager:
    """
    Central orchestrator for engine lifecycle decisions.

    Usage (inside dispatcher.py):

        ctm = ConditionTriggerManager(
            evidence_types=available_evidence_type_strings,
            investigative_objectives=case.investigative_objectives,
            user_department=current_user.department.value,
        )
        state = ctm.evaluate(engine_id, trigger_condition, prior_lifecycle_states)
    """

    def __init__(
        self,
        evidence_types: Set[str],
        investigative_objectives: Optional[List[str]] = None,
        user_department: str = "",
        evidence_quality_map: Optional[Dict[str, str]] = None,
    ) -> None:
        self.evidence_types = {et.upper() for et in evidence_types}
        self.investigative_objectives = [
            o.lower() for o in (investigative_objectives or [])
        ]
        self.user_department = user_department.upper()
        self.evidence_quality_map: Dict[str, str] = evidence_quality_map or {}

    # ------------------------------------------------------------------
    def evaluate(
        self,
        engine_id: str,
        condition: EngineTriggerCondition,
        prior_lifecycle: Dict[str, EngineLifecycleState],
    ) -> tuple[EngineLifecycleState, str]:
        """
        Returns (EngineLifecycleState, reason_string) for the given engine.

        Decision order:
        1. always_eligible → READY
        2. No matching evidence → SKIPPED_NO_INPUT
        3. Department gate → BLOCKED
        4. Objective relevance → NOT_REQUIRED
        5. Quality gate → SKIPPED_NO_INPUT
        6. Upstream prerequisite check → WAITING or BLOCKED
        7. → READY
        """

        # 1. Foundation layer engines always run when any evidence present
        if condition.always_eligible:
            return EngineLifecycleState.READY, "Foundation engine; always eligible."

        # 2. Evidence modality gate
        if condition.required_evidence_types:
            matched = condition.required_evidence_types & self.evidence_types
            if not matched:
                types_str = ", ".join(sorted(condition.required_evidence_types))
                return (
                    EngineLifecycleState.SKIPPED_NO_INPUT,
                    f"Required evidence modality not present: {types_str}.",
                )

        # 3. Department authorization gate
        if condition.required_departments:
            if self.user_department not in condition.required_departments:
                return (
                    EngineLifecycleState.BLOCKED,
                    f"User department '{self.user_department}' not authorized for this engine.",
                )

        # 4. Objective relevance gate
        if condition.objective_relevance_keywords:
            keywords_lower = [k.lower() for k in condition.objective_relevance_keywords]
            if not any(
                any(kw in obj for kw in keywords_lower)
                for obj in self.investigative_objectives
            ):
                return (
                    EngineLifecycleState.NOT_REQUIRED,
                    "No investigative objective matches engine relevance keywords.",
                )

        # 5. Quality gate (across all evidence of matching modality)
        if condition.minimum_quality:
            min_level = _QUALITY_ORDER.get(condition.minimum_quality.upper(), -1)
            # Find worst quality among matching evidence
            worst_quality = "HIGH"
            for ev_type, qual in self.evidence_quality_map.items():
                if ev_type.upper() in (condition.required_evidence_types or self.evidence_types):
                    q_order = _QUALITY_ORDER.get(qual.upper(), -1)
                    if q_order < _QUALITY_ORDER.get(worst_quality.upper(), 3):
                        worst_quality = qual
            if _QUALITY_ORDER.get(worst_quality.upper(), -1) < min_level:
                return (
                    EngineLifecycleState.SKIPPED_NO_INPUT,
                    f"Evidence quality '{worst_quality}' below minimum required '{condition.minimum_quality}'.",
                )

        # 6. Upstream prerequisite check
        for dep_id, accepted_states in condition.required_upstream_states.items():
            dep_state = prior_lifecycle.get(dep_id)
            if dep_state is None:
                return (
                    EngineLifecycleState.WAITING,
                    f"Prerequisite engine '{dep_id}' has not yet executed.",
                )
            if dep_state not in accepted_states:
                if dep_state in (
                    EngineLifecycleState.FAILED,
                    EngineLifecycleState.BLOCKED,
                    EngineLifecycleState.TIME_LIMIT_EXCEEDED,
                ):
                    return (
                        EngineLifecycleState.BLOCKED,
                        f"Prerequisite engine '{dep_id}' is in terminal failure state '{dep_state.value}'.",
                    )
                return (
                    EngineLifecycleState.WAITING,
                    f"Prerequisite engine '{dep_id}' is in state '{dep_state.value}'; "
                    f"expected one of {[s.value for s in accepted_states]}.",
                )

        return EngineLifecycleState.READY, "All trigger conditions satisfied."


# ---------------------------------------------------------------------------
# Lifecycle State → EngineExecutionResult mapper
# (for backward compatibility with existing EngineExecutionRecord)
# ---------------------------------------------------------------------------

def lifecycle_to_execution_result(state: EngineLifecycleState) -> str:
    """Maps a lifecycle state to the corresponding execution_path string."""
    mapping = {
        EngineLifecycleState.SKIPPED_NO_INPUT:    "BLOCKED_UNAVAILABLE_MODALITY",
        EngineLifecycleState.BLOCKED:             "BLOCKED_PREREQUISITE_FAILED",
        EngineLifecycleState.NOT_REQUIRED:        "SKIPPED_NOT_REQUIRED",
        EngineLifecycleState.TIME_LIMIT_EXCEEDED: "TIME_LIMIT_EXCEEDED",
        EngineLifecycleState.FAILED:              "FAILED",
        EngineLifecycleState.NO_USABLE_OUTPUT:    "NO_USABLE_OUTPUT",
    }
    return mapping.get(state, "NOT_STARTED")
