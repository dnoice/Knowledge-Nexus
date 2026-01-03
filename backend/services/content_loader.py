"""
Content Loader Service
======================
Loads and manages articles from the filesystem.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

import logging
import os
from pathlib import Path
from typing import Optional

from slugify import slugify

from ..config import get_settings, get_categories, CategoryConfig
from ..models.article import (
    Article,
    ArticleSummary,
    ArticleMetadata,
    ArticleContent,
    CompanionDocument,
    ArticleListResponse,
)
from ..models.category import (
    Category,
    CategorySummary,
    Subcategory,
    SubcategoryWithArticles,
    ArticleNavItem,
    CategoryTree,
)
from .parser import MarkdownParser, create_article_content
from .cache import get_cache

logger = logging.getLogger(__name__)


class ContentLoader:
    """
    Loads articles and builds navigation structures from the filesystem.

    Directory structure expected:
    articles/
        01-theoretical-frontiers/
            consciousness-hard-problem/
                consciousness_hard_problem.md
                consciousness_hard_problem_my_notes.md
                consciousness_hard_problem_works_cited.md
            ...
        02-materials-fabrication/
            ...
    """

    def __init__(self):
        self.settings = get_settings()
        self.categories_config = get_categories()
        self.parser = MarkdownParser()
        self.cache = get_cache()

        # Cached data
        self._articles: dict[str, dict] = {}
        self._articles_by_category: dict[str, list[str]] = {}
        self._category_tree: Optional[CategoryTree] = None
        self._loaded = False

    @property
    def articles_path(self) -> Path:
        """Get the articles directory path."""
        return self.settings.articles_path

    def load_all(self, force: bool = False) -> int:
        """
        Load all articles from the filesystem.

        Args:
            force: Force reload even if already loaded

        Returns:
            Number of articles loaded
        """
        if self._loaded and not force:
            return len(self._articles)

        logger.info(f"Loading articles from {self.articles_path}")

        self._articles.clear()
        self._articles_by_category.clear()

        count = 0

        # Iterate through category directories
        for category_dir in sorted(self.articles_path.iterdir()):
            if not category_dir.is_dir():
                continue

            category_id = category_dir.name

            # Get category config
            category_config = self.categories_config.get_category(category_id)
            if not category_config:
                logger.warning(f"Unknown category directory: {category_id}")
                continue

            self._articles_by_category[category_id] = []

            # Iterate through subcategory directories
            for subcategory_dir in sorted(category_dir.iterdir()):
                if not subcategory_dir.is_dir():
                    continue

                subcategory_slug = subcategory_dir.name

                # Find main article file
                article_files = list(subcategory_dir.glob("*.md"))
                main_file = self._find_main_article(article_files, subcategory_slug)

                if not main_file:
                    continue

                # Load article
                article = self._load_article(
                    main_file,
                    category_id,
                    category_config,
                    subcategory_slug,
                )

                if article:
                    self._articles[article['id']] = article
                    self._articles_by_category[category_id].append(article['id'])
                    count += 1

        self._loaded = True
        self._category_tree = None  # Invalidate tree cache

        logger.info(f"Loaded {count} articles from {len(self._articles_by_category)} categories")
        return count

    def _find_main_article(
        self,
        files: list[Path],
        subcategory_slug: str
    ) -> Optional[Path]:
        """Find the main article file (not notes or works_cited)."""
        # Filter out companion files
        candidates = [
            f for f in files
            if not f.stem.endswith('_my_notes')
            and not f.stem.endswith('_works_cited')
            and not f.stem.endswith('_notes')
            and not f.stem.endswith('_citations')
        ]

        if len(candidates) == 1:
            return candidates[0]

        if len(candidates) > 1:
            # Prefer file matching subcategory name
            expected_name = subcategory_slug.replace('-', '_')
            for f in candidates:
                if f.stem == expected_name:
                    return f
            # Fall back to first
            return candidates[0]

        return None

    def _load_article(
        self,
        file_path: Path,
        category_id: str,
        category_config: CategoryConfig,
        subcategory_slug: str,
    ) -> Optional[dict]:
        """Load a single article from file."""
        try:
            # Parse main article
            parsed = self.parser.parse_file(file_path)

            # Generate ID
            article_id = f"{category_id}/{subcategory_slug}"

            # Get subcategory name from config
            subcategory_name = subcategory_slug.replace('-', ' ').title()
            for sub in category_config.subcategories:
                if sub.slug == subcategory_slug:
                    subcategory_name = sub.name
                    break

            # Find companion files
            notes_file = self._find_companion_file(file_path, '_my_notes')
            citations_file = self._find_companion_file(file_path, '_works_cited')

            # Parse companions
            notes = self._load_companion(notes_file, 'notes')
            citations = self._load_companion(citations_file, 'citations')

            # Extract tags
            tags = self.parser.extract_tags(
                parsed['content'],
                parsed['metadata']
            )

            return {
                'id': article_id,
                'slug': subcategory_slug,
                'file_path': str(file_path),
                'category_id': category_id,
                'category_name': category_config.name,
                'category_icon': category_config.icon,
                'category_color': category_config.color,
                'subcategory': subcategory_slug,
                'subcategory_name': subcategory_name,
                'title': parsed['metadata'].title,
                'description': parsed['metadata'].description,
                'metadata': parsed['metadata'].model_dump(),
                'content': parsed['content'],
                'content_html': parsed['content_html'],
                'toc': [t.model_dump() for t in parsed['toc']],
                'word_count': parsed['word_count'],
                'reading_time_minutes': parsed['reading_time_minutes'],
                'key_features': parsed['metadata'].key_features,
                'tags': tags,
                'has_notes': notes is not None and notes.get('exists', False),
                'has_citations': citations is not None and citations.get('exists', False),
                'notes': notes,
                'citations': citations,
            }

        except Exception as e:
            logger.error(f"Error loading article {file_path}: {e}")
            return None

    def _find_companion_file(
        self,
        main_file: Path,
        suffix: str
    ) -> Optional[Path]:
        """Find a companion file (notes or works_cited)."""
        stem = main_file.stem
        parent = main_file.parent

        # Try common patterns
        patterns = [
            f"{stem}{suffix}.md",
            f"{stem.replace('_', '-')}{suffix.replace('_', '-')}.md",
        ]

        for pattern in patterns:
            companion = parent / pattern
            if companion.exists():
                return companion

        return None

    def _load_companion(
        self,
        file_path: Optional[Path],
        doc_type: str
    ) -> Optional[dict]:
        """Load a companion document."""
        if not file_path or not file_path.exists():
            return {'type': doc_type, 'exists': False}

        try:
            parsed = self.parser.parse_file(file_path)

            return {
                'type': doc_type,
                'exists': True,
                'file_path': str(file_path),
                'content': parsed['content'],
                'content_html': parsed['content_html'],
                'word_count': parsed['word_count'],
            }

        except Exception as e:
            logger.error(f"Error loading companion {file_path}: {e}")
            return {'type': doc_type, 'exists': False}

    # =========================================================================
    # Article retrieval methods
    # =========================================================================

    def get_article(self, article_id: str) -> Optional[Article]:
        """Get a single article by ID."""
        self.load_all()

        data = self._articles.get(article_id)
        if not data:
            return None

        return self._to_article_model(data)

    def get_article_summary(self, article_id: str) -> Optional[ArticleSummary]:
        """Get article summary by ID."""
        self.load_all()

        data = self._articles.get(article_id)
        if not data:
            return None

        return self._to_summary_model(data)

    def list_articles(
        self,
        category_id: Optional[str] = None,
        subcategory: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> ArticleListResponse:
        """List articles with optional filtering and pagination."""
        self.load_all()

        # Filter articles
        articles = list(self._articles.values())

        if category_id:
            articles = [a for a in articles if a['category_id'] == category_id]

        if subcategory:
            articles = [a for a in articles if a['subcategory'] == subcategory]

        # Sort by category and subcategory
        articles.sort(key=lambda a: (a['category_id'], a['subcategory']))

        # Paginate
        total = len(articles)
        start = (page - 1) * per_page
        end = start + per_page
        page_articles = articles[start:end]

        return ArticleListResponse(
            articles=[self._to_summary_model(a) for a in page_articles],
            total=total,
            page=page,
            per_page=per_page,
            has_more=end < total,
        )

    def get_all_articles(self) -> list[dict]:
        """Get all articles as dictionaries (for indexing)."""
        self.load_all()
        return list(self._articles.values())

    # =========================================================================
    # Category methods
    # =========================================================================

    def get_category_tree(self) -> CategoryTree:
        """Build the complete category navigation tree."""
        self.load_all()

        if self._category_tree:
            return self._category_tree

        categories = []

        for cat_config in self.categories_config.categories:
            # Build subcategories with articles
            subcategories = []

            for sub_config in cat_config.subcategories:
                # Find articles for this subcategory
                article_ids = [
                    a_id for a_id in self._articles_by_category.get(cat_config.id, [])
                    if self._articles[a_id]['subcategory'] == sub_config.slug
                ]

                articles = [
                    ArticleNavItem(
                        id=self._articles[a_id]['id'],
                        title=self._articles[a_id]['title'],
                        slug=self._articles[a_id]['slug'],
                    )
                    for a_id in article_ids
                ]

                subcategories.append(SubcategoryWithArticles(
                    id=f"{cat_config.id}/{sub_config.slug}",
                    slug=sub_config.slug,
                    name=sub_config.name,
                    category_id=cat_config.id,
                    article_count=len(articles),
                    has_content=len(articles) > 0,
                    articles=articles,
                ))

            categories.append(Category(
                id=cat_config.id,
                name=cat_config.name,
                short_name=cat_config.short_name,
                icon=cat_config.icon,
                color=cat_config.color,
                description=cat_config.description,
                order=cat_config.order,
                subcategories=subcategories,
            ))

        self._category_tree = CategoryTree.from_categories(categories)
        return self._category_tree

    def get_category(self, category_id: str) -> Optional[Category]:
        """Get a single category with full details."""
        tree = self.get_category_tree()

        for cat in tree.categories:
            if cat.id == category_id:
                return cat

        return None

    def list_categories(self) -> list[CategorySummary]:
        """List all categories as summaries."""
        tree = self.get_category_tree()
        return [cat.to_summary() for cat in tree.categories]

    # =========================================================================
    # Related articles
    # =========================================================================

    def get_related_articles(
        self,
        article_id: str,
        limit: int = 5
    ) -> list[ArticleSummary]:
        """Get articles related to the given article."""
        self.load_all()

        article = self._articles.get(article_id)
        if not article:
            return []

        related = []
        article_tags = set(article.get('tags', []))

        # Find articles with shared tags
        for other_id, other in self._articles.items():
            if other_id == article_id:
                continue

            other_tags = set(other.get('tags', []))
            shared = article_tags & other_tags

            if shared:
                related.append((other, len(shared)))

        # Sort by number of shared tags
        related.sort(key=lambda x: -x[1])

        # Take top N
        return [
            self._to_summary_model(a)
            for a, _ in related[:limit]
        ]

    # =========================================================================
    # Model conversion helpers
    # =========================================================================

    def _to_article_model(self, data: dict) -> Article:
        """Convert dict to Article model."""
        from ..models.article import TableOfContentsEntry

        # Rebuild TOC entries
        toc_entries = [
            TableOfContentsEntry(**t) for t in data.get('toc', [])
        ]

        # Rebuild metadata
        metadata = ArticleMetadata(**data['metadata'])

        # Rebuild content
        content = ArticleContent(
            raw=data['content'],
            html=data['content_html'],
            toc=toc_entries,
            word_count=data['word_count'],
            reading_time_minutes=data['reading_time_minutes'],
        )

        # Rebuild companions
        notes = None
        if data.get('notes'):
            notes = CompanionDocument(**data['notes'])

        citations = None
        if data.get('citations'):
            citations = CompanionDocument(**data['citations'])

        # Get related
        related = self.get_related_articles(data['id'], limit=5)

        return Article(
            id=data['id'],
            slug=data['slug'],
            category_id=data['category_id'],
            category_name=data['category_name'],
            category_icon=data['category_icon'],
            category_color=data['category_color'],
            subcategory=data['subcategory'],
            subcategory_name=data['subcategory_name'],
            metadata=metadata,
            content=content,
            notes=notes,
            citations=citations,
            related_articles=related,
            tags=data.get('tags', []),
        )

    def _to_summary_model(self, data: dict) -> ArticleSummary:
        """Convert dict to ArticleSummary model."""
        return ArticleSummary(
            id=data['id'],
            slug=data['slug'],
            title=data['title'],
            description=data.get('description', ''),
            category_id=data['category_id'],
            category_name=data['category_name'],
            subcategory=data['subcategory'],
            subcategory_name=data['subcategory_name'],
            word_count=data['word_count'],
            reading_time_minutes=data['reading_time_minutes'],
            has_notes=data.get('has_notes', False),
            has_citations=data.get('has_citations', False),
            tags=data.get('tags', []),
            version=data.get('metadata', {}).get('version', '1.0.0'),
            last_updated=data.get('metadata', {}).get('update'),
        )


# Global content loader instance
_loader: Optional[ContentLoader] = None


def get_content_loader() -> ContentLoader:
    """Get the global content loader instance."""
    global _loader
    if _loader is None:
        _loader = ContentLoader()
    return _loader
