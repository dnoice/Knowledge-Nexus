"""
Data Models
===========
Pydantic models for articles, categories, search results, and graph data.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

from .article import (
    ArticleMetadata,
    Article,
    ArticleSummary,
    ArticleContent,
    CompanionDocument,
    TableOfContentsEntry,
)
from .category import (
    Category,
    CategorySummary,
    Subcategory,
    CategoryTree,
)
from .graph import (
    GraphNode,
    GraphEdge,
    KnowledgeGraph,
    GraphNeighborhood,
)
from .search import (
    SearchQuery,
    SearchResult,
    SearchResponse,
    SearchSuggestion,
    SearchFacets,
    FacetItem,
)

__all__ = [
    # Article models
    "ArticleMetadata",
    "Article",
    "ArticleSummary",
    "ArticleContent",
    "CompanionDocument",
    "TableOfContentsEntry",
    # Category models
    "Category",
    "CategorySummary",
    "Subcategory",
    "CategoryTree",
    # Graph models
    "GraphNode",
    "GraphEdge",
    "KnowledgeGraph",
    "GraphNeighborhood",
    # Search models
    "SearchQuery",
    "SearchResult",
    "SearchResponse",
    "SearchSuggestion",
    "SearchFacets",
    "FacetItem",
]
