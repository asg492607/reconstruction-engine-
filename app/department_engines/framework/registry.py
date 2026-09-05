from typing import Dict, List, Optional, Set, Any
import asyncio
from datetime import datetime, timezone
import time

from app.department_engines.framework.base import (
    BaseEngine,
    EngineDefinition,
    EngineLevel,
    EngineContext,
    EngineExecutionRecord,
    EngineExecutionResult
)
from app.department_engines.framework.validator import output_validator

class CyclicDependencyError(Exception):
    pass

class EngineRegistry:
    def __init__(self):
        self._engines: Dict[str, BaseEngine] = {}

    def register(self, engine: BaseEngine) -> None:
        """Register an engine instance with the platform."""
        self._engines[engine.engine_id] = engine

    def get(self, engine_id: str) -> Optional[BaseEngine]:
        return self._engines.get(engine_id)

    def list_all(self) -> List[EngineDefinition]:
        return [engine.definition for engine in self._engines.values()]

    def list_by_level(self, level: EngineLevel) -> List[BaseEngine]:
        return [e for e in self._engines.values() if e.definition.engine_level == level]

    def list_by_department(self, department: str) -> List[BaseEngine]:
        return [e for e in self._engines.values() if e.definition.department == department]

    def count(self) -> int:
        return len(self._engines)

    def resolve_dag(self, target_engine_ids: List[str]) -> List[str]:
        """
        Computes topological execution order for the given engines and their prerequisites.
        Guarantees that an engine only executes after all prerequisite engines have completed.
        """
        # 1. Collect all required engines recursively
        required_set: Set[str] = set()

        def collect(eid: str):
            if eid not in self._engines:
                return
            if eid in required_set:
                return
            required_set.add(eid)
            engine = self._engines[eid]
            for dep in engine.dependencies:
                collect(dep)

        for tid in target_engine_ids:
            collect(tid)

        # 2. Build in-degree and graph
        graph: Dict[str, List[str]] = {eid: [] for eid in required_set}
        in_degree: Dict[str, int] = {eid: 0 for eid in required_set}

        for eid in required_set:
            engine = self._engines[eid]
            for dep in engine.dependencies:
                if dep in required_set:
                    graph[dep].append(eid)
                    in_degree[eid] += 1

        # 3. Kahn's Algorithm
        queue = [eid for eid, deg in in_degree.items() if deg == 0]
        sorted_order: List[str] = []

        while queue:
            curr = queue.pop(0)
            sorted_order.append(curr)
            for neighbor in graph[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_order) != len(required_set):
            raise CyclicDependencyError("Cyclic dependency detected in engine execution graph.")

        return sorted_order

    async def execute_engine(
        self,
        engine_id: str,
        case_id: str,
        evidence: Optional[Any],
        context: EngineContext
    ) -> EngineExecutionRecord:
        """
        Executes a single engine through its complete lifecycle:
        AVAILABLE -> AUTHORIZED -> RUNNING -> COMPLETED -> OUTPUT_VALIDATION -> AI_OUTPUT_GENERATED
        """
        engine = self.get(engine_id)
        if not engine:
            record = EngineExecutionRecord(
                case_id=case_id,
                engine_id=engine_id,
                engine_version="0.0.0",
                execution_mode="DETERMINISTIC",
                status=EngineExecutionResult.FAILED,
                failure_reason=f"Engine '{engine_id}' not found in registry."
            )
            return record

        # Verify prerequisites in context.prior_results
        for dep in engine.dependencies:
            dep_rec = context.prior_results.get(dep)
            if not dep_rec or getattr(dep_rec, "status", None) not in [EngineExecutionResult.SUCCESS, EngineExecutionResult.PARTIAL]:
                # If prerequisite failed, had no usable output, or missing, engine is BLOCKED
                path = "BLOCKED_PREREQUISITE_FAILED"
                dep_status = getattr(dep_rec, "status", "MISSING")
                if dep_status == EngineExecutionResult.NO_USABLE_OUTPUT:
                    reason = f"Prerequisite engine '{dep}' produced NO_USABLE_OUTPUT ({dep_rec.failure_reason or 'no usable features'})."
                    path = "BLOCKED_PREREQUISITE_NO_USABLE_OUTPUT"
                elif dep_status == EngineExecutionResult.BLOCKED:
                    reason = f"Prerequisite engine '{dep}' was BLOCKED ({dep_rec.failure_reason or 'prerequisite unavailable'})."
                elif dep_status == EngineExecutionResult.FAILED:
                    reason = f"Prerequisite engine '{dep}' FAILED ({dep_rec.failure_reason or 'engine error'})."
                else:
                    reason = f"Prerequisite engine '{dep}' not completed successfully."
                record = EngineExecutionRecord(
                    case_id=case_id,
                    evidence_ids=[getattr(evidence, "id", "")] if evidence else [],
                    engine_id=engine_id,
                    engine_version=engine.definition.engine_version,
                    execution_mode=engine.execution_mode,
                    status=EngineExecutionResult.BLOCKED,
                    confidence=None,
                    actual_execution_path=path,
                    actual_execution_mode="BLOCKED",
                    failure_reason=reason
                )
                return record

        t0 = time.time()
        start_dt = datetime.now(timezone.utc)
        try:
            raw_record = await engine.execute(case_id=case_id, evidence=evidence, context=context)
            raw_record.completed_at = datetime.now(timezone.utc)
            raw_record.execution_time_ms = int((time.time() - t0) * 1000)

            # Pass through OUTPUT_VALIDATION lifecycle stage
            validated_record = output_validator.validate(raw_record, engine.definition)
            context.prior_results[engine_id] = validated_record
            return validated_record

        except Exception as exc:
            record = EngineExecutionRecord(
                case_id=case_id,
                evidence_ids=[getattr(evidence, "id", "")] if evidence else [],
                engine_id=engine_id,
                engine_version=engine.definition.engine_version,
                execution_mode=engine.execution_mode,
                started_at=start_dt,
                completed_at=datetime.now(timezone.utc),
                execution_time_ms=int((time.time() - t0) * 1000),
                status=EngineExecutionResult.FAILED,
                failure_reason=f"Exception during execution: {str(exc)}"
            )
            context.prior_results[engine_id] = record
            return record


engine_registry = EngineRegistry()
