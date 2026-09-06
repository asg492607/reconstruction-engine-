"""
Phase 9: Case Knowledge REST API Router
========================================
Endpoints for managing non-evidentiary case research and domain reference knowledge.

NON-CONTAMINATION POLICY:
  - All knowledge items are tagged with is_evidence=False.
  - Knowledge items provide strategy context, not current-case evidence.
  - They cannot be inserted into the case observation graph or cited as exhibits.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import User
from app.models.knowledge import KnowledgeCategory
from app.dependencies import get_current_user
from app.knowledge.service import knowledge_service

router = APIRouter(prefix="/cases/{case_id}/knowledge", tags=["case-knowledge"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class KnowledgeItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    category: KnowledgeCategory = Field(default=KnowledgeCategory.DOMAIN_KNOWLEDGE)
    source_url: Optional[str] = None
    source_citation: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)


class KnowledgeItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    added_by: str
    title: str
    content: str
    category: str
    source_url: Optional[str] = None
    source_citation: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_evidence: bool = False
    created_at: str
    knowledge_guard: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=List[KnowledgeItemResponse])
async def list_case_knowledge(
    case_id: str,
    category: Optional[KnowledgeCategory] = Query(None),
    tag: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all research and domain knowledge items for a case.
    Strictly segregated from evidence.
    """
    items = await knowledge_service.get_items(
        db=db,
        case_id=case_id,
        category=category,
        tag=tag,
    )
    return [
        KnowledgeItemResponse(
            id=item.id,
            case_id=item.case_id,
            added_by=item.added_by,
            title=item.title,
            content=item.content,
            category=item.category.value if hasattr(item.category, "value") else str(item.category),
            source_url=item.source_url,
            source_citation=item.source_citation,
            tags=item.tags or [],
            is_evidence=False,
            created_at=item.created_at.isoformat() if item.created_at else "",
            knowledge_guard="RESEARCH_CONTEXT_ONLY: Not admissible as factual exhibit evidence."
        )
        for item in items
    ]


@router.post("", response_model=KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
async def create_case_knowledge(
    case_id: str,
    payload: KnowledgeItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a domain research or reference knowledge item to a case.
    Enforces immutable non-contamination guard: is_evidence is unconditionally False.
    """
    item = await knowledge_service.create_item(
        db=db,
        case_id=case_id,
        added_by=current_user.id,
        title=payload.title,
        content=payload.content,
        category=payload.category,
        source_url=payload.source_url,
        source_citation=payload.source_citation,
        tags=payload.tags,
    )
    return KnowledgeItemResponse(
        id=item.id,
        case_id=item.case_id,
        added_by=item.added_by,
        title=item.title,
        content=item.content,
        category=item.category.value if hasattr(item.category, "value") else str(item.category),
        source_url=item.source_url,
        source_citation=item.source_citation,
        tags=item.tags or [],
        is_evidence=False,
        created_at=item.created_at.isoformat() if item.created_at else "",
        knowledge_guard="RESEARCH_CONTEXT_ONLY: Not admissible as factual exhibit evidence."
    )


@router.get("/{item_id}", response_model=KnowledgeItemResponse)
async def get_case_knowledge_item(
    case_id: str,
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single knowledge item by ID."""
    item = await knowledge_service.get_item_by_id(db=db, item_id=item_id)
    if not item or item.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge item '{item_id}' not found in case '{case_id}'."
        )
    return KnowledgeItemResponse(
        id=item.id,
        case_id=item.case_id,
        added_by=item.added_by,
        title=item.title,
        content=item.content,
        category=item.category.value if hasattr(item.category, "value") else str(item.category),
        source_url=item.source_url,
        source_citation=item.source_citation,
        tags=item.tags or [],
        is_evidence=False,
        created_at=item.created_at.isoformat() if item.created_at else "",
        knowledge_guard="RESEARCH_CONTEXT_ONLY: Not admissible as factual exhibit evidence."
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case_knowledge_item(
    case_id: str,
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a research knowledge item from a case."""
    deleted = await knowledge_service.delete_item(db=db, item_id=item_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge item '{item_id}' not found."
        )
    return None
