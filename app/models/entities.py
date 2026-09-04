import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import (
    String, Boolean, Integer, Float, DateTime, ForeignKey, Text, JSON, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import (
    Role, Department, CaseType, CaseStatus, EvidenceType, ProcessingStatus,
    ObservationType, TimeConfidence, TimeReliability, EvidenceQuality,
    VerificationStatus, EntityType, IdentityStatus, GeneratedBy, ClaimStrength,
    HypothesisStatus, GapConflictType, Significance, TargetType, VerificationAction
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def gen_uuid() -> str:
    return str(uuid.uuid4())

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    users: Mapped[List["User"]] = relationship("User", back_populates="organization")
    cases: Mapped[List["Case"]] = relationship("Case", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[Role] = mapped_column(SAEnum(Role, native_enum=False), default=Role.INVESTIGATOR, nullable=False)
    department: Mapped[Department] = mapped_column(SAEnum(Department, native_enum=False), default=Department.INVESTIGATION, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="users")
    assignments: Mapped[List["CaseAssignment"]] = relationship("CaseAssignment", foreign_keys="CaseAssignment.user_id", back_populates="user")


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    case_type: Mapped[CaseType] = mapped_column(SAEnum(CaseType, native_enum=False), default=CaseType.THEFT, nullable=False)
    status: Mapped[CaseStatus] = mapped_column(SAEnum(CaseStatus, native_enum=False), default=CaseStatus.CREATED, nullable=False)
    incident_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    incident_time_observed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    incident_time_estimated: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # {min: ..., max: ...}
    organization_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="cases")
    evidence_items: Mapped[List["Evidence"]] = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    observations: Mapped[List["Observation"]] = relationship("Observation", back_populates="case", cascade="all, delete-orphan")
    assignments: Mapped[List["CaseAssignment"]] = relationship("CaseAssignment", back_populates="case", cascade="all, delete-orphan")
    versions: Mapped[List["CaseVersion"]] = relationship("CaseVersion", back_populates="case", cascade="all, delete-orphan")


class CaseVersion(Base):
    __tablename__ = "case_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="versions")


class CaseAssignment(Base):
    __tablename__ = "case_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    department: Mapped[Department] = mapped_column(SAEnum(Department, native_enum=False), nullable=False)
    assigned_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    case: Mapped["Case"] = relationship("Case", back_populates="assignments")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="assignments")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    evidence_type: Mapped[EvidenceType] = mapped_column(SAEnum(EvidenceType, native_enum=False), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False) # Local path or MinIO key (immutable)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False) # SHA-256 fingerprint
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    uploaded_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    is_classified: Mapped[bool] = mapped_column(Boolean, default=False)
    classification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authorized_departments: Mapped[list] = mapped_column(JSON, default=list) # e.g. ["INVESTIGATION", "FORENSIC"]
    processing_status: Mapped[ProcessingStatus] = mapped_column(SAEnum(ProcessingStatus, native_enum=False), default=ProcessingStatus.PENDING)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict) # camera_id, location, etc.

    case: Mapped["Case"] = relationship("Case", back_populates="evidence_items")
    observations: Mapped[List["Observation"]] = relationship("Observation", back_populates="evidence", cascade="all, delete-orphan")


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    evidence_id: Mapped[str] = mapped_column(String(36), ForeignKey("evidence.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    department: Mapped[Department] = mapped_column(SAEnum(Department, native_enum=False), nullable=False)
    observation_type: Mapped[ObservationType] = mapped_column(SAEnum(ObservationType, native_enum=False), nullable=False)
    
    # Raw output preserved
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)

    # Temporal info
    observed_time_raw: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    observed_time_parsed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_confidence: Mapped[TimeConfidence] = mapped_column(SAEnum(TimeConfidence, native_enum=False), default=TimeConfidence.UNKNOWN)
    time_source: Mapped[Optional[str]] = mapped_column(String(128), nullable=True) # "camera_timestamp", "gps", etc.
    time_reliability: Mapped[TimeReliability] = mapped_column(SAEnum(TimeReliability, native_enum=False), default=TimeReliability.UNKNOWN)
    estimated_clock_offset: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    time_window_min: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_window_max: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Spatial info
    location_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bounding_box: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # {x, y, w, h}
    frame_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Quality & Provenance
    observation_confidence: Mapped[float] = mapped_column(Float, default=0.0) # 0.0 - 1.0
    evidence_quality: Mapped[EvidenceQuality] = mapped_column(SAEnum(EvidenceQuality, native_enum=False), default=EvidenceQuality.MEDIUM)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    processing_job_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    derived_from_observation_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("observations.id"), nullable=True)

    # Human Verification
    verification_status: Mapped[VerificationStatus] = mapped_column(SAEnum(VerificationStatus, native_enum=False), default=VerificationStatus.PENDING)
    verified_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    evidence: Mapped["Evidence"] = relationship("Evidence", back_populates="observations")
    case: Mapped["Case"] = relationship("Case", back_populates="observations")
    candidate_links: Mapped[List["CandidateEntityLink"]] = relationship("CandidateEntityLink", back_populates="observation", cascade="all, delete-orphan")


class CandidateEntity(Base):
    __tablename__ = "candidate_entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(SAEnum(EntityType, native_enum=False), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False) # e.g. "P1", "V1", "ITEM-PHONE"
    description: Mapped[dict] = mapped_column(JSON, default=dict)
    first_observed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_observed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    identity_status: Mapped[IdentityStatus] = mapped_column(SAEnum(IdentityStatus, native_enum=False), default=IdentityStatus.UNKNOWN)
    identity_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    links: Mapped[List["CandidateEntityLink"]] = relationship("CandidateEntityLink", back_populates="candidate_entity", cascade="all, delete-orphan")


class CandidateEntityLink(Base):
    __tablename__ = "candidate_entity_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    observation_id: Mapped[str] = mapped_column(String(36), ForeignKey("observations.id"), nullable=False)
    candidate_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_entities.id"), nullable=False)
    link_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    link_evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    link_method: Mapped[str] = mapped_column(String(128), default="manual")
    is_human_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    observation: Mapped["Observation"] = relationship("Observation", back_populates="candidate_links")
    candidate_entity: Mapped["CandidateEntity"] = relationship("CandidateEntity", back_populates="links")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    department: Mapped[Department] = mapped_column(SAEnum(Department, native_enum=False), nullable=False)
    finding_type: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    observation_ids: Mapped[list] = mapped_column(JSON, default=list) # UUID list
    entity_ids: Mapped[list] = mapped_column(JSON, default=list)
    time_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Composite confidence
    detection_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    corroboration_count: Mapped[int] = mapped_column(Integer, default=1)
    corroboration_sources: Mapped[list] = mapped_column(JSON, default=list) # evidence IDs
    is_contradicted_by: Mapped[list] = mapped_column(JSON, default=list)

    # Attribution
    generated_by: Mapped[GeneratedBy] = mapped_column(SAEnum(GeneratedBy, native_enum=False), default=GeneratedBy.AI)
    model_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Verification
    verification_status: Mapped[VerificationStatus] = mapped_column(SAEnum(VerificationStatus, native_enum=False), default=VerificationStatus.PENDING)
    verified_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    correction_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    finding_ids: Mapped[list] = mapped_column(JSON, default=list)
    claim_strength: Mapped[ClaimStrength] = mapped_column(SAEnum(ClaimStrength, native_enum=False), default=ClaimStrength.MODERATE)
    contradicted_by_finding_ids: Mapped[list] = mapped_column(JSON, default=list)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SourceTimeline(Base):
    __tablename__ = "source_timelines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    source_label: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_id: Mapped[str] = mapped_column(String(36), ForeignKey("evidence.id"), nullable=False)
    department: Mapped[Department] = mapped_column(SAEnum(Department, native_enum=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    events: Mapped[List["SourceTimelineEvent"]] = relationship("SourceTimelineEvent", back_populates="timeline", cascade="all, delete-orphan")


class SourceTimelineEvent(Base):
    __tablename__ = "source_timeline_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    source_timeline_id: Mapped[str] = mapped_column(String(36), ForeignKey("source_timelines.id"), nullable=False)
    observation_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("observations.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    observed_time_raw: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    event_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_confidence: Mapped[TimeConfidence] = mapped_column(SAEnum(TimeConfidence, native_enum=False), default=TimeConfidence.UNKNOWN)
    time_window_min: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_window_max: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    entity_ids: Mapped[list] = mapped_column(JSON, default=list)
    sequence_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    timeline: Mapped["SourceTimeline"] = relationship("SourceTimeline", back_populates="events")


class CorrelatedTimelineEvent(Base):
    __tablename__ = "correlated_timeline_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    event_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_confidence: Mapped[TimeConfidence] = mapped_column(SAEnum(TimeConfidence, native_enum=False), default=TimeConfidence.UNKNOWN)
    time_window_min: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_window_max: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_event_ids: Mapped[list] = mapped_column(JSON, default=list)
    supporting_evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    entity_ids: Mapped[list] = mapped_column(JSON, default=list)
    department: Mapped[Department] = mapped_column(SAEnum(Department, native_enum=False), default=Department.CORRELATED)
    is_disputed: Mapped[bool] = mapped_column(Boolean, default=False)
    dispute_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    from_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_entities.id"), nullable=False)
    to_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_entities.id"), nullable=False)
    relationship: Mapped[str] = mapped_column(String(128), nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Hypothesis(Base):
    __tablename__ = "hypotheses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sequence: Mapped[list] = mapped_column(JSON, default=list) # [{step, entity_ids, evidence_ids, time}]
    supporting_claim_ids: Mapped[list] = mapped_column(JSON, default=list)
    contradicting_claim_ids: Mapped[list] = mapped_column(JSON, default=list)
    assumptions: Mapped[list] = mapped_column(JSON, default=list)
    unknowns: Mapped[list] = mapped_column(JSON, default=list)
    overall_strength: Mapped[ClaimStrength] = mapped_column(SAEnum(ClaimStrength, native_enum=False), default=ClaimStrength.MODERATE)
    
    # Self-challenge results
    deterministic_issues: Mapped[list] = mapped_column(JSON, default=list)
    ai_challenge_notes: Mapped[list] = mapped_column(JSON, default=list)

    status: Mapped[HypothesisStatus] = mapped_column(SAEnum(HypothesisStatus, native_enum=False), default=HypothesisStatus.DRAFT)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class GapConflict(Base):
    __tablename__ = "gaps_conflicts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    gc_type: Mapped[GapConflictType] = mapped_column(SAEnum(GapConflictType, native_enum=False), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    significance: Mapped[Significance] = mapped_column(SAEnum(Significance, native_enum=False), default=Significance.MEDIUM)
    significance_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    affected_evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    affected_observation_ids: Mapped[list] = mapped_column(JSON, default=list)
    affected_event_ids: Mapped[list] = mapped_column(JSON, default=list)
    affected_entity_ids: Mapped[list] = mapped_column(JSON, default=list)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    target_type: Mapped[TargetType] = mapped_column(SAEnum(TargetType, native_enum=False), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[VerificationAction] = mapped_column(SAEnum(VerificationAction, native_enum=False), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrected_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    verified_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    user_role: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    organization: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    before_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    after_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    report_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    generated_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ObservationEmbedding(Base):
    __tablename__ = "observation_embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    observation_id: Mapped[str] = mapped_column(String(36), ForeignKey("observations.id"), nullable=False)
    embedding: Mapped[list] = mapped_column(JSON, nullable=False) # Float vector stored as JSON array for SQLite/PG compatibility
    text_chunk: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
