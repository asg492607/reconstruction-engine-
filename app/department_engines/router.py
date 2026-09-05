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
