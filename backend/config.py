"""
Configuration Management
========================
Loads and validates application settings from YAML configuration files.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

import os
from pathlib import Path
from typing import Any, Optional
from functools import lru_cache

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# ==============================================================================
# Path Resolution
# ==============================================================================

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.resolve()


def resolve_path(path: str, base: Optional[Path] = None) -> Path:
    """Resolve a path relative to base or project root."""
    if base is None:
        base = get_project_root()
    path_obj = Path(path)
    if path_obj.is_absolute():
        return path_obj
    return (base / path_obj).resolve()


# ==============================================================================
# Configuration Models
# ==============================================================================

class AppConfig(BaseModel):
    """Application identity configuration."""
    name: str = "Knowledge Nexus"
    version: str = "1.0.0"
    description: str = "Interactive Knowledge Base Explorer"
    author: str = "Dennis 'dnoice' Smaltz"
    signature: str = "Aim Twice, Shoot Once!"


class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    workers: int = 1
    cors_origins: list[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ])


class PathsConfig(BaseModel):
    """Path configuration."""
    articles: str = "articles"
    data: str = "data"
    static: str = "front-end"
    config: str = "config"

    def resolve(self, base: Path) -> dict[str, Path]:
        """Resolve all paths relative to base directory."""
        return {
            "articles": resolve_path(self.articles, base),
            "data": resolve_path(self.data, base),
            "static": resolve_path(self.static, base),
            "config": resolve_path(self.config, base),
        }


class CacheConfig(BaseModel):
    """Cache configuration."""
    enabled: bool = True
    ttl_seconds: int = 3600
    max_size_mb: int = 100
    preload_on_startup: bool = True


class SearchConfig(BaseModel):
    """Search engine configuration."""
    index_path: str = "data/search_index"
    min_word_length: int = 2
    fuzzy_distance: int = 1
    highlight_fragments: int = 3
    results_per_page: int = 20
    max_results: int = 100
    boost_title: float = 3.0
    boost_description: float = 2.0
    boost_features: float = 1.5


class GraphLayoutConfig(BaseModel):
    """Graph layout configuration."""
    force_strength: int = -300
    link_distance: int = 100
    collision_radius: int = 30


class GraphConfig(BaseModel):
    """Knowledge graph configuration."""
    output_path: str = "data/graph.json"
    min_edge_weight: float = 0.3
    include_empty_categories: bool = False
    tag_connection_weight: float = 0.5
    reference_connection_weight: float = 1.0
    category_connection_weight: float = 0.8
    layout: GraphLayoutConfig = Field(default_factory=GraphLayoutConfig)


class CodeHiliteConfig(BaseModel):
    """Code highlighting configuration."""
    css_class: str = "highlight"
    guess_lang: bool = True
    linenums: bool = False


class TocConfig(BaseModel):
    """Table of contents configuration."""
    permalink: bool = True
    toc_depth: int = 4


class ExtensionConfigs(BaseModel):
    """Markdown extension configurations."""
    codehilite: CodeHiliteConfig = Field(default_factory=CodeHiliteConfig)
    toc: TocConfig = Field(default_factory=TocConfig)


class MarkdownConfig(BaseModel):
    """Markdown processing configuration."""
    extensions: list[str] = Field(default_factory=lambda: [
        "tables", "fenced_code", "codehilite", "toc", "footnotes", "smarty", "meta"
    ])
    extension_configs: ExtensionConfigs = Field(default_factory=ExtensionConfigs)


class ReadingConfig(BaseModel):
    """Reading time calculation configuration."""
    words_per_minute: int = 200
    min_reading_time: int = 1


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class Settings(BaseModel):
    """Complete application settings."""
    app: AppConfig = Field(default_factory=AppConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    graph: GraphConfig = Field(default_factory=GraphConfig)
    markdown: MarkdownConfig = Field(default_factory=MarkdownConfig)
    reading: ReadingConfig = Field(default_factory=ReadingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Resolved paths (populated after loading)
    _resolved_paths: dict[str, Path] = {}

    class Config:
        arbitrary_types_allowed = True

    def get_path(self, name: str) -> Path:
        """Get a resolved path by name."""
        if not self._resolved_paths:
            self._resolved_paths = self.paths.resolve(get_project_root())
        return self._resolved_paths.get(name, get_project_root())

    @property
    def articles_path(self) -> Path:
        return self.get_path("articles")

    @property
    def data_path(self) -> Path:
        return self.get_path("data")

    @property
    def static_path(self) -> Path:
        return self.get_path("static")

    @property
    def config_path(self) -> Path:
        return self.get_path("config")


# ==============================================================================
# Category Configuration
# ==============================================================================

class SubcategoryConfig(BaseModel):
    """Subcategory definition."""
    slug: str
    name: str


class CategoryConfig(BaseModel):
    """Category definition."""
    id: str
    name: str
    short_name: str
    icon: str
    description: str
    color: str
    order: int
    subcategories: list[SubcategoryConfig] = Field(default_factory=list)


class CategoriesConfig(BaseModel):
    """Categories configuration container."""
    categories: list[CategoryConfig] = Field(default_factory=list)

    def get_category(self, category_id: str) -> Optional[CategoryConfig]:
        """Get category by ID."""
        for cat in self.categories:
            if cat.id == category_id:
                return cat
        return None

    def get_category_ids(self) -> list[str]:
        """Get all category IDs."""
        return [cat.id for cat in self.categories]

    def get_icon_for_category(self, category_id: str) -> str:
        """Get icon name for a category."""
        cat = self.get_category(category_id)
        return cat.icon if cat else "folder"


# ==============================================================================
# Configuration Loading
# ==============================================================================

def load_yaml_config(path: Path) -> dict[str, Any]:
    """Load a YAML configuration file."""
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache application settings."""
    config_path = get_project_root() / "config" / "settings.yaml"
    config_data = load_yaml_config(config_path)
    settings = Settings(**config_data)
    # Initialize resolved paths
    settings._resolved_paths = settings.paths.resolve(get_project_root())
    return settings


@lru_cache(maxsize=1)
def get_categories() -> CategoriesConfig:
    """Load and cache categories configuration."""
    config_path = get_project_root() / "config" / "categories.yaml"
    config_data = load_yaml_config(config_path)
    return CategoriesConfig(**config_data)


def reload_settings() -> Settings:
    """Reload settings (clears cache)."""
    get_settings.cache_clear()
    return get_settings()


def reload_categories() -> CategoriesConfig:
    """Reload categories (clears cache)."""
    get_categories.cache_clear()
    return get_categories()


# ==============================================================================
# Module Exports
# ==============================================================================

__all__ = [
    "Settings",
    "CategoriesConfig",
    "CategoryConfig",
    "SubcategoryConfig",
    "get_settings",
    "get_categories",
    "get_project_root",
    "resolve_path",
    "reload_settings",
    "reload_categories",
]
