"""
Phase 10: Engine Telemetry Analytics
======================================
Aggregates per-engine performance data across all analysis runs to surface:

  - Average execution time per engine
  - Success / Partial / Blocked / Failed / Skipped rates
  - Confidence distribution
  - Most frequently blocked engine chains
  - Output Gate rejection rates
  - Time-limit-exceeded frequency
  - Per-modality utilization (which evidence types trigger which engines)

Data comes from the in-memory `_CASE_EXECUTION_RECORDS` and
`_CASE_EXECUTION_HISTORY` stores in dispatcher.py.

Intended to be surfaced via GET /engines/analytics/performance
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Telemetry Analytics Service
# ---------------------------------------------------------------------------

class EngineAnalyticsService:
    """
    Computes performance and utilization analytics from dispatcher telemetry.

    Usage:
        from app.department_engines.dispatcher import _CASE_EXECUTION_RECORDS, _CASE_EXECUTION_HISTORY
        from app.department_engines.telemetry_analytics import EngineAnalyticsService

        service = EngineAnalyticsService()
        report = service.compute_global_report(
            execution_records=_CASE_EXECUTION_RECORDS,
            run_history=_CASE_EXECUTION_HISTORY
        )
    """

    def compute_global_report(
        self,
        execution_records: Dict[str, List[Any]],  # case_id → List[EngineExecutionRecord]
        run_history: Dict[str, List[Dict]],        # case_id → List[run_snapshot]
    ) -> Dict[str, Any]:
        """
        Aggregates telemetry across all cases and runs.
        Returns a report suitable for the analytics API endpoint.
        """
        # Flatten all records
        all_records: List[Any] = []
        for records in execution_records.values():
            all_records.extend(records)

        # Flatten all run history
        all_runs: List[Dict] = []
        for runs in run_history.values():
            all_runs.extend(runs)

        # Per-engine stats
        engine_stats = self._compute_engine_stats(all_records)

        # Global summary
        total_cases = len(execution_records)
        total_runs = len(all_runs)
        total_records = len(all_records)

        return {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_cases_analyzed": total_cases,
                "total_analysis_runs": total_runs,
                "total_engine_executions": total_records,
            },
            "per_engine_performance": engine_stats,
            "top_blocked_chains": self._compute_blocked_chains(all_records),
            "modality_utilization": self._compute_modality_utilization(all_records),
            "output_gate_stats": self._compute_gate_stats(all_records),
            "time_limit_violations": self._compute_time_limit_violations(all_records),
        }

    # -----------------------------------------------------------------------

    def _compute_engine_stats(self, records: List[Any]) -> List[Dict[str, Any]]:
        """Per-engine aggregate statistics."""
        stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "engine_id": "",
            "total_executions": 0,
            "success": 0,
            "partial": 0,
            "blocked": 0,
            "failed": 0,
            "skipped": 0,
            "skipped_no_input": 0,
            "time_limit_exceeded": 0,
            "no_usable_output": 0,
            "confidence_sum": 0.0,
            "confidence_count": 0,
            "exec_time_ms_sum": 0,
            "exec_time_ms_count": 0,
        })

        for rec in records:
            eid = getattr(rec, "engine_id", "UNKNOWN")
            s = stats[eid]
            s["engine_id"] = eid
            s["total_executions"] += 1

            status_val = getattr(getattr(rec, "status", None), "value", str(getattr(rec, "status", "")))
            status_key = status_val.lower() if status_val else "failed"
            if status_key in s:
                s[status_key] += 1

            conf = getattr(rec, "confidence", None)
            if conf is not None:
                s["confidence_sum"] += conf
                s["confidence_count"] += 1

            exec_ms = getattr(rec, "execution_time_ms", None)
            if exec_ms is not None:
                s["exec_time_ms_sum"] += exec_ms
                s["exec_time_ms_count"] += 1

        result = []
        for eid, s in sorted(stats.items()):
            avg_conf = (s["confidence_sum"] / s["confidence_count"]) if s["confidence_count"] else None
            avg_ms = (s["exec_time_ms_sum"] / s["exec_time_ms_count"]) if s["exec_time_ms_count"] else None
            total = s["total_executions"] or 1
            result.append({
                "engine_id": eid,
                "total_executions": s["total_executions"],
                "success_rate": round(s["success"] / total, 3),
                "partial_rate": round(s["partial"] / total, 3),
                "blocked_rate": round(s["blocked"] / total, 3),
                "failed_rate": round(s["failed"] / total, 3),
                "skipped_rate": round((s["skipped"] + s["skipped_no_input"]) / total, 3),
                "time_limit_exceeded_rate": round(s["time_limit_exceeded"] / total, 3),
                "no_usable_output_rate": round(s["no_usable_output"] / total, 3),
                "avg_confidence": round(avg_conf, 3) if avg_conf is not None else None,
                "avg_execution_time_ms": round(avg_ms, 1) if avg_ms is not None else None,
            })
        return result

    def _compute_blocked_chains(self, records: List[Any]) -> List[Dict[str, Any]]:
        """Find the most commonly blocked engines and their root causes."""
        blocked = [
            r for r in records
            if getattr(getattr(r, "status", None), "value", "") in ("BLOCKED", "FAILED")
        ]
        chain_counts: Dict[str, int] = defaultdict(int)
        for r in blocked:
            reason = getattr(r, "failure_reason", "") or ""
            chain_counts[f"{r.engine_id}: {reason[:60]}"] += 1
        return [
            {"chain": chain, "occurrences": count}
            for chain, count in sorted(chain_counts.items(), key=lambda x: -x[1])[:10]
        ]

    def _compute_modality_utilization(self, records: List[Any]) -> Dict[str, int]:
        """Count how many engine executions involved each evidence modality."""
        modality_count: Dict[str, int] = defaultdict(int)
        for r in records:
            for ev_id in (getattr(r, "evidence_ids", []) or []):
                if ev_id:
                    modality_count["HAS_EVIDENCE"] += 1
                    break
            grounding = getattr(r, "grounding_sources", []) or []
            for gs in grounding:
                gs_str = str(gs).upper()
                for modality in ("CCTV", "IMAGE", "AUDIO", "DOCUMENT", "TRANSACTION", "INVENTORY", "WITNESS"):
                    if modality in gs_str:
                        modality_count[modality] += 1
                        break
        return dict(sorted(modality_count.items()))

    def _compute_gate_stats(self, records: List[Any]) -> Dict[str, Any]:
        """Analyze output gate rejection data from record warnings."""
        gate_rejections = 0
        gate_reviews = 0
        for r in records:
            for w in (getattr(r, "warnings", []) or []):
                w_str = str(w)
                if "OUTPUT_GATE_REJECT" in w_str:
                    gate_rejections += 1
                elif "OUTPUT_GATE" in w_str or "SPECIALIST_REVIEW" in w_str:
                    gate_reviews += 1
        return {
            "gate_rejections": gate_rejections,
            "gate_reviews_required": gate_reviews,
        }

    def _compute_time_limit_violations(self, records: List[Any]) -> List[str]:
        """Return engine IDs that exceeded their time budget."""
        return [
            getattr(r, "engine_id", "UNKNOWN")
            for r in records
            if getattr(getattr(r, "status", None), "value", "") == "TIME_LIMIT_EXCEEDED"
        ]

    def compute_case_report(
        self,
        execution_records: Dict[str, List[Any]],
        run_history: Dict[str, List[Dict]],
        case_id: str,
    ) -> Dict[str, Any]:
        """
        Single-case analytics report.
        """
        records = execution_records.get(case_id, [])
        runs = run_history.get(case_id, [])
        engine_stats = self._compute_engine_stats(records)

        return {
            "case_id": case_id,
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "analysis_run_count": len(runs),
            "total_engine_executions": len(records),
            "per_engine_performance": engine_stats,
            "run_history": runs,
        }


# Singleton
engine_analytics = EngineAnalyticsService()
