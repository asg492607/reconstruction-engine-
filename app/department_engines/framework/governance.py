"""
Phase 1 + Phase 8: Per-Engine Resource & Time Governance
=========================================================
Defines budget envelopes for every engine execution, enabling the planner
to make resource-aware decisions:

  - Skip entire engine branches when their modality is absent.
  - Prune optional engines below quality thresholds.
  - Suppress engines whose objectives are irrelevant to the active case.
  - Enforce hard wall-clock / token / frame limits per execution.

The ResourceGovernor is injected into the dispatcher and consulted before
and after each engine execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Engine Resource Budget
# ---------------------------------------------------------------------------

@dataclass
class EngineResourceBudget:
    """
    Configurable per-engine resource ceiling.

    All limits are soft-advisory by default and become hard limits when
    enforce=True.  The dispatcher enforces time limits via asyncio.wait_for().

    Attributes
    ----------
    max_execution_time_ms : int
        Maximum wall-clock execution time in milliseconds.
        0 = no limit.
    max_tokens : int
        Maximum tokens to consume in LLM calls.
        0 = no limit (uses provider default).
    max_model_calls : int
        Maximum number of LLM inference calls per engine run.
        0 = no limit.
    max_tool_calls : int
        Maximum internal tool / utility invocations (e.g., image pre-processing steps).
        0 = no limit.
    max_frames_rows : int
        Maximum video frames extracted OR data rows processed.
        0 = no limit.
    max_memory_mb : int
        Soft memory ceiling in megabytes.
        0 = no limit.
    max_output_size_kb : int
        Maximum serialized output payload size in kilobytes.
        0 = no limit.
    enforce : bool
        When True, exceeding limits causes TIME_LIMIT_EXCEEDED / BLOCKED.
        When False, limits are advisory only (warnings are emitted).
    """
    max_execution_time_ms: int = 0
    max_tokens: int = 0
    max_model_calls: int = 0
    max_tool_calls: int = 0
    max_frames_rows: int = 0
    max_memory_mb: int = 0
    max_output_size_kb: int = 0
    enforce: bool = True


# ---------------------------------------------------------------------------
# Default budgets per engine tier (sensible defaults; overridable)
# ---------------------------------------------------------------------------

TIER1_EVIDENCE_BUDGET = EngineResourceBudget(
    max_execution_time_ms=5_000,
    max_model_calls=0,
    max_frames_rows=0,
    enforce=True,
)

TIER2_INVESTIGATION_BUDGET = EngineResourceBudget(
    max_execution_time_ms=60_000,
    max_tokens=4_096,
    max_model_calls=3,
    max_frames_rows=500,
    enforce=True,
)

TIER3_FORENSIC_BUDGET = EngineResourceBudget(
    max_execution_time_ms=45_000,
    max_tokens=4_096,
    max_model_calls=3,
    enforce=True,
)

TIER4_FINANCIAL_BUDGET = EngineResourceBudget(
    max_execution_time_ms=30_000,
    max_frames_rows=10_000,
    enforce=True,
)

TIER5_INTELLIGENCE_BUDGET = EngineResourceBudget(
    max_execution_time_ms=30_000,
    max_tokens=8_192,
    max_model_calls=5,
    enforce=True,
)

TIER6_RECONSTRUCTION_BUDGET = EngineResourceBudget(
    max_execution_time_ms=120_000,
    max_tokens=16_384,
    max_model_calls=10,
    enforce=True,
)


# Engine-id → tier default mapping
_TIER_DEFAULTS: Dict[str, EngineResourceBudget] = {
    **{f"E0{i}": TIER1_EVIDENCE_BUDGET for i in range(1, 8)},
    **{f"I{str(i).zfill(2)}": TIER2_INVESTIGATION_BUDGET for i in range(1, 13)},
    **{f"F{str(i).zfill(2)}": TIER3_FORENSIC_BUDGET for i in range(1, 10)},
    **{f"FI{str(i).zfill(2)}": TIER4_FINANCIAL_BUDGET for i in range(1, 8)},
    **{f"X{str(i).zfill(2)}": TIER5_INTELLIGENCE_BUDGET for i in range(1, 7)},
    **{f"R{str(i).zfill(2)}": TIER6_RECONSTRUCTION_BUDGET for i in range(1, 5)},
}


# ---------------------------------------------------------------------------
# Resource Governor
# ---------------------------------------------------------------------------

class ResourceGovernor:
    """
    Central authority for per-engine resource budgets.

    Usage
    -----
    governor = ResourceGovernor()

    # Override a specific engine
    governor.set_budget("R01", EngineResourceBudget(max_execution_time_ms=180_000))

    # Retrieve budget before dispatching
    budget = governor.get_budget("R01")
    timeout_secs = budget.max_execution_time_ms / 1000 or None
    """

    def __init__(self, overrides: Optional[Dict[str, EngineResourceBudget]] = None):
        self._overrides: Dict[str, EngineResourceBudget] = overrides or {}

    def get_budget(self, engine_id: str) -> EngineResourceBudget:
        """Returns the effective budget for an engine (override > tier default > unlimited)."""
        if engine_id in self._overrides:
            return self._overrides[engine_id]
        for prefix, budget in _TIER_DEFAULTS.items():
            if engine_id.startswith(prefix[:2]):
                return budget
        return EngineResourceBudget()  # No restrictions

    def set_budget(self, engine_id: str, budget: EngineResourceBudget) -> None:
        """Set or replace a per-engine budget override."""
        self._overrides[engine_id] = budget

    def get_timeout_seconds(self, engine_id: str) -> Optional[float]:
        """Returns asyncio timeout in seconds, or None if no limit is set."""
        budget = self.get_budget(engine_id)
        if budget.max_execution_time_ms and budget.enforce:
            return budget.max_execution_time_ms / 1000.0
        return None

    def should_skip_for_quality(self, engine_id: str, quality: str) -> bool:
        """
        Phase 8 rule: If video quality is POOR, skip expensive downstream video engines.
        Extend this logic for other modality/quality combinations as needed.
        """
        poor_quality_video_engines = {"I07", "I09", "I10"}
        if engine_id in poor_quality_video_engines and quality.upper() == "POOR":
            return True
        return False

    def should_skip_for_objective(
        self,
        engine_id: str,
        investigative_objectives: list,
        optional_only: bool = True,
    ) -> bool:
        """
        Phase 8 rule: Prune optional engines with no relevance to case objectives.

        engine_objective_tags maps optional engines to required objective keywords.
        If no keyword matches, return True (skip).
        """
        if not investigative_objectives:
            return False  # No objectives set → run everything

        engine_objective_tags: Dict[str, list] = {
            "I07":  ["identify_person", "re_identify", "cross_camera"],
            "I09":  ["item_interaction", "merchandise", "shoplifting"],
            "I10":  ["blind_spot", "coverage", "camera_mapping"],
            "F06":  ["toolmark", "forced_entry", "physical_evidence"],
            "F07":  ["comparison", "baseline", "before_after"],
            "F08":  ["audio", "acoustic", "sound"],
            "F09":  ["audio", "alarm", "glass_break", "speech"],
            "FI05": ["pos", "transaction", "receipt"],
            "FI06": ["pos", "anomaly", "void", "no_sale"],
        }

        if engine_id not in engine_objective_tags:
            return False  # Not in optional relevance map → always eligible

        keywords = engine_objective_tags[engine_id]
        objectives_lower = [o.lower() for o in investigative_objectives]
        for kw in keywords:
            for obj in objectives_lower:
                if kw in obj:
                    return False  # Match found → do not skip
        return True  # No match → skip


# Singleton instance used by the dispatcher
resource_governor = ResourceGovernor()
