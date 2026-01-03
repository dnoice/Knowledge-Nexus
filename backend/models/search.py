"""
Search Models
=============
Data models for search queries, results, and facets.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, computed_field


class SearchQuery(BaseModel):
    """Search query parameters."""
    q: str = Field(..., min_length=1, description="Search query string")
    categories: list[str] = Field(
        default_factory=list,
        description="Filter by category IDs"
    )
    subcategories: list[str] = Field(
        default_factory=list,
        description="Filter by subcategory slugs"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Filter by tags"
    )
    fuzzy: bool = Field(default=True, description="Enable fuzzy matching")
    highlight: bool = Field(default=True, description="Include highlights in results")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Results per page")

    @computed_field
    @property
    def offset(self) -> int:
        """Calculate offset for pagination."""
        return (self.page - 1) * self.per_page

    @computed_field
    @property
    def has_filters(self) -> bool:
        """Check if any filters are applied."""
        return bool(self.categories or self.subcategories or self.tags)


class SearchHighlight(BaseModel):
    """Search result highlight/snippet."""
    field: str = Field(..., description="Field containing match")
    text: str = Field(..., description="Highlighted text snippet")
    score: float = Field(default=0.0, description="Match relevance score")


class SearchResult(BaseModel):
    """A single search result."""
    id: str = Field(..., description="Article ID")
    title: str = Field(..., description="Article title")
    description: str = Field(default="", description="Article description")
    category_id: str = Field(..., description="Category ID")
    category_name: str = Field(default="", description="Category name")
    category_icon: str = Field(default="folder", description="Category icon")
    subcategory: str = Field(default="", description="Subcategory slug")
    subcategory_name: str = Field(default="", description="Subcategory name")
    score: float = Field(default=0.0, description="Relevance score")
    highlights: list[SearchHighlight] = Field(
        default_factory=list,
        description="Match highlights"
    )
    tags: list[str] = Field(default_factory=list, description="Article tags")
    word_count: int = Field(default=0, description="Article word count")
    reading_time: int = Field(default=1, description="Reading time in minutes")

    @computed_field
    @property
    def path(self) -> str:
        """Article path."""
        return f"/article/{self.id}"

    @computed_field
    @property
    def primary_highlight(self) -> Optional[str]:
        """Get the best highlight text."""
        if self.highlights:
            return self.highlights[0].text
        return None


class FacetItem(BaseModel):
    """A single facet option with count."""
    id: str = Field(..., description="Facet item ID")
    label: str = Field(..., description="Display label")
    count: int = Field(default=0, description="Number of matching results")
    icon: Optional[str] = Field(default=None, description="Optional icon")
    color: Optional[str] = Field(default=None, description="Optional color")
    selected: bool = Field(default=False, description="Currently selected")


class SearchFacets(BaseModel):
    """Available search facets with counts."""
    categories: list[FacetItem] = Field(
        default_factory=list,
        description="Category facets"
    )
    subcategories: list[FacetItem] = Field(
        default_factory=list,
        description="Subcategory facets"
    )
    tags: list[FacetItem] = Field(
        default_factory=list,
        description="Tag facets"
    )
    reading_time: list[FacetItem] = Field(
        default_factory=list,
        description="Reading time ranges"
    )


class SearchResponse(BaseModel):
    """Complete search response."""
    query: str = Field(..., description="Original query string")
    results: list[SearchResult] = Field(
        default_factory=list,
        description="Search results"
    )
    total: int = Field(default=0, description="Total matching results")
    page: int = Field(default=1, description="Current page")
    per_page: int = Field(default=20, description="Results per page")
    facets: Optional[SearchFacets] = Field(
        default=None,
        description="Available facets"
    )
    search_time_ms: float = Field(default=0.0, description="Search execution time")

    @computed_field
    @property
    def total_pages(self) -> int:
        """Total number of pages."""
        if self.per_page <= 0:
            return 1
        return (self.total + self.per_page - 1) // self.per_page

    @computed_field
    @property
    def has_more(self) -> bool:
        """Check if more pages exist."""
        return self.page < self.total_pages

    @computed_field
    @property
    def has_results(self) -> bool:
        """Check if any results found."""
        return len(self.results) > 0

    @computed_field
    @property
    def showing_start(self) -> int:
        """First result number being shown."""
        if not self.results:
            return 0
        return (self.page - 1) * self.per_page + 1

    @computed_field
    @property
    def showing_end(self) -> int:
        """Last result number being shown."""
        if not self.results:
            return 0
        return min(self.page * self.per_page, self.total)


class SearchSuggestion(BaseModel):
    """Autocomplete suggestion."""
    id: str = Field(..., description="Article or category ID")
    type: Literal["article", "category", "tag"] = Field(
        ...,
        description="Suggestion type"
    )
    title: str = Field(..., description="Display title")
    subtitle: Optional[str] = Field(default=None, description="Secondary text")
    icon: str = Field(default="file-text", description="Icon identifier")
    category: Optional[str] = Field(default=None, description="Category name")
    score: float = Field(default=0.0, description="Relevance score")

    @computed_field
    @property
    def path(self) -> str:
        """Navigation path."""
        if self.type == "article":
            return f"/article/{self.id}"
        elif self.type == "category":
            return f"/category/{self.id}"
        else:
            return f"/search?tags={self.id}"


class SuggestResponse(BaseModel):
    """Autocomplete suggestions response."""
    query: str = Field(..., description="Original query")
    suggestions: list[SearchSuggestion] = Field(
        default_factory=list,
        description="Suggested completions"
    )
    search_time_ms: float = Field(default=0.0, description="Suggestion generation time")
