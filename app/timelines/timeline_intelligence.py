"""
Phase 3: Multi-Tier Timeline Intelligence
==========================================
Implements the four-tier timeline processing pipeline:

    Tier 1 — Source-Local Timeline
        Raw chronological events per individual exhibit.
        Clock source: device EXIF / video timecode / document timestamp.

    Tier 2 — Normalized Timeline
        Timestamps normalized to UTC with uncertainty windows (±Δt).
        Handles clock drift corrections and approximate time ranges.

    Tier 3 — Correlated Timeline
        Multi-source alignment that clusters concurrent events from
        independent sources (CCTV + Witness + POS + Forensic).

    Tier 4 — Timeline Break Detector
        Identifies discontinuities in temporal continuity.
        Strictly NEVER inserts synthetic or interpolated bridge events.
        For every break, records:
          - start / end timestamps and duration
          - affected source(s)
          - reason for the break
          - surrounding evidence references (what came before / after)
          - what CANNOT be inferred across the break

CARDINAL RULE:
    No synthetic events will be inserted to bridge a timeline gap.
    A break is a documented evidentiary void, not an opportunity for
    hallucinated reconstruction.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SourceEvent:
    """A single event from one specific evidence source."""
    event_id: str
    source_id: str            # evidence_id or engine_id that produced this event
    source_type: str          # "CCTV", "WITNESS_STATEMENT", "POS", "FORENSIC", etc.
    timestamp: Optional[datetime]
    timestamp_uncertainty_seconds: float = 0.0
    event_type: str = ""      # e.g. "PERSON_DETECTED", "TRANSACTION", "DAMAGE_OBSERVED"
    description: str = ""
    entity_refs: List[str] = field(default_factory=list)   # e.g. ["P1", "ITEM1"]
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedEvent:
    """Source event with UTC-normalized timestamp and drift metadata."""
    source_event: SourceEvent
    normalized_timestamp: Optional[datetime]
    drift_applied_seconds: float = 0.0
    confidence: str = "APPROXIMATE"   # "EXACT", "APPROXIMATE", "ESTIMATED", "UNKNOWN"
    normalization_note: str = ""


@dataclass
class CorrelatedEvent:
    """Two or more normalized events from different sources that are temporally coincident."""
    correlation_id: str
    timestamp_window_start: datetime
    timestamp_window_end: datetime
    sources: List[str]
    events: List[NormalizedEvent]
    correlation_type: str = "TEMPORAL_COINCIDENCE"   # or "SPATIAL_COINCIDENCE", "ENTITY_MATCH"
    confidence: float = 0.7
    description: str = ""


@dataclass
class TimelineBreak:
    """
    A documented evidentiary discontinuity.

    A break represents a period where temporal continuity cannot be established.
    It is explicitly NOT a reconstructed event — it is a recorded void.
    """
    break_id: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    affected_sources: List[str]
    reason: str
    surrounding_evidence_before: List[str]   # event_ids immediately preceding break
    surrounding_evidence_after: List[str]    # event_ids immediately following break
    what_cannot_be_inferred: List[str]       # Explicit statements of inference impossibility
    significance: str = "HIGH"               # "LOW", "MEDIUM", "HIGH", "CRITICAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "break_id": self.break_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "affected_sources": self.affected_sources,
            "reason": self.reason,
            "surrounding_evidence_before": self.surrounding_evidence_before,
            "surrounding_evidence_after": self.surrounding_evidence_after,
            "what_cannot_be_inferred": self.what_cannot_be_inferred,
            "significance": self.significance,
            "fabrication_guard": (
                "NO_SYNTHETIC_EVENTS: This break represents a genuine evidentiary void. "
                "No events, positions, or actions may be inferred within this interval."
            ),
        }


# ---------------------------------------------------------------------------
# Tier 1: Source-Local Timeline Builder
# ---------------------------------------------------------------------------

class SourceLocalTimelineBuilder:
    """
    Builds raw chronological event sequences per evidence source.

    Accepts engine outputs from any tier and extracts timestamped events.
    Does NOT reorder, correct, or normalize timestamps.
    """

    def build(
        self,
        engine_outputs: Dict[str, Any],   # engine_id → EngineExecutionRecord
        evidence_type_map: Dict[str, str], # evidence_id → evidence_type string
    ) -> Dict[str, List[SourceEvent]]:
        """
        Returns {source_id: [SourceEvent, ...]} ordered by raw timestamp.
        """
        timelines: Dict[str, List[SourceEvent]] = {}

        # Only engines that emit empirical physical/sensor/ledger timeline observations
        TIMELINE_PRODUCING_ENGINES = {"I12", "FI04", "FI01", "I11", "F01"}

        for engine_id, record in engine_outputs.items():
            if engine_id not in TIMELINE_PRODUCING_ENGINES:
                continue
            outputs = getattr(record, "outputs", None) or []
            ev_ids = getattr(record, "evidence_ids", []) or []
            source_id = ev_ids[0] if ev_ids else engine_id
            src_type = evidence_type_map.get(source_id, engine_id[:2].upper())

            events: List[SourceEvent] = []
            for idx, item in enumerate(outputs):
                if not isinstance(item, dict):
                    continue
                raw_ts = item.get("timestamp") or item.get("observed_time") or item.get("event_time") or item.get("stated_time")
                if not raw_ts:
                    continue
                ts = _parse_timestamp(raw_ts)
                if not ts:
                    continue

                desc = (
                    item.get("description")
                    or item.get("label")
                    or item.get("action_observed")
                    or item.get("event_name")
                    or item.get("observation")
                    or ""
                ).strip()

                # Semantic description resolution for structured items
                if not desc:
                    if "transaction_id" in item:
                        desc = f"POS Transaction {item.get('transaction_id')} on terminal {item.get('terminal_id', 'TERM')}"
                    elif "event_type" in item and item.get("event_type") in ("FORCED_DOOR_ALERT", "PERIMETER_ALARM"):
                        desc = f"Security alarm event: {item.get('event_type')}"
                    elif "actor_described" in item:
                        desc = f"Witness observation of {item.get('actor_described')}"
                    else:
                        # Do NOT fabricate generic debug record strings like "I1 record from ..."
                        continue

                # Exclude debug/engine artifacts
                if "record from" in desc.lower() or desc.lower().startswith("engine record"):
                    continue

                ev_type = item.get("event_type") or item.get("observation_type")
                if not ev_type or ev_type in ("I1", "F0", "X0", "I01", "I02", "I06", "F02", "F03", "X01", "OBSERVATION"):
                    if "transaction" in desc.lower():
                        ev_type = "POS_TRANSACTION"
                    elif "alarm" in desc.lower() or "door" in desc.lower():
                        ev_type = "PERIMETER_ALARM"
                    elif "photo" in desc.lower():
                        ev_type = "FORENSIC_PHOTOGRAPHY"
                    elif "witness" in desc.lower():
                        ev_type = "WITNESS_TESTIMONIAL"
                    else:
                        ev_type = "INVESTIGATIVE_OBSERVATION"

                events.append(SourceEvent(
                    event_id=item.get("event_id") or f"{engine_id}_{idx}",
                    source_id=source_id,
                    source_type=src_type,
                    timestamp=ts,
                    event_type=ev_type,
                    description=desc,
                    entity_refs=item.get("entity_refs", []) or ([item.get("actor_id")] if item.get("actor_id") else []),
                    raw_data=item,
                ))

            if events:
                events.sort(key=lambda e: e.timestamp or datetime.max.replace(tzinfo=timezone.utc))
                timelines.setdefault(source_id, []).extend(events)

        return timelines


# ---------------------------------------------------------------------------
# Tier 2: Timestamp Normalizer
# ---------------------------------------------------------------------------

class TimestampNormalizer:
    """
    Normalizes raw device timestamps to UTC with uncertainty annotations.

    Handles:
    - Naive datetime → UTC assumption
    - Clock drift specification (e.g. CCTV running 4 minutes slow)
    - Approximate time windows with ± bounds
    """

    def __init__(self, drift_map: Optional[Dict[str, float]] = None):
        """
        drift_map: {source_id: drift_seconds}
            positive = device clock is ahead of UTC
            negative = device clock is behind UTC
        """
        self.drift_map: Dict[str, float] = drift_map or {}

    def normalize(
        self,
        source_timelines: Dict[str, List[SourceEvent]],
    ) -> Dict[str, List[NormalizedEvent]]:
        normalized: Dict[str, List[NormalizedEvent]] = {}

        for source_id, events in source_timelines.items():
            drift = self.drift_map.get(source_id, 0.0)
            norm_events: List[NormalizedEvent] = []

            for ev in events:
                norm_ts = None
                drift_applied = 0.0
                confidence = "UNKNOWN"
                note = ""

                if ev.timestamp:
                    ts = ev.timestamp
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                        note = "Naive timestamp assumed UTC."
                        confidence = "APPROXIMATE"
                    else:
                        confidence = "EXACT"

                    if drift:
                        ts = ts - timedelta(seconds=drift)
                        drift_applied = drift
                        note += f" Clock drift corrected by {drift:+.1f}s."
                        confidence = "APPROXIMATE"

                    norm_ts = ts
                else:
                    confidence = "UNKNOWN"
                    note = "Timestamp absent; cannot normalize."

                norm_events.append(NormalizedEvent(
                    source_event=ev,
                    normalized_timestamp=norm_ts,
                    drift_applied_seconds=drift_applied,
                    confidence=confidence,
                    normalization_note=note.strip(),
                ))

            normalized[source_id] = norm_events

        return normalized


# ---------------------------------------------------------------------------
# Tier 3: Cross-Source Correlator
# ---------------------------------------------------------------------------

class CrossSourceCorrelator:
    """
    Identifies temporally coincident events from independent sources.

    Two events are correlated if their normalized timestamps fall within
    `correlation_window_seconds` of each other.

    Note: Correlation is a structural observation — it does NOT imply
    causal connection or identity.
    """

    def __init__(self, correlation_window_seconds: float = 120.0):
        self.window = timedelta(seconds=correlation_window_seconds)

    def correlate(
        self,
        normalized_timelines: Dict[str, List[NormalizedEvent]],
    ) -> List[CorrelatedEvent]:
        """
        Returns a list of CorrelatedEvent clusters.
        Two+ events from different sources within the window are clustered.
        """
        # Flatten all events with source tracking
        all_events: List[Tuple[str, NormalizedEvent]] = []
        for src, events in normalized_timelines.items():
            for ev in events:
                if ev.normalized_timestamp:
                    all_events.append((src, ev))

        # Sort by normalized timestamp
        all_events.sort(key=lambda x: x[1].normalized_timestamp)

        correlations: List[CorrelatedEvent] = []
        used: set = set()

        for i, (src_i, ev_i) in enumerate(all_events):
            if i in used:
                continue
            cluster_sources = [src_i]
            cluster_events = [ev_i]

            for j, (src_j, ev_j) in enumerate(all_events[i + 1:], start=i + 1):
                if j in used:
                    continue
                if src_j == src_i:
                    continue  # Same source = not cross-source correlation
                delta = abs(ev_j.normalized_timestamp - ev_i.normalized_timestamp)
                if delta <= self.window:
                    cluster_sources.append(src_j)
                    cluster_events.append(ev_j)
                    used.add(j)
                elif ev_j.normalized_timestamp > ev_i.normalized_timestamp + self.window:
                    break

            if len(cluster_events) >= 2:
                used.add(i)
                ts_start = min(e.normalized_timestamp for e in cluster_events)
                ts_end = max(e.normalized_timestamp for e in cluster_events)
                corr_id = f"CORR_{i:04d}"
                correlations.append(CorrelatedEvent(
                    correlation_id=corr_id,
                    timestamp_window_start=ts_start,
                    timestamp_window_end=ts_end,
                    sources=list(set(cluster_sources)),
                    events=cluster_events,
                    description=(
                        f"{len(cluster_events)} events from "
                        f"{len(set(cluster_sources))} sources within "
                        f"{(ts_end - ts_start).total_seconds():.0f}s window."
                    ),
                ))

        return correlations


# ---------------------------------------------------------------------------
# Tier 4: Timeline Break Detector
# ---------------------------------------------------------------------------

_GAP_SIGNIFICANCE_THRESHOLDS = {
    "CRITICAL": 3600,   # 1 hour+
    "HIGH":     900,    # 15 minutes+
    "MEDIUM":   300,    # 5 minutes+
    "LOW":      60,     # 1 minute+
}


class TimelineBreakDetector:
    """
    Identifies gaps in temporal continuity within each source timeline.

    A break is detected when consecutive events from the same source
    are separated by more than `min_gap_seconds`.

    CARDINAL RULE: No synthetic events are generated.
    Every break is documented as an explicit evidentiary void.
    """

    def __init__(
        self,
        min_gap_seconds: float = 300.0,  # 5 minutes default
        expected_continuity_sources: Optional[List[str]] = None,
    ):
        self.min_gap = timedelta(seconds=min_gap_seconds)
        self.continuity_sources = expected_continuity_sources or []

    def detect(
        self,
        normalized_timelines: Dict[str, List[NormalizedEvent]],
    ) -> List[TimelineBreak]:
        """
        Returns list of TimelineBreak records for all detected discontinuities.
        Never modifies the timelines.
        """
        breaks: List[TimelineBreak] = []
        break_counter = 0

        for source_id, events in normalized_timelines.items():
            # Filter to events with known timestamps
            timed = [e for e in events if e.normalized_timestamp is not None]
            timed.sort(key=lambda e: e.normalized_timestamp)

            for i in range(len(timed) - 1):
                ev_a = timed[i]
                ev_b = timed[i + 1]
                gap = ev_b.normalized_timestamp - ev_a.normalized_timestamp

                if gap >= self.min_gap:
                    duration_s = gap.total_seconds()
                    significance = "LOW"
                    for sig, threshold in _GAP_SIGNIFICANCE_THRESHOLDS.items():
                        if duration_s >= threshold:
                            significance = sig
                            break

                    break_counter += 1
                    breaks.append(TimelineBreak(
                        break_id=f"BREAK_{break_counter:04d}_{source_id[:8]}",
                        start_time=ev_a.normalized_timestamp,
                        end_time=ev_b.normalized_timestamp,
                        duration_seconds=duration_s,
                        affected_sources=[source_id],
                        reason=(
                            f"No recorded events from source '{source_id}' "
                            f"for {duration_s / 60:.1f} minutes "
                            f"(between event '{ev_a.source_event.event_id}' "
                            f"and '{ev_b.source_event.event_id}')."
                        ),
                        surrounding_evidence_before=[ev_a.source_event.event_id],
                        surrounding_evidence_after=[ev_b.source_event.event_id],
                        what_cannot_be_inferred=_build_cannot_infer(
                            source_id, duration_s, ev_a, ev_b
                        ),
                        significance=significance,
                    ))

        return sorted(breaks, key=lambda b: b.start_time or datetime.max.replace(tzinfo=timezone.utc))


def _build_cannot_infer(
    source_id: str,
    duration_s: float,
    before: NormalizedEvent,
    after: NormalizedEvent,
) -> List[str]:
    """
    Generates explicit statements of what analytical conclusions
    CANNOT be drawn across this break.
    """
    statements = [
        f"The location, movement, or actions of any subject during the {duration_s / 60:.1f}-minute "
        f"gap in source '{source_id}' cannot be established from available evidence.",
        "Entity continuity across this break cannot be assumed — the same individual observed "
        "before and after the break cannot be confirmed to be the same person without additional corroboration.",
        "No timeline event may be synthetically inserted into this gap.",
    ]

    if "CCTV" in source_id.upper() or "VIDEO" in before.source_event.source_type.upper():
        statements.append(
            "Any movement, transaction, or interaction within the unmonitored interval "
            "cannot be attributed to any candidate entity."
        )
    if duration_s > 1800:
        statements.append(
            "Given the gap exceeds 30 minutes, alternative suspect pathways via unmonitored "
            "routes cannot be ruled out."
        )
    return statements


# ---------------------------------------------------------------------------
# Orchestrator: TimelineIntelligence
# ---------------------------------------------------------------------------

class TimelineIntelligence:
    """
    Top-level orchestrator that runs all four timeline tiers.

    Usage:
        ti = TimelineIntelligence(drift_map={evidence_id: drift_seconds})
        result = ti.process(engine_outputs, evidence_type_map)
    """

    def __init__(
        self,
        drift_map: Optional[Dict[str, float]] = None,
        correlation_window_seconds: float = 120.0,
        min_gap_seconds: float = 300.0,
    ):
        self.tier1 = SourceLocalTimelineBuilder()
        self.tier2 = TimestampNormalizer(drift_map=drift_map)
        self.tier3 = CrossSourceCorrelator(correlation_window_seconds=correlation_window_seconds)
        self.tier4 = TimelineBreakDetector(min_gap_seconds=min_gap_seconds)

    def process(
        self,
        engine_outputs: Dict[str, Any],
        evidence_type_map: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Returns a complete multi-tier timeline package suitable for
        storage in EngineExecutionRecord.outputs and API responses.
        """
        # Tier 1
        source_timelines = self.tier1.build(engine_outputs, evidence_type_map)

        # Tier 2
        normalized_timelines = self.tier2.normalize(source_timelines)

        # Tier 3
        correlated_events = self.tier3.correlate(normalized_timelines)

        # Tier 4
        breaks = self.tier4.detect(normalized_timelines)

        # Serialize
        return {
            "source_local_timelines": {
                src: [
                    {
                        "event_id": e.event_id,
                        "source_type": e.source_type,
                        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                        "event_type": e.event_type,
                        "description": e.description,
                        "entity_refs": e.entity_refs,
                    }
                    for e in events
                ]
                for src, events in source_timelines.items()
            },
            "normalized_timelines": {
                src: [
                    {
                        "event_id": e.source_event.event_id,
                        "source_id": e.source_event.source_id,
                        "source_type": e.source_event.source_type,
                        "observed_time": e.source_event.timestamp.isoformat() if e.source_event.timestamp else None,
                        "normalized_timestamp": e.normalized_timestamp.isoformat() if e.normalized_timestamp else None,
                        "event_type": e.source_event.event_type,
                        "description": e.source_event.description,
                        "entity_refs": e.source_event.entity_refs,
                        "drift_applied_seconds": e.drift_applied_seconds,
                        "confidence": e.confidence,
                        "normalization_note": e.normalization_note,
                    }
                    for e in events
                ]
                for src, events in normalized_timelines.items()
            },
            "correlated_events": [
                {
                    "correlation_id": c.correlation_id,
                    "window_start": c.timestamp_window_start.isoformat(),
                    "window_end": c.timestamp_window_end.isoformat(),
                    "sources": c.sources,
                    "event_count": len(c.events),
                    "correlation_type": c.correlation_type,
                    "description": c.description,
                }
                for c in correlated_events
            ],
            "timeline_breaks": [b.to_dict() for b in breaks],
            "break_count": len(breaks),
            "correlated_event_count": len(correlated_events),
            "timeline_summary": {
                "source_count": len(source_timelines),
                "total_source_events": sum(len(v) for v in source_timelines.values()),
                "total_normalized_events": sum(len(v) for v in normalized_timelines.values()),
                "total_correlated_clusters": len(correlated_events),
                "total_breaks": len(breaks),
                "critical_breaks": len([b for b in breaks if b.significance == "CRITICAL"]),
                "fabrication_guard": (
                    "NO_SYNTHETIC_EVENTS: All timeline breaks represent genuine "
                    "evidentiary voids. No events have been interpolated or generated."
                ),
            },
        }


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _parse_timestamp(value: Any) -> Optional[datetime]:
    """Safely parse a timestamp value into a datetime object."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None
