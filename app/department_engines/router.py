from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query
from app.department_engines.framework.registry import engine_registry
from app.department_engines.framework.base import EngineDefinition

router = APIRouter(prefix="/engines", tags=["Department Engines"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_registered_engines():
    """
    Single source of truth for the RRE 45-Engine Backbone.
    Returns all registered engine definitions including inputs, dependencies,
    execution modes, human review policies, and failure codes.
    """
    defs = engine_registry.list_all()
    return [d.model_dump() for d in defs]

@router.get("/analytics/performance", response_model=Dict[str, Any])
async def get_engine_performance_analytics(case_id: Optional[str] = Query(default=None)):
    """
    Phase 10 — Engine Telemetry Analytics.

    Returns aggregated performance statistics across all analysis runs.
    If `case_id` is provided, scopes to a single case.
    Includes per-engine success/blocked/failed rates, average execution time,
    confidence distribution, output gate rejections, and top blocked chains.
    """
    from app.department_engines.dispatcher import _CASE_EXECUTION_RECORDS, _CASE_EXECUTION_HISTORY
    from app.department_engines.telemetry_analytics import engine_analytics

    if case_id:
        return engine_analytics.compute_case_report(
            execution_records=_CASE_EXECUTION_RECORDS,
            run_history=_CASE_EXECUTION_HISTORY,
            case_id=case_id,
        )
    return engine_analytics.compute_global_report(
        execution_records=_CASE_EXECUTION_RECORDS,
        run_history=_CASE_EXECUTION_HISTORY,
    )

@router.get("/{engine_id}", response_model=Dict[str, Any])
async def get_engine_definition(engine_id: str):
    """Retrieve full definition for a specific engine."""
    eng = engine_registry.get(engine_id)
    if not eng:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Engine '{engine_id}' not found in registry.")
    return eng.definition.model_dump()

@router.get("/dag/resolve")
async def resolve_engine_dag(targets: List[str] = Query(default=["R04"])):
    """Computes Kahn's algorithm topological DAG execution sequence for target engines."""
    try:
        sequence = engine_registry.resolve_dag(targets)
        return {"targets": targets, "execution_order": sequence, "total_nodes": len(sequence)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
