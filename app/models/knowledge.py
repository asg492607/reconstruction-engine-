"""
Phase 9: Case Knowledge / Research Store
=========================================
Provides a per-case, role-gated knowledge repository.

Use cases:
  - Store domain knowledge relevant to the case type (e.g. shoplifting tactics,
    CCTV evidence standards, vehicle theft MO taxonomy)
  - Store legal precedents / case law relevant to admissibility
  - Store investigative research notes about the case context
  - Make this context available to reconstruction engines as supplementary input

NON-CONTAMINATION GUARD:
  Historical case data is strictly segregated from current analytical evidence.
  Knowledge items are tagged as "RESEARCH" not "EVIDENCE".
  No engine output may cite a knowledge item as if it were a current exhibit.
  All knowledge items carry an immutable `is_evidence = False` flag.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import String, Boolean, DateTime, JSON, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Knowledge Item Category Enum
# ---------------------------------------------------------------------------

class KnowledgeCategory(str, Enum):
    DOMAIN_KNOWLEDGE     = "DOMAIN_KNOWLEDGE"     # General criminology / MO taxonomy
    LEGAL_PRECEDENT      = "LEGAL_PRECEDENT"      # Case law / admissibility standards
    INVESTIGATIVE_NOTE   = "INVESTIGATIVE_NOTE"   # Investigator research notes
    TECHNICAL_STANDARD   = "TECHNICAL_STANDARD"   # e.g. CCTV resolution minimums
    COMPARATIVE_CONTEXT  = "COMPARATIVE_CONTEXT"  # Aggregated base-rates (anonymous)
    TOOL_REFERENCE       = "TOOL_REFERENCE"       # External reference documents


# ---------------------------------------------------------------------------
# ORM Model
# ---------------------------------------------------------------------------

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _gen_uuid() -> str:
    return str(uuid.uuid4())


class CaseKnowledgeItem(Base):
    """
    A research / domain knowledge item attached to a specific case.

    IMMUTABLE FLAGS:
      is_evidence = False always. This field cannot be set to True
      through normal service methods (enforced in KnowledgeService).
    """
    __tablename__ = "case_knowledge_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_gen_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    category: Mapped[KnowledgeCategory] = mapped_column(
        SAEnum(KnowledgeCategory, native_enum=False),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_citation: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    added_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # IMMUTABLE: Knowledge items are never evidence
    is_evidence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
