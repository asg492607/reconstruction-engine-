"""
Phase 9: Case Knowledge Service
================================
CRUD operations for CaseKnowledgeItem.

NON-CONTAMINATION GUARD:
  The `create_knowledge_item` method sets is_evidence=False unconditionally.
  Knowledge items returned from this service carry a `_knowledge_guard` field
  in their serialized form indicating they are research context, not evidence.

  When knowledge is injected into an engine context, it is passed via a separate
  `research_context` field on EngineContext — never into the evidence vault.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import CaseKnowledgeItem, KnowledgeCategory

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Knowledge Service
# ---------------------------------------------------------------------------

class KnowledgeService:

    async def create_item(
        self,
        db: AsyncSession,
        case_id: str,
        added_by: str,
        title: str,
        content: str,
        category: KnowledgeCategory,
        source_url: Optional[str] = None,
        source_citation: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> CaseKnowledgeItem:
        """
        Creates a knowledge item for a case.
        NON-CONTAMINATION: is_evidence is always False.
        """
        item = CaseKnowledgeItem(
            case_id=case_id,
            added_by=added_by,
            title=title,
            content=content,
            category=category,
            source_url=source_url,
            source_citation=source_citation,
            tags=tags or [],
            is_evidence=False,  # IMMUTABLE — never set to True
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        logger.info("Knowledge item created: case=%s id=%s category=%s", case_id, item.id, category.value)
        return item

    async def get_items(
        self,
        db: AsyncSession,
        case_id: str,
        category: Optional[KnowledgeCategory] = None,
    ) -> List[CaseKnowledgeItem]:
        stmt = select(CaseKnowledgeItem).where(CaseKnowledgeItem.case_id == case_id)
        if category:
            stmt = stmt.where(CaseKnowledgeItem.category == category)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def delete_item(self, db: AsyncSession, item_id: str) -> bool:
        stmt = delete(CaseKnowledgeItem).where(CaseKnowledgeItem.id == item_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    def serialize_for_engine(self, items: List[CaseKnowledgeItem]) -> List[Dict[str, Any]]:
        """
        Serializes knowledge items for injection into EngineContext.research_context.
        Every item carries _knowledge_guard to prevent engines from treating it as evidence.
        """
        return [
            {
                "id": item.id,
                "category": item.category.value,
                "title": item.title,
                "content": item.content,
                "source_citation": item.source_citation,
                "tags": item.tags or [],
                "_knowledge_guard": (
                    "RESEARCH_CONTEXT: This item is domain knowledge / research context, "
                    "NOT a case exhibit. It must never be cited as evidence in analytical outputs."
                ),
                "is_evidence": False,
            }
            for item in items
        ]


knowledge_service = KnowledgeService()
