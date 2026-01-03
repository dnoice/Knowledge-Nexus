"""
Article Models
==============
Data models for articles and their metadata.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

from __future__ import annotations
import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, computed_field, ConfigDict


class TableOfContentsEntry(BaseModel):
    """A single entry in the table of contents."""
    level: int = Field(..., ge=1, le=6, description="Heading level (1-6)")
    title: str = Field(..., description="Heading text")
    slug: str = Field(..., description="URL-friendly anchor ID")
    children: list["TableOfContentsEntry"] = Field(
        default_factory=list,
        description="Nested headings"
    )


class ArticleMetadata(BaseModel):
    """
    Metadata extracted from the article's docstring header.
    Maps to the standard Knowledge Nexus docstring format.
    """
    model_config = ConfigDict(
        json_encoders={datetime.date: lambda v: v.isoformat() if v else None}
    )

    title: str = Field(..., description="Article title")
    file_name: str = Field(..., description="Original filename")
    relative_path: str = Field(default="", description="Path relative to articles directory")
    artifact_type: str = Field(default="docs", description="Type of artifact")
    version: str = Field(default="1.0.0", description="Document version")
    date: Optional[datetime.date] = Field(default=None, description="Creation date")
    update: Optional[str] = Field(default=None, description="Last update timestamp")
    author: str = Field(default="Dennis 'dnoice' Smaltz", description="Author name")
    ai_acknowledgement: str = Field(
        default="Anthropic - Claude Opus 4.5",
        description="AI assistance acknowledgement"
    )
    signature: str = Field(
        default="Aim Twice, Shoot Once!",
        description="Author signature"
    )
    description: str = Field(default="", description="Brief description")
    key_features: list[str] = Field(
        default_factory=list,
        description="List of key features/highlights"
    )
    usage_instructions: str = Field(default="", description="How to use this document")
    other_info: str = Field(default="", description="Additional information")


class CompanionDocument(BaseModel):
    """Companion document (notes or works cited)."""
    type: str = Field(..., description="Type: 'notes' or 'citations'")
    exists: bool = Field(..., description="Whether the file exists")
    file_path: Optional[str] = Field(default=None, description="Path to the file")
    content: Optional[str] = Field(default=None, description="Raw markdown content")
    content_html: Optional[str] = Field(default=None, description="Rendered HTML")
    word_count: int = Field(default=0, description="Word count")


class ArticleSummary(BaseModel):
    """
    Lightweight article representation for listings.
    Used in search results, navigation, and category views.
    """
    id: str = Field(..., description="Unique article identifier (slug)")
    slug: str = Field(..., description="URL-friendly identifier")
    title: str = Field(..., description="Article title")
    description: str = Field(default="", description="Brief description")
    category_id: str = Field(..., description="Parent category ID")
    category_name: str = Field(default="", description="Parent category name")
    subcategory: str = Field(..., description="Subcategory slug")
    subcategory_name: str = Field(default="", description="Subcategory display name")
    word_count: int = Field(default=0, description="Total word count")
    reading_time_minutes: int = Field(default=1, description="Estimated reading time")
    has_notes: bool = Field(default=False, description="Has companion notes")
    has_citations: bool = Field(default=False, description="Has works cited")
    tags: list[str] = Field(default_factory=list, description="Extracted tags")
    version: str = Field(default="1.0.0", description="Document version")
    last_updated: Optional[str] = Field(default=None, description="Last update")

    @computed_field
    @property
    def path(self) -> str:
        """Full path for navigation."""
        return f"/article/{self.id}"


class ArticleContent(BaseModel):
    """Article content container."""
    raw: str = Field(..., description="Raw markdown content")
    html: str = Field(..., description="Rendered HTML content")
    toc: list[TableOfContentsEntry] = Field(
        default_factory=list,
        description="Table of contents"
    )
    word_count: int = Field(default=0, description="Word count")
    reading_time_minutes: int = Field(default=1, description="Estimated reading time")


class Article(BaseModel):
    """
    Complete article representation with full content.
    Used when viewing a single article.
    """
    model_config = ConfigDict(
        json_encoders={datetime.date: lambda v: v.isoformat() if v else None}
    )

    id: str = Field(..., description="Unique article identifier")
    slug: str = Field(..., description="URL-friendly identifier")
    category_id: str = Field(..., description="Parent category ID")
    category_name: str = Field(default="", description="Category display name")
    category_icon: str = Field(default="folder", description="Category icon name")
    category_color: str = Field(default="#8b4513", description="Category theme color")
    subcategory: str = Field(..., description="Subcategory slug")
    subcategory_name: str = Field(default="", description="Subcategory display name")

    # Metadata from docstring
    metadata: ArticleMetadata = Field(..., description="Extracted metadata")

    # Content
    content: ArticleContent = Field(..., description="Article content")

    # Companion documents
    notes: Optional[CompanionDocument] = Field(default=None, description="Personal notes")
    citations: Optional[CompanionDocument] = Field(default=None, description="Works cited")

    # Relationships
    related_articles: list[ArticleSummary] = Field(
        default_factory=list,
        description="Related articles"
    )
    tags: list[str] = Field(default_factory=list, description="Extracted tags")

    # Navigation
    prev_article: Optional[ArticleSummary] = Field(
        default=None,
        description="Previous article in category"
    )
    next_article: Optional[ArticleSummary] = Field(
        default=None,
        description="Next article in category"
    )

    @computed_field
    @property
    def word_count(self) -> int:
        """Total word count including companions."""
        total = self.content.word_count
        if self.notes and self.notes.word_count:
            total += self.notes.word_count
        if self.citations and self.citations.word_count:
            total += self.citations.word_count
        return total

    @computed_field
    @property
    def reading_time_minutes(self) -> int:
        """Estimated reading time for main content."""
        return self.content.reading_time_minutes

    @computed_field
    @property
    def has_notes(self) -> bool:
        """Check if notes exist."""
        return self.notes is not None and self.notes.exists

    @computed_field
    @property
    def has_citations(self) -> bool:
        """Check if citations exist."""
        return self.citations is not None and self.citations.exists


class ArticleListResponse(BaseModel):
    """Response for article listing endpoints."""
    articles: list[ArticleSummary] = Field(..., description="List of articles")
    total: int = Field(..., description="Total number of articles")
    page: int = Field(default=1, description="Current page")
    per_page: int = Field(default=20, description="Items per page")
    has_more: bool = Field(default=False, description="More pages available")

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total pages."""
        if self.per_page <= 0:
            return 1
        return (self.total + self.per_page - 1) // self.per_page
