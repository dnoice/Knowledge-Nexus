"""
Search Router
=============
API endpoints for full-text search and suggestions.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from ..models.search import (
    SearchQuery,
    SearchResponse,
    SuggestResponse,
    SearchFacets,
    FacetItem,
)
from ..services.indexer import SearchIndexer
from ..services.content_loader import get_content_loader
from ..config import get_categories

router = APIRouter(prefix="/api/search", tags=["search"])

# Global indexer instance
_indexer: Optional[SearchIndexer] = None


def get_indexer() -> SearchIndexer:
    """Get or create the search indexer."""
    global _indexer
    if _indexer is None:
        _indexer = SearchIndexer()
    return _indexer


@router.get(
    "",
    response_model=SearchResponse,
    summary="Search Articles",
    description="Full-text search across all articles.",
)
async def search(
    q: str = Query(
        ...,
        min_length=2,
        description="Search query string"
    ),
    categories: Optional[list[str]] = Query(
        None,
        description="Filter by category IDs"
    ),
    subcategories: Optional[list[str]] = Query(
        None,
        description="Filter by subcategory slugs"
    ),
    tags: Optional[list[str]] = Query(
        None,
        description="Filter by tags"
    ),
    fuzzy: bool = Query(
        True,
        description="Enable fuzzy matching for typo tolerance"
    ),
    highlight: bool = Query(
        True,
        description="Include highlighted snippets in results"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """
    Full-text search across all articles.

    Features:
    - Searches title, description, content, and tags
    - Supports fuzzy matching for typo tolerance
    - Category and tag filtering
    - Highlighted result snippets
    - Pagination

    Results are ranked by relevance score.
    """
    indexer = get_indexer()

    query = SearchQuery(
        q=q,
        categories=categories or [],
        subcategories=subcategories or [],
        tags=tags or [],
        fuzzy=fuzzy,
        highlight=highlight,
        page=page,
        per_page=per_page,
    )

    return indexer.search(query)


@router.get(
    "/suggest",
    response_model=SuggestResponse,
    summary="Get Suggestions",
    description="Get autocomplete suggestions for search.",
)
async def suggest(
    q: str = Query(
        ...,
        min_length=1,
        description="Partial search query"
    ),
    limit: int = Query(
        8,
        ge=1,
        le=20,
        description="Maximum suggestions"
    ),
):
    """
    Get autocomplete suggestions for search.

    Returns matching articles by title prefix.
    Used for the search autocomplete dropdown.
    """
    indexer = get_indexer()
    return indexer.suggest(q, limit=limit)


@router.get(
    "/facets",
    response_model=SearchFacets,
    summary="Get Search Facets",
    description="Get available filter facets for search.",
)
async def get_facets():
    """
    Get available filter facets for search refinement.

    Returns:
    - Categories with article counts
    - Tags with usage counts
    - Reading time ranges
    """
    loader = get_content_loader()
    categories_config = get_categories()

    # Build category facets
    category_facets = []
    articles = loader.get_all_articles()

    # Count articles per category
    category_counts: dict[str, int] = {}
    tag_counts: dict[str, int] = {}

    for article in articles:
        cat_id = article.get('category_id', '')
        category_counts[cat_id] = category_counts.get(cat_id, 0) + 1

        for tag in article.get('tags', []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Build category facet items
    for cat in categories_config.categories:
        count = category_counts.get(cat.id, 0)
        category_facets.append(FacetItem(
            id=cat.id,
            label=cat.name,
            count=count,
            icon=cat.icon,
            color=cat.color,
        ))

    # Build tag facet items (top 20)
    tag_facets = [
        FacetItem(id=tag, label=tag, count=count)
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:20]
    ]

    # Build reading time ranges
    reading_time_facets = [
        FacetItem(id="short", label="< 5 min", count=0),
        FacetItem(id="medium", label="5-15 min", count=0),
        FacetItem(id="long", label="15-30 min", count=0),
        FacetItem(id="very_long", label="> 30 min", count=0),
    ]

    for article in articles:
        reading_time = article.get('reading_time_minutes', 0)
        if reading_time < 5:
            reading_time_facets[0].count += 1
        elif reading_time < 15:
            reading_time_facets[1].count += 1
        elif reading_time < 30:
            reading_time_facets[2].count += 1
        else:
            reading_time_facets[3].count += 1

    return SearchFacets(
        categories=category_facets,
        tags=tag_facets,
        reading_time=reading_time_facets,
    )


@router.post(
    "/reindex",
    summary="Rebuild Search Index",
    description="Rebuild the search index from all articles.",
)
async def reindex():
    """
    Rebuild the search index from all articles.

    This should be called after adding or modifying articles.
    """
    loader = get_content_loader()
    indexer = get_indexer()

    # Force reload articles
    loader.load_all(force=True)

    # Get all articles
    articles = loader.get_all_articles()

    # Rebuild index
    count = indexer.build_index(articles)

    return {
        "status": "success",
        "articles_indexed": count,
    }


@router.get(
    "/stats",
    summary="Get Search Statistics",
    description="Get statistics about the search index.",
)
async def get_search_stats():
    """
    Get statistics about the search index.

    Returns document count, index path, and schema information.
    """
    indexer = get_indexer()
    return indexer.get_index_stats()
