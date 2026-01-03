"""
Categories Router
=================
API endpoints for category navigation.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Path

from ..models.category import (
    Category,
    CategorySummary,
    CategoryTree,
    CategoryListResponse,
)
from ..services.content_loader import get_content_loader

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get(
    "",
    response_model=list[CategorySummary],
    summary="List Categories",
    description="Get all categories with article counts.",
)
async def list_categories():
    """
    Get a list of all categories as summaries.

    Returns category metadata including:
    - ID, name, icon, color
    - Description
    - Article and subcategory counts
    """
    loader = get_content_loader()
    return loader.list_categories()


@router.get(
    "/tree",
    response_model=CategoryTree,
    summary="Get Category Tree",
    description="Get the complete category navigation tree.",
)
async def get_category_tree():
    """
    Get the complete navigation tree with all categories,
    subcategories, and articles.

    This endpoint returns the full hierarchical structure
    for rendering the navigation sidebar.
    """
    loader = get_content_loader()
    return loader.get_category_tree()


@router.get(
    "/{category_id}",
    response_model=Category,
    summary="Get Category",
    description="Get a single category with full details.",
)
async def get_category(
    category_id: str = Path(
        ...,
        description="Category ID (e.g., '01-theoretical-frontiers')"
    ),
):
    """
    Get a single category with all its subcategories and articles.

    The category ID matches the directory name in the articles folder.
    """
    loader = get_content_loader()
    category = loader.get_category(category_id)

    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Category not found: {category_id}"
        )

    return category


@router.get(
    "/{category_id}/articles",
    summary="Get Category Articles",
    description="Get all articles in a category.",
)
async def get_category_articles(
    category_id: str = Path(
        ...,
        description="Category ID"
    ),
):
    """
    Get all articles within a specific category.

    Returns article summaries organized by subcategory.
    """
    loader = get_content_loader()
    category = loader.get_category(category_id)

    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Category not found: {category_id}"
        )

    # Collect all articles from subcategories
    articles = []
    for sub in category.subcategories:
        for article in sub.articles:
            articles.append({
                "id": article.id,
                "title": article.title,
                "slug": article.slug,
                "subcategory": sub.slug,
                "subcategory_name": sub.name,
            })

    return {
        "category_id": category_id,
        "category_name": category.name,
        "article_count": len(articles),
        "articles": articles,
    }


@router.get(
    "/{category_id}/stats",
    summary="Get Category Statistics",
    description="Get statistics for a category.",
)
async def get_category_stats(
    category_id: str = Path(
        ...,
        description="Category ID"
    ),
):
    """
    Get statistics for a category including:
    - Total articles
    - Total word count
    - Total reading time
    - Subcategory breakdown
    """
    loader = get_content_loader()
    category = loader.get_category(category_id)

    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Category not found: {category_id}"
        )

    # Calculate stats
    total_articles = 0
    total_word_count = 0
    subcategory_stats = []

    for sub in category.subcategories:
        sub_articles = len(sub.articles)
        total_articles += sub_articles

        # Get detailed stats for each subcategory
        sub_word_count = 0
        for article in sub.articles:
            article_data = loader.get_article(article.id)
            if article_data:
                sub_word_count += article_data.word_count

        total_word_count += sub_word_count

        subcategory_stats.append({
            "slug": sub.slug,
            "name": sub.name,
            "article_count": sub_articles,
            "word_count": sub_word_count,
            "has_content": sub.has_content,
        })

    # Estimate reading time (200 wpm)
    total_reading_time = max(1, round(total_word_count / 200))

    return {
        "category_id": category_id,
        "category_name": category.name,
        "total_articles": total_articles,
        "total_subcategories": len(category.subcategories),
        "total_word_count": total_word_count,
        "total_reading_time_minutes": total_reading_time,
        "subcategories": subcategory_stats,
    }
