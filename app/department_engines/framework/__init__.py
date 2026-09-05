"""
RRE 45-Engine Backbone Framework.
Standardized base classes, registry, dependency DAG, dynamic planner, and output validator.
"""
from app.department_engines.framework.base import (
    BaseEngine,
    EngineDefinition,
    EngineLevel,
    ExecutionMode,
    ReviewPolicy,
    EngineExecutionResult,
    EngineExecutionRecord,
    EngineContext
)
from app.department_engines.framework.registry import engine_registry
from app.department_engines.framework.validator import output_validator
from app.department_engines.framework.planner import dynamic_planner

__all__ = [
    "BaseEngine",
    "EngineDefinition",
    "EngineLevel",
    "ExecutionMode",
    "ReviewPolicy",
    "EngineExecutionResult",
    "EngineExecutionRecord",
    "EngineContext",
    "engine_registry",
    "output_validator",
    "dynamic_planner",
]
