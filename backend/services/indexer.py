"""
Search Indexer Service
======================
Builds and queries the full-text search index using Whoosh.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional

from whoosh import index
from whoosh.fields import Schema, TEXT, ID, KEYWORD, STORED, NUMERIC
from whoosh.analysis import StemmingAnalyzer, StandardAnalyzer
from whoosh.qparser import MultifieldParser, QueryParser, FuzzyTermPlugin
from whoosh.query import And, Or, Term
from whoosh.writing import AsyncWriter
from whoosh.highlight import ContextFragmenter, HtmlFormatter

from ..config import get_settings
from ..models.search import (
    SearchQuery,
    SearchResult,
    SearchResponse,
    SearchHighlight,
    SearchSuggestion,
    SuggestResponse,
    SearchFacets,
    FacetItem,
)

logger = logging.getLogger(__name__)


class SearchIndexer:
    """
    Full-text search engine using Whoosh.
    Handles index creation, updates, and querying.
    """

    def __init__(self, index_path: Optional[Path] = None):
        self.settings = get_settings()

        if index_path:
            self.index_path = index_path
        else:
            self.index_path = self.settings.data_path / "search_index"

        self.schema = self._create_schema()
        self._index: Optional[index.Index] = None

    def _create_schema(self) -> Schema:
        """Create the search index schema."""
        stemming = StemmingAnalyzer()
        standard = StandardAnalyzer()

        return Schema(
            # Identifiers
            id=ID(stored=True, unique=True),
            slug=ID(stored=True),

            # Searchable text fields with boosting support
            title=TEXT(stored=True, analyzer=stemming, field_boost=3.0),
            description=TEXT(stored=True, analyzer=stemming, field_boost=2.0),
            content=TEXT(analyzer=stemming),
            features=TEXT(stored=True, analyzer=stemming, field_boost=1.5),

            # Facets
            category_id=ID(stored=True),
            category_name=STORED,
            category_icon=STORED,
            subcategory=ID(stored=True),
            subcategory_name=STORED,
            tags=KEYWORD(stored=True, lowercase=True, commas=True),

            # Metadata
            word_count=NUMERIC(stored=True),
            reading_time=NUMERIC(stored=True),
            has_notes=STORED,
            has_citations=STORED,
        )

    @property
    def ix(self) -> index.Index:
        """Get or create the index."""
        if self._index is None:
            self._index = self._open_or_create_index()
        return self._index

    def _open_or_create_index(self) -> index.Index:
        """Open existing index or create new one."""
        self.index_path.mkdir(parents=True, exist_ok=True)

        if index.exists_in(str(self.index_path)):
            logger.info(f"Opening existing index at {self.index_path}")
            return index.open_dir(str(self.index_path))
        else:
            logger.info(f"Creating new index at {self.index_path}")
            return index.create_in(str(self.index_path), self.schema)

    def build_index(self, articles: list[dict]) -> int:
        """
        Build the search index from scratch.

        Args:
            articles: List of article dictionaries with required fields

        Returns:
            Number of articles indexed
        """
        logger.info(f"Building search index with {len(articles)} articles")
        start_time = time.time()

        # Clear and recreate index
        if self.index_path.exists():
            import shutil
            shutil.rmtree(self.index_path)

        self.index_path.mkdir(parents=True, exist_ok=True)
        self._index = index.create_in(str(self.index_path), self.schema)

        writer = self.ix.writer()

        try:
            for article in articles:
                self._add_document(writer, article)

            writer.commit()
            elapsed = time.time() - start_time
            logger.info(f"Indexed {len(articles)} articles in {elapsed:.2f}s")

            return len(articles)

        except Exception as e:
            writer.cancel()
            logger.error(f"Error building index: {e}")
            raise

    def update_article(self, article: dict) -> None:
        """Update a single article in the index."""
        writer = AsyncWriter(self.ix)

        try:
            self._add_document(writer, article, update=True)
            writer.commit()
            logger.debug(f"Updated article in index: {article.get('id')}")

        except Exception as e:
            writer.cancel()
            logger.error(f"Error updating article: {e}")
            raise

    def delete_article(self, article_id: str) -> None:
        """Remove an article from the index."""
        writer = self.ix.writer()

        try:
            writer.delete_by_term('id', article_id)
            writer.commit()
            logger.debug(f"Deleted article from index: {article_id}")

        except Exception as e:
            writer.cancel()
            logger.error(f"Error deleting article: {e}")
            raise

    def _add_document(
        self,
        writer,
        article: dict,
        update: bool = False
    ) -> None:
        """Add or update a document in the index."""
        doc = {
            'id': article['id'],
            'slug': article.get('slug', article['id']),
            'title': article.get('title', ''),
            'description': article.get('description', ''),
            'content': article.get('content', ''),
            'features': '\n'.join(article.get('key_features', [])),
            'category_id': article.get('category_id', ''),
            'category_name': article.get('category_name', ''),
            'category_icon': article.get('category_icon', 'folder'),
            'subcategory': article.get('subcategory', ''),
            'subcategory_name': article.get('subcategory_name', ''),
            'tags': ','.join(article.get('tags', [])),
            'word_count': article.get('word_count', 0),
            'reading_time': article.get('reading_time_minutes', 1),
            'has_notes': article.get('has_notes', False),
            'has_citations': article.get('has_citations', False),
        }

        if update:
            writer.update_document(**doc)
        else:
            writer.add_document(**doc)

    def search(self, query: SearchQuery) -> SearchResponse:
        """
        Execute a search query.

        Args:
            query: SearchQuery with search parameters

        Returns:
            SearchResponse with results and metadata
        """
        start_time = time.time()

        with self.ix.searcher() as searcher:
            # Build query parser
            parser = MultifieldParser(
                ['title', 'description', 'content', 'features', 'tags'],
                schema=self.schema
            )

            if query.fuzzy:
                parser.add_plugin(FuzzyTermPlugin())

            # Parse query string
            try:
                q = parser.parse(query.q)
            except Exception as e:
                logger.warning(f"Query parse error: {e}")
                # Fall back to simple term query
                q = Term('content', query.q.lower())

            # Add filters
            filter_query = None
            if query.categories:
                cat_query = Or([Term('category_id', cat) for cat in query.categories])
                filter_query = cat_query

            if query.subcategories:
                sub_query = Or([Term('subcategory', sub) for sub in query.subcategories])
                if filter_query:
                    filter_query = And([filter_query, sub_query])
                else:
                    filter_query = sub_query

            # Execute search
            if filter_query:
                results = searcher.search(
                    q,
                    filter=filter_query,
                    limit=query.per_page + query.offset
                )
            else:
                results = searcher.search(
                    q,
                    limit=query.per_page + query.offset
                )

            # Get total count
            total = len(results)

            # Apply pagination
            start = query.offset
            end = start + query.per_page
            page_results = list(results)[start:end]

            # Build response
            search_results = []
            for hit in page_results:
                highlights = []

                if query.highlight:
                    # Get content highlights
                    try:
                        content_hl = hit.highlights(
                            'content',
                            top=self.settings.search.highlight_fragments
                        )
                        if content_hl:
                            highlights.append(SearchHighlight(
                                field='content',
                                text=content_hl,
                                score=hit.score
                            ))
                    except Exception:
                        pass

                    # Get description highlights
                    try:
                        desc_hl = hit.highlights('description')
                        if desc_hl:
                            highlights.append(SearchHighlight(
                                field='description',
                                text=desc_hl,
                                score=hit.score
                            ))
                    except Exception:
                        pass

                search_results.append(SearchResult(
                    id=hit['id'],
                    title=hit['title'],
                    description=hit.get('description', ''),
                    category_id=hit.get('category_id', ''),
                    category_name=hit.get('category_name', ''),
                    category_icon=hit.get('category_icon', 'folder'),
                    subcategory=hit.get('subcategory', ''),
                    subcategory_name=hit.get('subcategory_name', ''),
                    score=hit.score,
                    highlights=highlights,
                    tags=hit.get('tags', '').split(',') if hit.get('tags') else [],
                    word_count=hit.get('word_count', 0),
                    reading_time=hit.get('reading_time', 1),
                ))

            # Calculate facets
            facets = self._calculate_facets(searcher, q)

            elapsed_ms = (time.time() - start_time) * 1000

            return SearchResponse(
                query=query.q,
                results=search_results,
                total=total,
                page=query.page,
                per_page=query.per_page,
                facets=facets,
                search_time_ms=round(elapsed_ms, 2),
            )

    def suggest(self, query: str, limit: int = 8) -> SuggestResponse:
        """
        Get autocomplete suggestions.

        Args:
            query: Partial search query
            limit: Maximum suggestions to return

        Returns:
            SuggestResponse with suggestions
        """
        start_time = time.time()

        with self.ix.searcher() as searcher:
            suggestions = []

            # Search titles with prefix matching
            parser = QueryParser('title', self.schema)

            try:
                # Use wildcard for prefix matching
                q = parser.parse(f"{query}*")
                results = searcher.search(q, limit=limit * 2)

                for hit in results[:limit]:
                    suggestions.append(SearchSuggestion(
                        id=hit['id'],
                        type='article',
                        title=hit['title'],
                        subtitle=hit.get('category_name', ''),
                        icon='file-text',
                        category=hit.get('category_name'),
                        score=hit.score,
                    ))

            except Exception as e:
                logger.warning(f"Suggestion query error: {e}")

            elapsed_ms = (time.time() - start_time) * 1000

            return SuggestResponse(
                query=query,
                suggestions=suggestions,
                search_time_ms=round(elapsed_ms, 2),
            )

    def _calculate_facets(self, searcher, query) -> SearchFacets:
        """Calculate facet counts for the current query."""
        categories: dict[str, int] = {}
        tags: dict[str, int] = {}

        try:
            results = searcher.search(query, limit=None)

            for hit in results:
                # Count categories
                cat_id = hit.get('category_id')
                if cat_id:
                    categories[cat_id] = categories.get(cat_id, 0) + 1

                # Count tags
                hit_tags = hit.get('tags', '').split(',')
                for tag in hit_tags:
                    tag = tag.strip()
                    if tag:
                        tags[tag] = tags.get(tag, 0) + 1

        except Exception as e:
            logger.warning(f"Facet calculation error: {e}")

        # Convert to FacetItems
        category_facets = [
            FacetItem(id=k, label=k, count=v)
            for k, v in sorted(categories.items(), key=lambda x: -x[1])
        ]

        tag_facets = [
            FacetItem(id=k, label=k, count=v)
            for k, v in sorted(tags.items(), key=lambda x: -x[1])[:20]
        ]

        return SearchFacets(
            categories=category_facets,
            tags=tag_facets,
        )

    def get_index_stats(self) -> dict:
        """Get statistics about the search index."""
        with self.ix.searcher() as searcher:
            return {
                'doc_count': searcher.doc_count(),
                'index_path': str(self.index_path),
                'schema_fields': list(self.schema.names()),
            }
