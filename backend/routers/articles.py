"""
Articles Router
===============
API endpoints for article CRUD operations.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Path

from ..models.article import Article, ArticleSummary, ArticleListResponse
from ..services.content_loader import get_content_loader

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get(
    "",
    response_model=ArticleListResponse,
    summary="List Articles",
    description="Get a paginated list of articles with optional filtering.",
)
async def list_articles(
    category: Optional[str] = Query(
        None,
        description="Filter by category ID (e.g., '01-theoretical-frontiers')"
    ),
    subcategory: Optional[str] = Query(
        None,
        description="Filter by subcategory slug (e.g., 'consciousness-hard-problem')"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List articles with optional filtering and pagination.

    Supports filtering by:
    - category: Main category ID
    - subcategory: Subcategory slug

    Results are sorted by category and subcategory.
    """
    loader = get_content_loader()

    return loader.list_articles(
        category_id=category,
        subcategory=subcategory,
        page=page,
        per_page=per_page,
    )


@router.get(
    "/{article_id:path}",
    response_model=Article,
    summary="Get Article",
    description="Get a single article by ID with full content.",
)
async def get_article(
    article_id: str = Path(
        ...,
        description="Article ID (e.g., '01-theoretical-frontiers/consciousness-hard-problem')"
    ),
):
    """
    Get a single article with full content.

    The article ID is in the format: `category-id/subcategory-slug`

    Returns:
    - Full article content (markdown and HTML)
    - Metadata from docstring header
    - Table of contents
    - Companion documents (notes, citations) if available
    - Related articles
    """
    loader = get_content_loader()
    article = loader.get_article(article_id)

    if not article:
        raise HTTPException(
            status_code=404,
            detail=f"Article not found: {article_id}"
        )

    return article


@router.get(
    "/{article_id:path}/notes",
    summary="Get Article Notes",
    description="Get the companion notes for an article.",
)
async def get_article_notes(
    article_id: str = Path(
        ...,
        description="Article ID"
    ),
):
    """
    Get the personal notes companion document for an article.

    Returns the parsed notes content if available.
    """
    loader = get_content_loader()
    article = loader.get_article(article_id)

    if not article:
        raise HTTPException(
            status_code=404,
            detail=f"Article not found: {article_id}"
        )

    if not article.has_notes or not article.notes:
        raise HTTPException(
            status_code=404,
            detail=f"Notes not found for article: {article_id}"
        )

    return {
        "article_id": article_id,
        "type": "notes",
        "content": article.notes.content,
        "content_html": article.notes.content_html,
        "word_count": article.notes.word_count,
    }


@router.get(
    "/{article_id:path}/citations",
    summary="Get Article Citations",
    description="Get the works cited for an article.",
)
async def get_article_citations(
    article_id: str = Path(
        ...,
        description="Article ID"
    ),
):
    """
    Get the works cited companion document for an article.

    Returns the parsed citations content if available.
    """
    loader = get_content_loader()
    article = loader.get_article(article_id)

    if not article:
        raise HTTPException(
            status_code=404,
            detail=f"Article not found: {article_id}"
        )

    if not article.has_citations or not article.citations:
        raise HTTPException(
            status_code=404,
            detail=f"Citations not found for article: {article_id}"
        )

    return {
        "article_id": article_id,
        "type": "citations",
        "content": article.citations.content,
        "content_html": article.citations.content_html,
        "word_count": article.citations.word_count,
    }


@router.get(
    "/{article_id:path}/related",
    response_model=list[ArticleSummary],
    summary="Get Related Articles",
    description="Get articles related to the specified article.",
)
async def get_related_articles(
    article_id: str = Path(
        ...,
        description="Article ID"
    ),
    limit: int = Query(5, ge=1, le=20, description="Maximum related articles"),
):
    """
    Get articles related to the specified article.

    Relationships are determined by:
    - Shared tags
    - Same category/subcategory
    - Cross-references in content
    """
    loader = get_content_loader()

    # Verify article exists
    article = loader.get_article(article_id)
    if not article:
        raise HTTPException(
            status_code=404,
            detail=f"Article not found: {article_id}"
        )

    return loader.get_related_articles(article_id, limit=limit)


@router.get(
    "/{article_id:path}/toc",
    summary="Get Article Table of Contents",
    description="Get just the table of contents for an article.",
)
async def get_article_toc(
    article_id: str = Path(
        ...,
        description="Article ID"
    ),
):
    """
    Get the table of contents for an article.

    Useful for rendering navigation without loading full content.
    """
    loader = get_content_loader()
    article = loader.get_article(article_id)

    if not article:
        raise HTTPException(
            status_code=404,
            detail=f"Article not found: {article_id}"
        )

    return {
        "article_id": article_id,
        "title": article.metadata.title,
        "toc": [t.model_dump() for t in article.content.toc],
    }
