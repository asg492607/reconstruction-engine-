"""
Engine Input Resolver & Boundary Gate
=====================================
Enforces strict mathematical isolation at the data-consumption boundary:

case_id + analysis_version
        │
engine input resolver
        │
only matching records allowed
        │
engine execution
        │
validated output

Prevents stale-version contamination and cross-case leakage at the source.
"""

from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entities import (
    Evidence,
    Observation,
    CandidateEntity,
    SourceTimeline,
    CorrelatedTimelineEvent,
    Hypothesis,
    GapConflict,
    Finding,
    Claim
)
from app.department_engines.framework.base import EngineContext, EngineExecutionRecord

logger = logging.getLogger(__name__)


class ScopeViolationError(Exception):
    """Raised when an engine or operation attempts to consume data belonging to another case or analysis version."""
    pass


class EngineInputResolver:
    """
    Guarantees that downstream engines and dispatchers may only consume records
    matching the active case_id AND analysis_version.
    """

    @staticmethod
    async def resolve_evidence(db: AsyncSession, case_id: str) -> List[Evidence]:
        """Resolves only evidence attached to the specified case."""
        stmt = select(Evidence).where(Evidence.case_id == case_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def resolve_observations(
        db: AsyncSession,
        case_id: str,
        analysis_version: int
    ) -> List[Observation]:
        """Resolves observations strictly belonging to the case and analysis_version."""
        stmt = select(Observation).where(
            Observation.case_id == case_id,
            Observation.analysis_version == analysis_version
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def resolve_candidate_entities(
        db: AsyncSession,
        case_id: str,
        analysis_version: int
    ) -> List[CandidateEntity]:
        """Resolves candidate entities strictly belonging to the case and analysis_version."""
        stmt = select(CandidateEntity).where(
            CandidateEntity.case_id == case_id,
            CandidateEntity.analysis_version == analysis_version
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def resolve_source_timelines(
        db: AsyncSession,
        case_id: str,
        analysis_version: int
    ) -> List[SourceTimeline]:
        """Resolves source timelines strictly belonging to the case and analysis_version."""
        stmt = select(SourceTimeline).where(
            SourceTimeline.case_id == case_id,
            SourceTimeline.analysis_version == analysis_version
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def resolve_correlated_events(
        db: AsyncSession,
        case_id: str,
        analysis_version: int
    ) -> List[CorrelatedTimelineEvent]:
        """Resolves correlated events strictly belonging to the case and analysis_version."""
        stmt = select(CorrelatedTimelineEvent).where(
            CorrelatedTimelineEvent.case_id == case_id,
            CorrelatedTimelineEvent.analysis_version == analysis_version
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def resolve_hypotheses(
        db: AsyncSession,
        case_id: str,
        analysis_version: int
    ) -> List[Hypothesis]:
        """Resolves hypotheses strictly belonging to the case and analysis_version."""
        stmt = select(Hypothesis).where(
            Hypothesis.case_id == case_id,
            Hypothesis.analysis_version == analysis_version
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def resolve_gaps_conflicts(
        db: AsyncSession,
        case_id: str,
        analysis_version: int
    ) -> List[GapConflict]:
        """Resolves gaps and conflicts strictly belonging to the case and analysis_version."""
        stmt = select(GapConflict).where(
            GapConflict.case_id == case_id,
            GapConflict.analysis_version == analysis_version
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    def filter_prior_results_for_engine(
        context: EngineContext,
        target_case_id: str,
        target_analysis_version: int
    ) -> Dict[str, EngineExecutionRecord]:
        """
        Validates context.prior_results at the consumption boundary.
        Rejects or purges any record that belongs to another case or a different analysis version.
        """
        valid_results: Dict[str, EngineExecutionRecord] = {}
        for eid, rec in list(context.prior_results.items()):
            if not isinstance(rec, EngineExecutionRecord):
                continue
            if rec.case_id != target_case_id:
                logger.error(
                    f"DATA_CONSUMPTION_BREACH: Engine '{eid}' result belongs to case '{rec.case_id}', "
                    f"expected '{target_case_id}'. Rejected at input boundary."
                )
                raise ScopeViolationError(
                    f"Cross-case contamination blocked: Result for engine {eid} has case_id '{rec.case_id}' != '{target_case_id}'"
                )
            if rec.analysis_version != target_analysis_version:
                logger.error(
                    f"DATA_CONSUMPTION_BREACH: Engine '{eid}' result has analysis_version {rec.analysis_version}, "
                    f"expected {target_analysis_version}. Rejected at input boundary."
                )
                raise ScopeViolationError(
                    f"Stale-version contamination blocked: Result for engine {eid} has analysis_version {rec.analysis_version} != {target_analysis_version}"
                )
            valid_results[eid] = rec
        return valid_results


input_resolver = EngineInputResolver()
