from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
import uuid
from pydantic import BaseModel, Field, model_validator


class EngineLevel(str, Enum):
    EVIDENCE = "EVIDENCE"
    DEPARTMENT = "DEPARTMENT"
    CROSS_DOMAIN = "CROSS_DOMAIN"
    DECISION_SUPPORT = "DECISION_SUPPORT"


class ExecutionMode(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    MODEL = "MODEL"
    LLM = "LLM"
    HYBRID = "HYBRID"
    WORKFLOW = "WORKFLOW"


class ReviewPolicy(str, Enum):
    AUTO_ACCEPT = "AUTO_ACCEPT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    SPECIALIST_REVIEW_REQUIRED = "SPECIALIST_REVIEW_REQUIRED"
    LEAD_REVIEW_REQUIRED = "LEAD_REVIEW_REQUIRED"


class EngineExecutionResult(str, Enum):
    SUCCESS = "SUCCESS"                      # Full output generated satisfying all confidence thresholds
    PARTIAL = "PARTIAL"                      # Some observations generated; partial occlusion or corruption noted
    NO_USABLE_OUTPUT = "NO_USABLE_OUTPUT"    # Media processed successfully but no target features detected
    BLOCKED = "BLOCKED"                      # Prerequisite engine failed or quality below minimum threshold
    FAILED = "FAILED"                        # Model exception, timeout, or processing failure
    SKIPPED = "SKIPPED"                      # Engine not applicable under current Analysis Plan


class EngineDefinition(BaseModel):
    engine_id: str
    engine_name: str
    engine_version: str = "1.0.0"
    engine_level: EngineLevel
    department: Optional[str] = None         # "INVESTIGATION", "FORENSIC", "FINANCIAL", or None (Cross-Domain)
    execution_mode: ExecutionMode
    description: str
    accepted_evidence_types: List[str] = []
    required_inputs: List[str] = []
    optional_inputs: List[str] = []
    dependencies: List[str] = []             # Prerequisite engine IDs
    output_types: List[str] = []             # e.g. ["OBSERVATION", "METADATA", "TIMELINE_EVENT"]
    confidence_method: str = "HEURISTIC"     # "PROBABILISTIC_BOUND", "CALIBRATED_SCORE", "DETERMINISTIC", "HEURISTIC"
    human_review_policy: ReviewPolicy = ReviewPolicy.AUTO_ACCEPT
    quality_thresholds: Dict[str, Any] = Field(default_factory=dict)
    failure_codes: List[str] = Field(default_factory=list)


class EngineContext(BaseModel):
    case_id: str
    case_title: Optional[str] = None
    specific_offense: Optional[str] = None
    incident_location: Optional[str] = None
    incident_time: Optional[datetime] = None
    prior_results: Dict[str, Any] = Field(default_factory=dict)  # Outputs from prerequisite engines keyed by engine_id
    shared_state: Dict[str, Any] = Field(default_factory=dict)   # Additional runtime data
    user_id: Optional[str] = None


class EngineExecutionRecord(BaseModel):
    execution_id: str = Field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:12]}")
    case_id: str
    evidence_ids: List[str] = Field(default_factory=list)
    engine_id: str
    engine_version: str
    execution_mode: ExecutionMode
    declared_execution_mode: Optional[str] = None
    actual_execution_mode: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    execution_time_ms: int = 0
    status: EngineExecutionResult = EngineExecutionResult.SUCCESS
    outputs: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: Optional[float] = None
    provenance: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    failure_reason: Optional[str] = None
    review_status: str = "AUTO_ACCEPT"
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    # Truthful execution path — must be set by every engine that attempts AI/LLM:
    # "REAL_LLM"                 — LLM was called and returned usable output
    # "DETERMINISTIC_ONLY"       — Engine is fully deterministic, no LLM required
    # "DETERMINISTIC_COMPONENT"  — Deterministic logic ran for MODEL/HYBRID engine
    # "BLOCKED_LLM_UNAVAILABLE"  — LLM required but no API credentials configured
    # "BLOCKED_LLM_FAILED"       — LLM credentials present but call failed/quota exceeded
    # "BLOCKED_PREREQUISITE_INSUFFICIENT" — Prerequisite engine insufficient
    # "BLOCKED_PREREQUISITE_FAILED"       — Prerequisite engine blocked/failed
    # "BLOCKED_UNAVAILABLE_MODALITY"      — Modality unavailable in evidence exhibits
    # "PARTIAL_DETERMINISTIC"    — HYBRID engine; LLM component blocked, deterministic component ran
    # "NOT_STARTED"              — Record created but engine did not execute (BLOCKED at dispatch)
    actual_execution_path: str = "NOT_STARTED"
    fallback_used: str = "NOT_APPLICABLE"  # "NO", "BLOCKED", "NOT_APPLICABLE"
    grounding_sources: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def populate_modes(self):
        if not self.declared_execution_mode:
            self.declared_execution_mode = (
                self.execution_mode.value if hasattr(self.execution_mode, "value") else str(self.execution_mode)
            )
        if self.status == EngineExecutionResult.BLOCKED:
            self.actual_execution_mode = "BLOCKED"
            self.confidence = None
            if self.actual_execution_path in ("NOT_STARTED", ""):
                self.actual_execution_path = "BLOCKED"
            self.grounding_sources = []
        elif not self.actual_execution_mode:
            if self.actual_execution_path == "REAL_LLM":
                self.actual_execution_mode = "LLM"
            elif self.actual_execution_path in ["DETERMINISTIC_ONLY", "PARTIAL_DETERMINISTIC", "DETERMINISTIC_COMPONENT"]:
                self.actual_execution_mode = "DETERMINISTIC"
            elif "BLOCKED" in self.actual_execution_path:
                self.actual_execution_mode = "BLOCKED"
                self.confidence = None
            elif self.declared_execution_mode == "DETERMINISTIC":
                self.actual_execution_mode = "DETERMINISTIC"
            else:
                self.actual_execution_mode = self.declared_execution_mode
        return self



class BaseEngine(ABC):
    definition: EngineDefinition

    def __init__(self, definition: Optional[EngineDefinition] = None):
        if definition:
            self.definition = definition

    @property
    def engine_id(self) -> str:
        return self.definition.engine_id

    @property
    def engine_name(self) -> str:
        return self.definition.engine_name

    @property
    def dependencies(self) -> List[str]:
        return self.definition.dependencies

    @property
    def execution_mode(self) -> ExecutionMode:
        return self.definition.execution_mode

    @property
    def human_review_policy(self) -> ReviewPolicy:
        return self.definition.human_review_policy

    @abstractmethod
    async def execute(
        self,
        case_id: str,
        evidence: Optional[Any],
        context: EngineContext
    ) -> EngineExecutionRecord:
        """
        Executes analytical capability.
        Must strictly adhere to SWGDE/NIST non-verdict principles and the Cardinal Anti-Hallucination Rule:
        No engine may manufacture an observation merely because its output is expected by a downstream engine.
        """
        pass
