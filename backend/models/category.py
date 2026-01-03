"""
Category Models
===============
Data models for categories and navigation structure.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, computed_field


class Subcategory(BaseModel):
    """Subcategory within a main category."""
    id: str = Field(..., description="Unique subcategory identifier")
    slug: str = Field(..., description="URL-friendly slug")
    name: str = Field(..., description="Display name")
    category_id: str = Field(..., description="Parent category ID")
    article_count: int = Field(default=0, description="Number of articles")
    has_content: bool = Field(default=False, description="Has any articles")

    @computed_field
    @property
    def path(self) -> str:
        """Navigation path."""
        return f"/category/{self.category_id}/{self.slug}"


class CategorySummary(BaseModel):
    """Lightweight category representation for listings."""
    id: str = Field(..., description="Unique category identifier")
    name: str = Field(..., description="Display name")
    short_name: str = Field(default="", description="Abbreviated name")
    icon: str = Field(default="folder", description="Icon identifier")
    color: str = Field(default="#8b4513", description="Theme color (hex)")
    description: str = Field(default="", description="Brief description")
    order: int = Field(default=0, description="Display order")
    article_count: int = Field(default=0, description="Total articles in category")
    subcategory_count: int = Field(default=0, description="Number of subcategories")

    @computed_field
    @property
    def path(self) -> str:
        """Navigation path."""
        return f"/category/{self.id}"


class SubcategoryWithArticles(Subcategory):
    """Subcategory with article list for navigation tree."""
    articles: list["ArticleNavItem"] = Field(
        default_factory=list,
        description="Articles in this subcategory"
    )


class ArticleNavItem(BaseModel):
    """Minimal article representation for navigation."""
    id: str = Field(..., description="Article identifier")
    title: str = Field(..., description="Article title")
    slug: str = Field(..., description="URL slug")

    @computed_field
    @property
    def path(self) -> str:
        """Navigation path."""
        return f"/article/{self.id}"


class Category(BaseModel):
    """Complete category with subcategories."""
    id: str = Field(..., description="Unique category identifier")
    name: str = Field(..., description="Display name")
    short_name: str = Field(default="", description="Abbreviated name")
    icon: str = Field(default="folder", description="Icon identifier")
    color: str = Field(default="#8b4513", description="Theme color (hex)")
    description: str = Field(default="", description="Brief description")
    order: int = Field(default=0, description="Display order")
    subcategories: list[SubcategoryWithArticles] = Field(
        default_factory=list,
        description="Subcategories with articles"
    )

    @computed_field
    @property
    def article_count(self) -> int:
        """Total articles across all subcategories."""
        return sum(sub.article_count for sub in self.subcategories)

    @computed_field
    @property
    def subcategory_count(self) -> int:
        """Number of subcategories."""
        return len(self.subcategories)

    @computed_field
    @property
    def has_content(self) -> bool:
        """Has any articles."""
        return self.article_count > 0

    @computed_field
    @property
    def path(self) -> str:
        """Navigation path."""
        return f"/category/{self.id}"

    def to_summary(self) -> CategorySummary:
        """Convert to summary representation."""
        return CategorySummary(
            id=self.id,
            name=self.name,
            short_name=self.short_name,
            icon=self.icon,
            color=self.color,
            description=self.description,
            order=self.order,
            article_count=self.article_count,
            subcategory_count=self.subcategory_count,
        )


class CategoryTree(BaseModel):
    """Complete category tree for navigation."""
    categories: list[Category] = Field(
        default_factory=list,
        description="All categories with nested structure"
    )
    total_categories: int = Field(default=0, description="Total category count")
    total_subcategories: int = Field(default=0, description="Total subcategory count")
    total_articles: int = Field(default=0, description="Total article count")

    @classmethod
    def from_categories(cls, categories: list[Category]) -> "CategoryTree":
        """Build tree from category list."""
        total_subcategories = sum(len(cat.subcategories) for cat in categories)
        total_articles = sum(cat.article_count for cat in categories)

        return cls(
            categories=sorted(categories, key=lambda c: c.order),
            total_categories=len(categories),
            total_subcategories=total_subcategories,
            total_articles=total_articles,
        )


class CategoryListResponse(BaseModel):
    """Response for category listing endpoint."""
    categories: list[CategorySummary] = Field(
        ...,
        description="List of category summaries"
    )
    total: int = Field(..., description="Total categories")


# Update forward references
SubcategoryWithArticles.model_rebuild()
