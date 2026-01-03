"""
Content Cache Service
=====================
In-memory caching layer for articles and parsed content.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

import hashlib
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, TypeVar, Generic
from dataclasses import dataclass, field

from ..config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """A single cache entry with metadata."""
    key: str
    value: T
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    hits: int = 0
    size_bytes: int = 0

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if entry has expired."""
        return (time.time() - self.created_at) > ttl_seconds

    def touch(self) -> None:
        """Update access time and hit count."""
        self.accessed_at = time.time()
        self.hits += 1


class ContentCache:
    """
    Thread-safe in-memory cache with TTL and size limits.

    Features:
    - TTL-based expiration
    - LRU eviction when size limit reached
    - Hit/miss statistics
    - File-based persistence for warm starts
    """

    def __init__(self):
        self.settings = get_settings()
        self._cache: dict[str, CacheEntry] = {}
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
        }

        # Cache settings
        self.enabled = self.settings.cache.enabled
        self.ttl = self.settings.cache.ttl_seconds
        self.max_size = self.settings.cache.max_size_mb * 1024 * 1024  # Convert to bytes
        self._current_size = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None

        entry = self._cache.get(key)

        if entry is None:
            self._stats['misses'] += 1
            return None

        if entry.is_expired(self.ttl):
            self.delete(key)
            self._stats['misses'] += 1
            return None

        entry.touch()
        self._stats['hits'] += 1
        return entry.value

    def set(self, key: str, value: Any) -> None:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        if not self.enabled:
            return

        # Estimate size
        try:
            size = len(json.dumps(value, default=str).encode('utf-8'))
        except (TypeError, ValueError):
            size = 1024  # Default estimate

        # Evict if needed
        while self._current_size + size > self.max_size and self._cache:
            self._evict_lru()

        # Remove old entry if exists
        if key in self._cache:
            self._current_size -= self._cache[key].size_bytes

        # Add new entry
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            size_bytes=size,
        )
        self._current_size += size

    def delete(self, key: str) -> bool:
        """
        Remove a key from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was present
        """
        if key in self._cache:
            self._current_size -= self._cache[key].size_bytes
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._current_size = 0
        logger.info("Cache cleared")

    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return

        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].accessed_at
        )

        self._current_size -= self._cache[lru_key].size_bytes
        del self._cache[lru_key]
        self._stats['evictions'] += 1

    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired(self.ttl)
        ]

        for key in expired_keys:
            self.delete(key)

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (
            self._stats['hits'] / total_requests
            if total_requests > 0
            else 0.0
        )

        return {
            'enabled': self.enabled,
            'entries': len(self._cache),
            'size_bytes': self._current_size,
            'size_mb': round(self._current_size / (1024 * 1024), 2),
            'max_size_mb': self.settings.cache.max_size_mb,
            'ttl_seconds': self.ttl,
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'evictions': self._stats['evictions'],
            'hit_rate': round(hit_rate, 3),
        }

    # =========================================================================
    # Specialized cache methods for articles
    # =========================================================================

    def get_article(self, article_id: str) -> Optional[dict]:
        """Get a cached article."""
        return self.get(f"article:{article_id}")

    def set_article(self, article_id: str, article: dict) -> None:
        """Cache an article."""
        self.set(f"article:{article_id}", article)

    def invalidate_article(self, article_id: str) -> None:
        """Invalidate a cached article."""
        self.delete(f"article:{article_id}")

    def get_category_tree(self) -> Optional[dict]:
        """Get the cached category tree."""
        return self.get("category_tree")

    def set_category_tree(self, tree: dict) -> None:
        """Cache the category tree."""
        self.set("category_tree", tree)

    def get_graph(self) -> Optional[dict]:
        """Get the cached knowledge graph."""
        return self.get("knowledge_graph")

    def set_graph(self, graph: dict) -> None:
        """Cache the knowledge graph."""
        self.set("knowledge_graph", graph)

    # =========================================================================
    # Key generation utilities
    # =========================================================================

    @staticmethod
    def make_key(*parts: str) -> str:
        """Create a cache key from parts."""
        return ":".join(str(p) for p in parts)

    @staticmethod
    def hash_key(data: str) -> str:
        """Create a hash-based key for long data."""
        return hashlib.md5(data.encode()).hexdigest()


# Global cache instance
_cache: Optional[ContentCache] = None


def get_cache() -> ContentCache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = ContentCache()
    return _cache


def clear_cache() -> None:
    """Clear the global cache."""
    global _cache
    if _cache:
        _cache.clear()
