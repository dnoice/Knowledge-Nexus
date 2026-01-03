# Knowledge Nexus Frontend Implementation Plan

> **Project**: Knowledge Nexus - Interactive Knowledge Base Explorer
> **Author**: Dennis 'dnoice' Smaltz
> **Date**: 2026-01-03
> **Status**: Planning Phase

---

## Executive Summary

Build a beautiful, scholarly-themed web application for exploring the Knowledge Nexus article collection. The solution combines a Python FastAPI backend for intelligent content processing with a modern frontend featuring three navigation paradigms: visual knowledge graph, hierarchical tree browser, and faceted search.

**Design Philosophy**: Aged parchment aesthetic meets modern interaction design. Think ancient library meets digital scholarship.

---

## 1. Project Architecture

### 1.1 Directory Structure

```tree
knowledge-nexus/
├── articles/                    # Existing content (unchanged)
│   ├── 01-theoretical-frontiers/
│   ├── 02-materials-fabrication/
│   └── ... (14 categories)
│
├── config/                      # Configuration files
│   ├── settings.yaml            # Application settings
│   ├── categories.yaml          # Category metadata & icons
│   ├── graph-connections.yaml   # Manual topic relationships
│   └── search-synonyms.yaml     # Search term mappings
│
├── backend/                     # FastAPI Python backend
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Settings loader
│   ├── models/
│   │   ├── __init__.py
│   │   ├── article.py           # Article data models
│   │   ├── category.py          # Category models
│   │   └── graph.py             # Graph node/edge models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── parser.py            # Markdown parser & metadata extractor
│   │   ├── indexer.py           # Search index builder
│   │   ├── graph_builder.py     # Knowledge graph generator
│   │   └── cache.py             # Content caching layer
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── articles.py          # Article CRUD endpoints
│   │   ├── categories.py        # Category endpoints
│   │   ├── search.py            # Search endpoints
│   │   └── graph.py             # Graph data endpoints
│   └── utils/
│       ├── __init__.py
│       └── markdown_extensions.py
│
├── front-end/                   # Frontend application
│   ├── index.html               # Main entry point
│   ├── css/
│   │   ├── tokens.css           # Design tokens (colors, spacing, fonts)
│   │   ├── base.css             # Reset and base styles
│   │   ├── typography.css       # Font styles and scales
│   │   ├── components.css       # Reusable component styles
│   │   ├── layout.css           # Grid and layout systems
│   │   ├── parchment.css        # Sepia theme & textures
│   │   ├── animations.css       # Transitions and keyframes
│   │   └── utilities.css        # Utility classes
│   ├── js/
│   │   ├── app.js               # Main application controller
│   │   ├── router.js            # Client-side routing
│   │   ├── state.js             # State management
│   │   ├── api.js               # Backend API client
│   │   ├── components/
│   │   │   ├── navigation.js    # Nav tree component
│   │   │   ├── search.js        # Search interface
│   │   │   ├── graph.js         # Knowledge graph (D3.js)
│   │   │   ├── reader.js        # Article reader
│   │   │   ├── panels.js        # Split panel manager
│   │   │   └── toc.js           # Table of contents
│   │   └── utils/
│   │       ├── markdown.js      # Client-side MD rendering
│   │       ├── debounce.js      # Utility functions
│   │       └── keyboard.js      # Keyboard shortcuts
│   ├── assets/
│   │   ├── icons/               # SVG icon library
│   │   │   ├── categories/      # Category-specific icons
│   │   │   ├── ui/              # Interface icons
│   │   │   └── sprite.svg       # Combined SVG sprite
│   │   ├── textures/            # Parchment textures
│   │   │   ├── paper-light.png
│   │   │   ├── paper-aged.png
│   │   │   └── paper-dark.png
│   │   └── fonts/               # Custom typography
│   └── favicon.svg
│
├── data/                        # Generated data (gitignored)
│   ├── index.json               # Search index
│   ├── graph.json               # Knowledge graph data
│   ├── articles.json            # Parsed article metadata
│   └── cache/                   # Rendered content cache
│
├── scripts/                     # Build and utility scripts
│   ├── build_index.py           # Rebuild search index
│   ├── generate_graph.py        # Generate graph data
│   └── dev_server.py            # Development server
│
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Python project config
├── IMPLEMENTATION_PLAN.md       # This document
└── README.md                    # Project documentation
```

---

## 2. Backend Architecture (FastAPI)

### 2.1 Core Dependencies

```txt
# requirements.txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-frontmatter>=1.1.0
markdown>=3.5.0
pyyaml>=6.0.1
whoosh>=2.7.4              # Full-text search
networkx>=3.2              # Graph processing
python-slugify>=8.0.0
pydantic>=2.5.0
httpx>=0.26.0              # Async HTTP client
watchfiles>=0.21.0         # Hot reload
rich>=13.7.0               # CLI output
```

### 2.2 Article Data Model

```python
# backend/models/article.py
from pydantic import BaseModel
from typing import Optional
from datetime import date

class ArticleMetadata(BaseModel):
    """Extracted from docstring header"""
    title: str
    file_name: str
    relative_path: str
    artifact_type: str
    version: str
    date: date
    update: str
    author: str
    ai_acknowledgement: str
    description: str
    key_features: list[str]

class Article(BaseModel):
    """Complete article representation"""
    id: str                          # slug from path
    slug: str                        # URL-friendly identifier
    category_id: str                 # e.g., "01-theoretical-frontiers"
    subcategory: str                 # e.g., "consciousness-hard-problem"
    metadata: ArticleMetadata
    content: str                     # Raw markdown
    content_html: str                # Rendered HTML
    toc: list[dict]                  # Table of contents
    word_count: int
    reading_time_minutes: int
    has_notes: bool
    has_citations: bool
    related_articles: list[str]      # IDs of related articles
    tags: list[str]                  # Extracted keywords
```

### 2.3 Metadata Parser

```python
# backend/services/parser.py
import re
from pathlib import Path
from typing import Optional
import frontmatter

class DocstringParser:
    """Parse the custom docstring metadata format"""

    METADATA_PATTERN = re.compile(
        r'<!--\s*\n(.*?)\n-+\s*-->',
        re.DOTALL
    )

    FIELD_PATTERN = re.compile(
        r'-\s*([^:]+):\s*(.+?)(?=\n\s*-|\n\n|$)',
        re.DOTALL
    )

    def parse_file(self, path: Path) -> dict:
        """Extract metadata and content from markdown file"""
        content = path.read_text(encoding='utf-8')

        # Extract docstring block
        match = self.METADATA_PATTERN.search(content)
        if not match:
            return self._empty_metadata(path)

        docstring = match.group(1)
        metadata = self._parse_docstring(docstring)

        # Remove docstring from content
        clean_content = self.METADATA_PATTERN.sub('', content).strip()

        return {
            'metadata': metadata,
            'content': clean_content,
            'toc': self._extract_toc(clean_content)
        }

    def _parse_docstring(self, docstring: str) -> dict:
        """Parse docstring fields into dictionary"""
        metadata = {}
        current_section = None

        for line in docstring.split('\n'):
            line = line.strip()

            # Section header (e.g., "Metadata", "Description")
            if line.startswith('✒'):
                section_match = re.match(r'✒\s*(\w+)', line)
                if section_match:
                    current_section = section_match.group(1).lower()
                    # Check for inline value
                    if ':' in line:
                        value = line.split(':', 1)[1].strip()
                        metadata[current_section] = value
                continue

            # Field within section
            if line.startswith('-') and ':' in line:
                field_match = re.match(r'-\s*([^:]+):\s*(.+)', line)
                if field_match:
                    key = self._normalize_key(field_match.group(1))
                    value = field_match.group(2).strip()
                    metadata[key] = value

            # Feature list items
            elif line.startswith('- Feature') and current_section == 'key features':
                if 'key_features' not in metadata:
                    metadata['key_features'] = []
                feature = re.sub(r'^-\s*Feature\s*\d+:\s*', '', line)
                metadata['key_features'].append(feature)

        return metadata

    def _extract_toc(self, content: str) -> list[dict]:
        """Extract table of contents from markdown headings"""
        toc = []
        for match in re.finditer(r'^(#{1,4})\s+(.+)$', content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            slug = self._slugify(title)
            toc.append({
                'level': level,
                'title': title,
                'slug': slug
            })
        return toc
```

### 2.4 API Endpoints

```python
# backend/routers/articles.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/api/articles", tags=["articles"])

@router.get("/")
async def list_articles(
    category: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[list[str]] = Query(None),
    limit: int = 50,
    offset: int = 0
):
    """List articles with optional filtering"""
    pass

@router.get("/{article_id}")
async def get_article(article_id: str):
    """Get single article with full content"""
    pass

@router.get("/{article_id}/notes")
async def get_article_notes(article_id: str):
    """Get companion notes for article"""
    pass

@router.get("/{article_id}/citations")
async def get_article_citations(article_id: str):
    """Get works cited for article"""
    pass

@router.get("/{article_id}/related")
async def get_related_articles(article_id: str, limit: int = 5):
    """Get related articles based on graph connections"""
    pass
```

```python
# backend/routers/search.py
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/search", tags=["search"])

@router.get("/")
async def search(
    q: str = Query(..., min_length=2),
    categories: Optional[list[str]] = Query(None),
    fuzzy: bool = True,
    limit: int = 20
):
    """Full-text search with faceted filtering"""
    pass

@router.get("/suggest")
async def suggest(q: str = Query(..., min_length=1), limit: int = 8):
    """Autocomplete suggestions"""
    pass

@router.get("/facets")
async def get_facets():
    """Get available filter facets (categories, tags, etc.)"""
    pass
```

```python
# backend/routers/graph.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/graph", tags=["graph"])

@router.get("/")
async def get_full_graph():
    """Get complete knowledge graph for visualization"""
    pass

@router.get("/neighborhood/{article_id}")
async def get_neighborhood(article_id: str, depth: int = 2):
    """Get local graph around specific article"""
    pass

@router.get("/categories")
async def get_category_graph():
    """Get category-level graph overview"""
    pass
```

### 2.5 Search Index (Whoosh)

```python
# backend/services/indexer.py
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD, STORED
from whoosh.qparser import MultifieldParser, FuzzyTermPlugin
from whoosh.analysis import StemmingAnalyzer
from pathlib import Path

class SearchIndexer:
    """Build and query full-text search index"""

    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.schema = Schema(
            id=ID(stored=True, unique=True),
            title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            description=TEXT(stored=True),
            content=TEXT(analyzer=StemmingAnalyzer()),
            category=ID(stored=True),
            subcategory=ID(stored=True),
            tags=KEYWORD(stored=True, commas=True, lowercase=True),
            features=TEXT(stored=True)
        )

    def build_index(self, articles: list[dict]):
        """Build fresh search index from articles"""
        self.index_path.mkdir(parents=True, exist_ok=True)
        ix = create_in(str(self.index_path), self.schema)

        writer = ix.writer()
        for article in articles:
            writer.add_document(
                id=article['id'],
                title=article['metadata']['title'],
                description=article['metadata'].get('description', ''),
                content=article['content'],
                category=article['category_id'],
                subcategory=article['subcategory'],
                tags=','.join(article.get('tags', [])),
                features='\n'.join(article['metadata'].get('key_features', []))
            )
        writer.commit()

    def search(self, query: str, categories: list[str] = None,
               fuzzy: bool = True, limit: int = 20) -> list[dict]:
        """Execute search query"""
        ix = open_dir(str(self.index_path))

        parser = MultifieldParser(
            ['title', 'description', 'content', 'tags', 'features'],
            schema=self.schema
        )
        if fuzzy:
            parser.add_plugin(FuzzyTermPlugin())

        with ix.searcher() as searcher:
            q = parser.parse(query)
            results = searcher.search(q, limit=limit)

            return [
                {
                    'id': hit['id'],
                    'title': hit['title'],
                    'description': hit['description'],
                    'category': hit['category'],
                    'score': hit.score,
                    'highlights': hit.highlights('content', top=3)
                }
                for hit in results
            ]
```

### 2.6 Knowledge Graph Builder

```python
# backend/services/graph_builder.py
import networkx as nx
from collections import defaultdict
import re

class KnowledgeGraphBuilder:
    """Build knowledge graph from articles and their relationships"""

    def __init__(self):
        self.graph = nx.Graph()

    def build_graph(self, articles: list[dict],
                    manual_connections: dict = None) -> dict:
        """
        Build knowledge graph with:
        1. Category nodes
        2. Article nodes
        3. Edges based on:
           - Same category (weak)
           - Shared tags (medium)
           - Cross-references (strong)
           - Manual connections (strongest)
        """
        # Add category nodes
        categories = set()
        for article in articles:
            cat_id = article['category_id']
            categories.add(cat_id)

            self.graph.add_node(
                cat_id,
                type='category',
                label=self._format_category_label(cat_id),
                size=30
            )

        # Add article nodes
        for article in articles:
            self.graph.add_node(
                article['id'],
                type='article',
                label=article['metadata']['title'],
                category=article['category_id'],
                size=15
            )

            # Edge to category
            self.graph.add_edge(
                article['id'],
                article['category_id'],
                weight=1,
                type='category'
            )

        # Find connections between articles
        self._add_tag_connections(articles)
        self._add_cross_references(articles)

        if manual_connections:
            self._add_manual_connections(manual_connections)

        return self._export_for_d3()

    def _add_tag_connections(self, articles: list[dict]):
        """Connect articles sharing tags"""
        tag_to_articles = defaultdict(list)

        for article in articles:
            for tag in article.get('tags', []):
                tag_to_articles[tag].append(article['id'])

        for tag, article_ids in tag_to_articles.items():
            if len(article_ids) > 1:
                for i, a1 in enumerate(article_ids):
                    for a2 in article_ids[i+1:]:
                        if self.graph.has_edge(a1, a2):
                            self.graph[a1][a2]['weight'] += 0.5
                        else:
                            self.graph.add_edge(a1, a2, weight=0.5, type='tag')

    def _add_cross_references(self, articles: list[dict]):
        """Detect cross-references in content"""
        article_titles = {a['metadata']['title'].lower(): a['id'] for a in articles}

        for article in articles:
            content = article['content'].lower()
            for title, target_id in article_titles.items():
                if target_id != article['id'] and title in content:
                    if self.graph.has_edge(article['id'], target_id):
                        self.graph[article['id']][target_id]['weight'] += 1
                    else:
                        self.graph.add_edge(
                            article['id'], target_id,
                            weight=1, type='reference'
                        )

    def _export_for_d3(self) -> dict:
        """Export graph in D3.js force-directed format"""
        return {
            'nodes': [
                {
                    'id': node,
                    **self.graph.nodes[node]
                }
                for node in self.graph.nodes()
            ],
            'links': [
                {
                    'source': u,
                    'target': v,
                    **data
                }
                for u, v, data in self.graph.edges(data=True)
            ]
        }
```

---

## 3. Frontend Architecture

### 3.1 Design Tokens (CSS Custom Properties)

```css
/* front-end/css/tokens.css */

:root {
    /* ===========================================
       SEPIA PARCHMENT COLOR PALETTE
       =========================================== */

    /* Base Parchment Tones */
    --color-parchment-100: #fdf8f0;  /* Lightest - fresh paper */
    --color-parchment-200: #f8f0e3;  /* Light cream */
    --color-parchment-300: #f0e6d3;  /* Warm paper */
    --color-parchment-400: #e8dcc6;  /* Aged paper */
    --color-parchment-500: #d9c9a8;  /* Classic parchment */
    --color-parchment-600: #c4b28a;  /* Darker aged */
    --color-parchment-700: #a89570;  /* Deep parchment */

    /* Ink Colors */
    --color-ink-900: #2c2416;        /* Darkest ink */
    --color-ink-800: #3d3221;        /* Dark sepia ink */
    --color-ink-700: #4a3c28;        /* Standard ink */
    --color-ink-600: #5c4a33;        /* Medium ink */
    --color-ink-500: #7a6548;        /* Faded ink */
    --color-ink-400: #9a8564;        /* Light ink */
    --color-ink-300: #b8a080;        /* Very faded */

    /* Accent Colors (muted, scholarly) */
    --color-accent-rust: #8b4513;    /* Rust/burnt sienna */
    --color-accent-gold: #b8860b;    /* Dark goldenrod */
    --color-accent-forest: #556b2f;  /* Dark olive green */
    --color-accent-navy: #2f4f4f;    /* Dark slate */
    --color-accent-burgundy: #722f37;/* Deep wine */

    /* Semantic Colors */
    --color-bg-primary: var(--color-parchment-200);
    --color-bg-secondary: var(--color-parchment-300);
    --color-bg-elevated: var(--color-parchment-100);
    --color-bg-sunken: var(--color-parchment-400);

    --color-text-primary: var(--color-ink-800);
    --color-text-secondary: var(--color-ink-600);
    --color-text-muted: var(--color-ink-500);
    --color-text-accent: var(--color-accent-rust);

    --color-border-light: var(--color-parchment-500);
    --color-border-medium: var(--color-parchment-600);
    --color-border-dark: var(--color-ink-400);

    --color-link: var(--color-accent-rust);
    --color-link-hover: var(--color-ink-700);
    --color-link-visited: var(--color-accent-burgundy);

    /* ===========================================
       TYPOGRAPHY SCALE
       =========================================== */

    --font-family-serif: 'Crimson Pro', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
    --font-family-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-family-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;

    --font-size-xs: 0.75rem;     /* 12px */
    --font-size-sm: 0.875rem;    /* 14px */
    --font-size-base: 1rem;      /* 16px */
    --font-size-lg: 1.125rem;    /* 18px */
    --font-size-xl: 1.25rem;     /* 20px */
    --font-size-2xl: 1.5rem;     /* 24px */
    --font-size-3xl: 1.875rem;   /* 30px */
    --font-size-4xl: 2.25rem;    /* 36px */
    --font-size-5xl: 3rem;       /* 48px */

    --line-height-tight: 1.25;
    --line-height-normal: 1.5;
    --line-height-relaxed: 1.75;
    --line-height-loose: 2;

    --font-weight-normal: 400;
    --font-weight-medium: 500;
    --font-weight-semibold: 600;
    --font-weight-bold: 700;

    /* ===========================================
       SPACING SCALE
       =========================================== */

    --space-1: 0.25rem;   /* 4px */
    --space-2: 0.5rem;    /* 8px */
    --space-3: 0.75rem;   /* 12px */
    --space-4: 1rem;      /* 16px */
    --space-5: 1.25rem;   /* 20px */
    --space-6: 1.5rem;    /* 24px */
    --space-8: 2rem;      /* 32px */
    --space-10: 2.5rem;   /* 40px */
    --space-12: 3rem;     /* 48px */
    --space-16: 4rem;     /* 64px */
    --space-20: 5rem;     /* 80px */

    /* ===========================================
       SHADOWS & EFFECTS
       =========================================== */

    --shadow-sm: 0 1px 2px rgba(44, 36, 22, 0.08);
    --shadow-md: 0 4px 6px rgba(44, 36, 22, 0.1);
    --shadow-lg: 0 10px 15px rgba(44, 36, 22, 0.15);
    --shadow-xl: 0 20px 25px rgba(44, 36, 22, 0.2);
    --shadow-inner: inset 0 2px 4px rgba(44, 36, 22, 0.1);

    /* Parchment edge shadow */
    --shadow-parchment:
        0 0 0 1px var(--color-parchment-500),
        0 2px 8px rgba(44, 36, 22, 0.15),
        inset 0 0 60px rgba(217, 201, 168, 0.3);

    /* ===========================================
       TRANSITIONS
       =========================================== */

    --transition-fast: 150ms ease;
    --transition-normal: 250ms ease;
    --transition-slow: 400ms ease;
    --transition-bounce: 400ms cubic-bezier(0.34, 1.56, 0.64, 1);

    /* ===========================================
       BORDERS & RADII
       =========================================== */

    --radius-sm: 0.25rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;
    --radius-full: 9999px;

    --border-width-thin: 1px;
    --border-width-medium: 2px;
    --border-width-thick: 4px;

    /* ===========================================
       Z-INDEX SCALE
       =========================================== */

    --z-base: 0;
    --z-dropdown: 100;
    --z-sticky: 200;
    --z-overlay: 300;
    --z-modal: 400;
    --z-toast: 500;
}
```

### 3.2 Parchment Theme Styles

```css
/* front-end/css/parchment.css */

/* ===========================================
   PARCHMENT TEXTURE & EFFECTS
   =========================================== */

/* Base parchment background with texture */
.parchment-bg {
    background-color: var(--color-bg-primary);
    background-image:
        url('../assets/textures/paper-light.png'),
        linear-gradient(
            135deg,
            var(--color-parchment-200) 0%,
            var(--color-parchment-300) 50%,
            var(--color-parchment-200) 100%
        );
    background-blend-mode: multiply;
}

/* Aged parchment effect for cards */
.parchment-card {
    background-color: var(--color-bg-elevated);
    background-image: url('../assets/textures/paper-aged.png');
    background-blend-mode: soft-light;
    box-shadow: var(--shadow-parchment);
    border: var(--border-width-thin) solid var(--color-border-light);
    position: relative;
}

/* Torn edge effect */
.parchment-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(
        90deg,
        transparent 0%,
        var(--color-parchment-600) 2%,
        transparent 4%,
        var(--color-parchment-500) 6%,
        transparent 8%,
        var(--color-parchment-600) 10%,
        transparent 12%
        /* ... repeating pattern */
    );
    opacity: 0.3;
}

/* Ink stain decorative element */
.ink-stain {
    position: relative;
}

.ink-stain::after {
    content: '';
    position: absolute;
    width: 60px;
    height: 60px;
    background: radial-gradient(
        ellipse at center,
        rgba(44, 36, 22, 0.08) 0%,
        rgba(44, 36, 22, 0.04) 40%,
        transparent 70%
    );
    pointer-events: none;
}

/* Decorative border frame */
.ornate-frame {
    border: var(--border-width-medium) solid var(--color-border-medium);
    border-image: url('../assets/textures/border-ornate.svg') 30 round;
    padding: var(--space-6);
}

/* Drop cap for article starts */
.drop-cap::first-letter {
    float: left;
    font-family: var(--font-family-serif);
    font-size: var(--font-size-5xl);
    line-height: 0.8;
    padding-right: var(--space-3);
    padding-top: var(--space-1);
    color: var(--color-accent-rust);
    font-weight: var(--font-weight-bold);
}

/* Horizontal rule - ornate divider */
.divider-ornate {
    border: none;
    height: 24px;
    background: url('../assets/icons/ui/divider.svg') center no-repeat;
    background-size: contain;
    margin: var(--space-8) 0;
    opacity: 0.6;
}

/* Scrollbar styling (webkit) */
::-webkit-scrollbar {
    width: 12px;
    height: 12px;
}

::-webkit-scrollbar-track {
    background: var(--color-parchment-400);
    border-radius: var(--radius-full);
}

::-webkit-scrollbar-thumb {
    background: var(--color-ink-400);
    border-radius: var(--radius-full);
    border: 2px solid var(--color-parchment-400);
}

::-webkit-scrollbar-thumb:hover {
    background: var(--color-ink-500);
}
```

### 3.3 Layout System

```css
/* front-end/css/layout.css */

/* ===========================================
   MAIN APPLICATION LAYOUT
   =========================================== */

.app-container {
    display: grid;
    grid-template-areas:
        "header header header"
        "nav    main   aside"
        "footer footer footer";
    grid-template-columns: minmax(240px, 280px) 1fr minmax(240px, 320px);
    grid-template-rows: auto 1fr auto;
    min-height: 100vh;
    max-width: 1920px;
    margin: 0 auto;
}

.app-header {
    grid-area: header;
    position: sticky;
    top: 0;
    z-index: var(--z-sticky);
}

.app-nav {
    grid-area: nav;
    position: sticky;
    top: var(--header-height, 64px);
    height: calc(100vh - var(--header-height, 64px));
    overflow-y: auto;
    border-right: var(--border-width-thin) solid var(--color-border-light);
}

.app-main {
    grid-area: main;
    padding: var(--space-6);
    min-width: 0; /* Prevent grid blowout */
}

.app-aside {
    grid-area: aside;
    position: sticky;
    top: var(--header-height, 64px);
    height: calc(100vh - var(--header-height, 64px));
    overflow-y: auto;
    border-left: var(--border-width-thin) solid var(--color-border-light);
}

.app-footer {
    grid-area: footer;
}

/* ===========================================
   SPLIT PANEL READER LAYOUT
   =========================================== */

.reader-container {
    display: grid;
    grid-template-columns: 1fr;
    gap: var(--space-4);
    transition: grid-template-columns var(--transition-normal);
}

.reader-container[data-panels="2"] {
    grid-template-columns: 1fr 1fr;
}

.reader-container[data-panels="3"] {
    grid-template-columns: 1fr 1fr 1fr;
}

.reader-panel {
    display: flex;
    flex-direction: column;
    background: var(--color-bg-elevated);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    overflow: hidden;
}

.panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--space-3) var(--space-4);
    background: var(--color-bg-secondary);
    border-bottom: var(--border-width-thin) solid var(--color-border-light);
}

.panel-tabs {
    display: flex;
    gap: var(--space-1);
}

.panel-tab {
    padding: var(--space-2) var(--space-4);
    border-radius: var(--radius-md) var(--radius-md) 0 0;
    background: transparent;
    color: var(--color-text-secondary);
    border: none;
    cursor: pointer;
    transition: all var(--transition-fast);
    font-family: var(--font-family-sans);
    font-size: var(--font-size-sm);
}

.panel-tab:hover {
    background: var(--color-parchment-300);
    color: var(--color-text-primary);
}

.panel-tab[aria-selected="true"] {
    background: var(--color-bg-elevated);
    color: var(--color-text-primary);
    font-weight: var(--font-weight-medium);
}

.panel-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-6);
}

/* ===========================================
   RESPONSIVE BREAKPOINTS
   =========================================== */

@media (max-width: 1200px) {
    .app-container {
        grid-template-areas:
            "header header"
            "nav    main"
            "footer footer";
        grid-template-columns: minmax(200px, 240px) 1fr;
    }

    .app-aside {
        display: none;
    }
}

@media (max-width: 768px) {
    .app-container {
        grid-template-areas:
            "header"
            "main"
            "footer";
        grid-template-columns: 1fr;
    }

    .app-nav {
        position: fixed;
        left: 0;
        top: var(--header-height, 64px);
        width: 280px;
        transform: translateX(-100%);
        transition: transform var(--transition-normal);
        z-index: var(--z-overlay);
        background: var(--color-bg-primary);
    }

    .app-nav[data-open="true"] {
        transform: translateX(0);
    }

    .reader-container[data-panels="2"],
    .reader-container[data-panels="3"] {
        grid-template-columns: 1fr;
    }
}
```

### 3.4 Knowledge Graph Component (D3.js)

```javascript
// front-end/js/components/graph.js

/**
 * Knowledge Graph Visualization
 * Interactive force-directed graph using D3.js
 */

class KnowledgeGraph {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            width: options.width || container.clientWidth,
            height: options.height || container.clientHeight,
            nodeRadius: {
                category: 24,
                article: 12
            },
            colors: {
                category: '#8b4513',    // Rust
                article: '#5c4a33',     // Ink
                link: '#c4b28a',        // Parchment border
                highlight: '#b8860b'    // Gold
            },
            ...options
        };

        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];

        this.init();
    }

    init() {
        // Create SVG container
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', `0 0 ${this.options.width} ${this.options.height}`)
            .attr('class', 'knowledge-graph');

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.3, 3])
            .on('zoom', (event) => {
                this.graphGroup.attr('transform', event.transform);
            });

        this.svg.call(zoom);

        // Create main group for graph elements
        this.graphGroup = this.svg.append('g').attr('class', 'graph-content');

        // Create groups for links and nodes (order matters for z-index)
        this.linksGroup = this.graphGroup.append('g').attr('class', 'links');
        this.nodesGroup = this.graphGroup.append('g').attr('class', 'nodes');

        // Create tooltip
        this.tooltip = d3.select(this.container)
            .append('div')
            .attr('class', 'graph-tooltip')
            .style('opacity', 0);

        // Initialize force simulation
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink()
                .id(d => d.id)
                .distance(d => d.type === 'category' ? 150 : 80)
            )
            .force('charge', d3.forceManyBody()
                .strength(d => d.type === 'category' ? -400 : -150)
            )
            .force('center', d3.forceCenter(
                this.options.width / 2,
                this.options.height / 2
            ))
            .force('collision', d3.forceCollide()
                .radius(d => this.getNodeRadius(d) + 5)
            );
    }

    async loadData(url = '/api/graph') {
        try {
            const response = await fetch(url);
            const data = await response.json();
            this.setData(data);
        } catch (error) {
            console.error('Failed to load graph data:', error);
        }
    }

    setData(data) {
        this.nodes = data.nodes;
        this.links = data.links;
        this.render();
    }

    render() {
        // Render links
        const links = this.linksGroup
            .selectAll('line')
            .data(this.links, d => `${d.source}-${d.target}`)
            .join(
                enter => enter.append('line')
                    .attr('class', 'graph-link')
                    .attr('stroke', this.options.colors.link)
                    .attr('stroke-width', d => Math.sqrt(d.weight || 1))
                    .attr('stroke-opacity', 0.6),
                update => update,
                exit => exit.remove()
            );

        // Render nodes
        const nodeGroups = this.nodesGroup
            .selectAll('g.node')
            .data(this.nodes, d => d.id)
            .join(
                enter => {
                    const g = enter.append('g')
                        .attr('class', d => `node node-${d.type}`)
                        .call(this.drag())
                        .on('click', (event, d) => this.onNodeClick(event, d))
                        .on('mouseenter', (event, d) => this.onNodeHover(event, d, true))
                        .on('mouseleave', (event, d) => this.onNodeHover(event, d, false));

                    // Add circle
                    g.append('circle')
                        .attr('r', d => this.getNodeRadius(d))
                        .attr('fill', d => this.getNodeColor(d))
                        .attr('stroke', 'var(--color-parchment-100)')
                        .attr('stroke-width', 2);

                    // Add icon for categories
                    g.filter(d => d.type === 'category')
                        .append('use')
                        .attr('href', d => `#icon-${this.getCategoryIcon(d.id)}`)
                        .attr('x', -10)
                        .attr('y', -10)
                        .attr('width', 20)
                        .attr('height', 20)
                        .attr('fill', 'var(--color-parchment-100)');

                    // Add label
                    g.append('text')
                        .attr('class', 'node-label')
                        .attr('dy', d => this.getNodeRadius(d) + 14)
                        .attr('text-anchor', 'middle')
                        .text(d => this.truncateLabel(d.label, 20));

                    return g;
                },
                update => update,
                exit => exit.remove()
            );

        // Update simulation
        this.simulation.nodes(this.nodes);
        this.simulation.force('link').links(this.links);
        this.simulation.alpha(1).restart();

        this.simulation.on('tick', () => {
            links
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            nodeGroups.attr('transform', d => `translate(${d.x},${d.y})`);
        });
    }

    getNodeRadius(node) {
        return this.options.nodeRadius[node.type] || 12;
    }

    getNodeColor(node) {
        if (node.type === 'category') {
            return this.options.colors.category;
        }
        return this.options.colors.article;
    }

    getCategoryIcon(categoryId) {
        const iconMap = {
            '01-theoretical-frontiers': 'atom',
            '02-materials-fabrication': 'cube',
            '03-energy-propulsion': 'lightning',
            '04-life-sciences': 'dna',
            '05-mind-cognition': 'brain',
            '06-earth-systems': 'globe',
            '07-space-cosmos': 'stars',
            '08-information-security': 'shield',
            '09-systems-civilization': 'network',
            '10-human-experience': 'heart',
            '11-speculative-fringe': 'question',
            '12-applied-frontiers': 'gear',
            '13-meta-learning': 'book',
            '14-nexus-points': 'link'
        };
        return iconMap[categoryId] || 'circle';
    }

    truncateLabel(label, maxLength) {
        if (label.length <= maxLength) return label;
        return label.substring(0, maxLength - 3) + '...';
    }

    drag() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }

    onNodeClick(event, node) {
        event.stopPropagation();

        if (node.type === 'article') {
            // Navigate to article
            window.dispatchEvent(new CustomEvent('navigate', {
                detail: { path: `/article/${node.id}` }
            }));
        } else {
            // Focus on category
            this.focusOnNode(node);
        }
    }

    onNodeHover(event, node, isEntering) {
        if (isEntering) {
            this.tooltip
                .style('opacity', 1)
                .html(this.getTooltipContent(node))
                .style('left', `${event.pageX + 10}px`)
                .style('top', `${event.pageY - 10}px`);

            // Highlight connected nodes
            this.highlightConnected(node);
        } else {
            this.tooltip.style('opacity', 0);
            this.clearHighlight();
        }
    }

    getTooltipContent(node) {
        if (node.type === 'category') {
            return `
                <strong>${node.label}</strong>
                <br><small>Category</small>
            `;
        }
        return `
            <strong>${node.label}</strong>
            <br><small>${node.category}</small>
        `;
    }

    highlightConnected(node) {
        const connectedIds = new Set([node.id]);
        this.links.forEach(link => {
            if (link.source.id === node.id) connectedIds.add(link.target.id);
            if (link.target.id === node.id) connectedIds.add(link.source.id);
        });

        this.nodesGroup.selectAll('.node')
            .classed('dimmed', d => !connectedIds.has(d.id));

        this.linksGroup.selectAll('line')
            .classed('dimmed', d =>
                d.source.id !== node.id && d.target.id !== node.id
            );
    }

    clearHighlight() {
        this.nodesGroup.selectAll('.node').classed('dimmed', false);
        this.linksGroup.selectAll('line').classed('dimmed', false);
    }

    focusOnNode(node, duration = 750) {
        const scale = 1.5;
        const x = this.options.width / 2 - node.x * scale;
        const y = this.options.height / 2 - node.y * scale;

        this.svg.transition()
            .duration(duration)
            .call(
                d3.zoom().transform,
                d3.zoomIdentity.translate(x, y).scale(scale)
            );
    }

    resize() {
        this.options.width = this.container.clientWidth;
        this.options.height = this.container.clientHeight;

        this.svg.attr('viewBox', `0 0 ${this.options.width} ${this.options.height}`);

        this.simulation
            .force('center', d3.forceCenter(
                this.options.width / 2,
                this.options.height / 2
            ))
            .alpha(0.3)
            .restart();
    }
}

export { KnowledgeGraph };
```

### 3.5 Search Component

```javascript
// front-end/js/components/search.js

/**
 * Faceted Search Interface
 * Full-text search with autocomplete and category filtering
 */

class SearchInterface {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            apiBase: '/api/search',
            debounceMs: 250,
            minChars: 2,
            maxSuggestions: 8,
            ...options
        };

        this.state = {
            query: '',
            categories: [],
            results: [],
            suggestions: [],
            isLoading: false,
            showSuggestions: false
        };

        this.elements = {};
        this.debounceTimer = null;

        this.init();
    }

    init() {
        this.render();
        this.bindEvents();
        this.loadFacets();
    }

    render() {
        this.container.innerHTML = `
            <div class="search-interface">
                <div class="search-input-wrapper">
                    <svg class="search-icon" aria-hidden="true">
                        <use href="#icon-search"></use>
                    </svg>
                    <input
                        type="search"
                        class="search-input"
                        placeholder="Search articles, topics, concepts..."
                        autocomplete="off"
                        aria-label="Search knowledge base"
                        aria-describedby="search-help"
                    >
                    <button class="search-clear" aria-label="Clear search" hidden>
                        <svg><use href="#icon-x"></use></svg>
                    </button>
                </div>

                <div class="search-suggestions" role="listbox" hidden>
                    <!-- Populated dynamically -->
                </div>

                <div class="search-facets">
                    <div class="facet-group">
                        <span class="facet-label">Categories:</span>
                        <div class="facet-chips" role="group" aria-label="Category filters">
                            <!-- Populated dynamically -->
                        </div>
                    </div>
                </div>

                <p id="search-help" class="search-help">
                    Press <kbd>/</kbd> to focus search. Use arrow keys to navigate suggestions.
                </p>

                <div class="search-results" role="region" aria-live="polite">
                    <!-- Populated dynamically -->
                </div>
            </div>
        `;

        // Cache element references
        this.elements = {
            input: this.container.querySelector('.search-input'),
            clear: this.container.querySelector('.search-clear'),
            suggestions: this.container.querySelector('.search-suggestions'),
            facets: this.container.querySelector('.facet-chips'),
            results: this.container.querySelector('.search-results')
        };
    }

    bindEvents() {
        // Input events
        this.elements.input.addEventListener('input', (e) => {
            this.onInputChange(e.target.value);
        });

        this.elements.input.addEventListener('focus', () => {
            if (this.state.suggestions.length > 0) {
                this.showSuggestions(true);
            }
        });

        this.elements.input.addEventListener('keydown', (e) => {
            this.onKeyDown(e);
        });

        // Clear button
        this.elements.clear.addEventListener('click', () => {
            this.clear();
        });

        // Click outside to close suggestions
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.showSuggestions(false);
            }
        });

        // Global keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && document.activeElement !== this.elements.input) {
                e.preventDefault();
                this.elements.input.focus();
            }
        });
    }

    async loadFacets() {
        try {
            const response = await fetch(`${this.options.apiBase}/facets`);
            const facets = await response.json();
            this.renderFacets(facets.categories);
        } catch (error) {
            console.error('Failed to load facets:', error);
        }
    }

    renderFacets(categories) {
        this.elements.facets.innerHTML = categories.map(cat => `
            <button
                class="facet-chip"
                data-category="${cat.id}"
                aria-pressed="false"
            >
                <svg class="facet-icon"><use href="#icon-${cat.icon}"></use></svg>
                <span>${cat.label}</span>
                <span class="facet-count">${cat.count}</span>
            </button>
        `).join('');

        // Bind facet click events
        this.elements.facets.querySelectorAll('.facet-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                this.toggleFacet(chip.dataset.category);
            });
        });
    }

    toggleFacet(categoryId) {
        const index = this.state.categories.indexOf(categoryId);
        if (index === -1) {
            this.state.categories.push(categoryId);
        } else {
            this.state.categories.splice(index, 1);
        }

        // Update UI
        this.elements.facets.querySelectorAll('.facet-chip').forEach(chip => {
            const isActive = this.state.categories.includes(chip.dataset.category);
            chip.setAttribute('aria-pressed', isActive);
            chip.classList.toggle('active', isActive);
        });

        // Re-run search if we have a query
        if (this.state.query.length >= this.options.minChars) {
            this.search();
        }
    }

    onInputChange(value) {
        this.state.query = value;
        this.elements.clear.hidden = value.length === 0;

        // Debounce API calls
        clearTimeout(this.debounceTimer);

        if (value.length < this.options.minChars) {
            this.state.suggestions = [];
            this.showSuggestions(false);
            return;
        }

        this.debounceTimer = setTimeout(() => {
            this.fetchSuggestions(value);
        }, this.options.debounceMs);
    }

    async fetchSuggestions(query) {
        try {
            const params = new URLSearchParams({
                q: query,
                limit: this.options.maxSuggestions
            });

            const response = await fetch(`${this.options.apiBase}/suggest?${params}`);
            const suggestions = await response.json();

            this.state.suggestions = suggestions;
            this.renderSuggestions(suggestions);
            this.showSuggestions(true);
        } catch (error) {
            console.error('Failed to fetch suggestions:', error);
        }
    }

    renderSuggestions(suggestions) {
        if (suggestions.length === 0) {
            this.elements.suggestions.innerHTML = `
                <div class="suggestion-empty">
                    No suggestions found
                </div>
            `;
            return;
        }

        this.elements.suggestions.innerHTML = suggestions.map((s, i) => `
            <div
                class="suggestion-item"
                role="option"
                data-index="${i}"
                data-id="${s.id}"
            >
                <svg class="suggestion-icon">
                    <use href="#icon-${s.type === 'category' ? 'folder' : 'file-text'}"></use>
                </svg>
                <div class="suggestion-content">
                    <span class="suggestion-title">${this.highlightMatch(s.title, this.state.query)}</span>
                    <span class="suggestion-category">${s.category}</span>
                </div>
            </div>
        `).join('');

        // Bind click events
        this.elements.suggestions.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectSuggestion(parseInt(item.dataset.index));
            });
        });
    }

    highlightMatch(text, query) {
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    showSuggestions(show) {
        this.state.showSuggestions = show;
        this.elements.suggestions.hidden = !show;
    }

    onKeyDown(e) {
        if (!this.state.showSuggestions) {
            if (e.key === 'Enter') {
                this.search();
            }
            return;
        }

        const items = this.elements.suggestions.querySelectorAll('.suggestion-item');
        const currentIndex = [...items].findIndex(item => item.classList.contains('focused'));

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.focusSuggestion(Math.min(currentIndex + 1, items.length - 1));
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.focusSuggestion(Math.max(currentIndex - 1, 0));
                break;
            case 'Enter':
                e.preventDefault();
                if (currentIndex >= 0) {
                    this.selectSuggestion(currentIndex);
                } else {
                    this.search();
                }
                break;
            case 'Escape':
                this.showSuggestions(false);
                break;
        }
    }

    focusSuggestion(index) {
        const items = this.elements.suggestions.querySelectorAll('.suggestion-item');
        items.forEach((item, i) => {
            item.classList.toggle('focused', i === index);
        });
    }

    selectSuggestion(index) {
        const suggestion = this.state.suggestions[index];
        if (!suggestion) return;

        this.showSuggestions(false);

        // Navigate to article
        window.dispatchEvent(new CustomEvent('navigate', {
            detail: { path: `/article/${suggestion.id}` }
        }));
    }

    async search() {
        if (this.state.query.length < this.options.minChars) return;

        this.state.isLoading = true;
        this.showSuggestions(false);
        this.renderLoadingState();

        try {
            const params = new URLSearchParams({
                q: this.state.query,
                fuzzy: true,
                limit: 20
            });

            this.state.categories.forEach(cat => {
                params.append('categories', cat);
            });

            const response = await fetch(`${this.options.apiBase}?${params}`);
            const results = await response.json();

            this.state.results = results;
            this.renderResults(results);
        } catch (error) {
            console.error('Search failed:', error);
            this.renderError();
        } finally {
            this.state.isLoading = false;
        }
    }

    renderLoadingState() {
        this.elements.results.innerHTML = `
            <div class="search-loading">
                <div class="loading-spinner"></div>
                <span>Searching...</span>
            </div>
        `;
    }

    renderResults(results) {
        if (results.length === 0) {
            this.elements.results.innerHTML = `
                <div class="search-empty">
                    <svg class="empty-icon"><use href="#icon-search-x"></use></svg>
                    <h3>No results found</h3>
                    <p>Try different keywords or remove some filters</p>
                </div>
            `;
            return;
        }

        this.elements.results.innerHTML = `
            <div class="results-header">
                <span class="results-count">${results.length} results</span>
            </div>
            <ul class="results-list">
                ${results.map(r => `
                    <li class="result-item">
                        <a href="/article/${r.id}" class="result-link">
                            <h3 class="result-title">${r.title}</h3>
                            <p class="result-description">${r.description}</p>
                            <div class="result-meta">
                                <span class="result-category">${r.category}</span>
                                ${r.highlights ? `<span class="result-highlight">${r.highlights}</span>` : ''}
                            </div>
                        </a>
                    </li>
                `).join('')}
            </ul>
        `;
    }

    renderError() {
        this.elements.results.innerHTML = `
            <div class="search-error">
                <svg class="error-icon"><use href="#icon-alert-circle"></use></svg>
                <h3>Search failed</h3>
                <p>Please try again later</p>
            </div>
        `;
    }

    clear() {
        this.state.query = '';
        this.state.suggestions = [];
        this.state.results = [];
        this.elements.input.value = '';
        this.elements.clear.hidden = true;
        this.showSuggestions(false);
        this.elements.results.innerHTML = '';
        this.elements.input.focus();
    }
}

export { SearchInterface };
```

### 3.6 Navigation Tree Component

```javascript
// front-end/js/components/navigation.js

/**
 * Hierarchical Navigation Tree
 * Expandable category tree with smart filtering
 */

class NavigationTree {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            apiBase: '/api/categories',
            collapsedByDefault: true,
            showArticleCount: true,
            ...options
        };

        this.state = {
            categories: [],
            expanded: new Set(),
            activeArticle: null,
            filterText: ''
        };

        this.init();
    }

    async init() {
        this.render();
        await this.loadCategories();
        this.bindEvents();
    }

    render() {
        this.container.innerHTML = `
            <nav class="nav-tree" aria-label="Article categories">
                <div class="nav-filter">
                    <svg class="filter-icon"><use href="#icon-filter"></use></svg>
                    <input
                        type="text"
                        class="nav-filter-input"
                        placeholder="Filter categories..."
                        aria-label="Filter navigation"
                    >
                </div>
                <ul class="nav-list" role="tree">
                    <!-- Populated dynamically -->
                </ul>
            </nav>
        `;

        this.elements = {
            list: this.container.querySelector('.nav-list'),
            filter: this.container.querySelector('.nav-filter-input')
        };
    }

    async loadCategories() {
        try {
            const response = await fetch(this.options.apiBase);
            const categories = await response.json();
            this.state.categories = categories;
            this.renderTree(categories);
        } catch (error) {
            console.error('Failed to load categories:', error);
            this.renderError();
        }
    }

    renderTree(categories) {
        this.elements.list.innerHTML = categories.map(cat => `
            <li class="nav-category" role="treeitem" aria-expanded="false">
                <div class="nav-category-header" data-id="${cat.id}">
                    <button class="nav-toggle" aria-label="Toggle ${cat.name}">
                        <svg class="toggle-icon"><use href="#icon-chevron-right"></use></svg>
                    </button>
                    <svg class="nav-icon"><use href="#icon-${cat.icon}"></use></svg>
                    <span class="nav-label">${cat.name}</span>
                    ${this.options.showArticleCount ? `
                        <span class="nav-count">${cat.articleCount}</span>
                    ` : ''}
                </div>
                <ul class="nav-subcategories" role="group" hidden>
                    ${cat.subcategories.map(sub => `
                        <li class="nav-subcategory" role="treeitem">
                            <a
                                href="/category/${cat.id}/${sub.slug}"
                                class="nav-subcategory-link"
                                data-id="${sub.id}"
                            >
                                <span class="nav-label">${sub.name}</span>
                                ${this.options.showArticleCount && sub.articleCount ? `
                                    <span class="nav-count">${sub.articleCount}</span>
                                ` : ''}
                            </a>
                            ${sub.articles && sub.articles.length > 0 ? `
                                <ul class="nav-articles" role="group">
                                    ${sub.articles.map(article => `
                                        <li class="nav-article" role="treeitem">
                                            <a
                                                href="/article/${article.id}"
                                                class="nav-article-link"
                                                data-id="${article.id}"
                                            >
                                                ${article.title}
                                            </a>
                                        </li>
                                    `).join('')}
                                </ul>
                            ` : ''}
                        </li>
                    `).join('')}
                </ul>
            </li>
        `).join('');
    }

    bindEvents() {
        // Toggle category expansion
        this.elements.list.addEventListener('click', (e) => {
            const toggle = e.target.closest('.nav-toggle');
            const header = e.target.closest('.nav-category-header');

            if (toggle || (header && !e.target.closest('a'))) {
                const categoryId = header?.dataset.id;
                if (categoryId) {
                    this.toggleCategory(categoryId);
                }
            }
        });

        // Filter input
        this.elements.filter.addEventListener('input', (e) => {
            this.filterTree(e.target.value);
        });

        // Handle navigation
        this.elements.list.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link) {
                e.preventDefault();
                const path = link.getAttribute('href');
                window.dispatchEvent(new CustomEvent('navigate', {
                    detail: { path }
                }));
            }
        });
    }

    toggleCategory(categoryId) {
        const isExpanded = this.state.expanded.has(categoryId);

        if (isExpanded) {
            this.state.expanded.delete(categoryId);
        } else {
            this.state.expanded.add(categoryId);
        }

        const categoryEl = this.elements.list.querySelector(
            `.nav-category-header[data-id="${categoryId}"]`
        ).parentElement;

        const subcategories = categoryEl.querySelector('.nav-subcategories');

        categoryEl.setAttribute('aria-expanded', !isExpanded);
        subcategories.hidden = isExpanded;

        // Animate toggle icon
        const toggleIcon = categoryEl.querySelector('.toggle-icon');
        toggleIcon.style.transform = isExpanded ? '' : 'rotate(90deg)';
    }

    filterTree(text) {
        this.state.filterText = text.toLowerCase();

        const categories = this.elements.list.querySelectorAll('.nav-category');

        categories.forEach(catEl => {
            const catName = catEl.querySelector('.nav-label').textContent.toLowerCase();
            const subcategories = catEl.querySelectorAll('.nav-subcategory');
            let hasVisibleSubcategory = false;

            subcategories.forEach(subEl => {
                const subName = subEl.querySelector('.nav-label').textContent.toLowerCase();
                const articles = subEl.querySelectorAll('.nav-article');
                let hasVisibleArticle = false;

                articles.forEach(artEl => {
                    const artName = artEl.textContent.toLowerCase();
                    const matches = artName.includes(this.state.filterText);
                    artEl.hidden = !matches && this.state.filterText.length > 0;
                    if (matches) hasVisibleArticle = true;
                });

                const matches = subName.includes(this.state.filterText) || hasVisibleArticle;
                subEl.hidden = !matches && this.state.filterText.length > 0;
                if (matches) hasVisibleSubcategory = true;
            });

            const matches = catName.includes(this.state.filterText) || hasVisibleSubcategory;
            catEl.hidden = !matches && this.state.filterText.length > 0;

            // Auto-expand categories with matches
            if (matches && this.state.filterText.length > 0) {
                const catId = catEl.querySelector('.nav-category-header').dataset.id;
                if (!this.state.expanded.has(catId)) {
                    this.toggleCategory(catId);
                }
            }
        });
    }

    setActiveArticle(articleId) {
        // Remove previous active state
        this.elements.list.querySelectorAll('.nav-article-link.active')
            .forEach(el => el.classList.remove('active'));

        // Set new active state
        const activeLink = this.elements.list.querySelector(
            `.nav-article-link[data-id="${articleId}"]`
        );

        if (activeLink) {
            activeLink.classList.add('active');

            // Ensure parent categories are expanded
            const category = activeLink.closest('.nav-category');
            const catId = category.querySelector('.nav-category-header').dataset.id;

            if (!this.state.expanded.has(catId)) {
                this.toggleCategory(catId);
            }

            // Scroll into view
            activeLink.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        this.state.activeArticle = articleId;
    }

    renderError() {
        this.elements.list.innerHTML = `
            <li class="nav-error">
                <svg class="error-icon"><use href="#icon-alert-circle"></use></svg>
                <span>Failed to load navigation</span>
            </li>
        `;
    }
}

export { NavigationTree };
```

---

## 4. SVG Icon Library

### 4.1 Icon Sprite Structure

```xml
<!-- front-end/assets/icons/sprite.svg -->
<svg xmlns="http://www.w3.org/2000/svg" style="display: none;">

    <!-- UI Icons -->
    <symbol id="icon-search" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/>
        <path d="m21 21-4.35-4.35"/>
    </symbol>

    <symbol id="icon-x" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 6 6 18M6 6l12 12"/>
    </symbol>

    <symbol id="icon-chevron-right" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="m9 18 6-6-6-6"/>
    </symbol>

    <symbol id="icon-menu" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 12h18M3 6h18M3 18h18"/>
    </symbol>

    <symbol id="icon-filter" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
    </symbol>

    <symbol id="icon-book-open" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
    </symbol>

    <symbol id="icon-file-text" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
    </symbol>

    <symbol id="icon-external-link" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
        <polyline points="15 3 21 3 21 9"/>
        <line x1="10" y1="14" x2="21" y2="3"/>
    </symbol>

    <symbol id="icon-columns" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <line x1="12" y1="3" x2="12" y2="21"/>
    </symbol>

    <!-- Category Icons -->
    <symbol id="icon-atom" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="1"/>
        <path d="M20.2 20.2c2.04-2.03.02-7.36-4.5-11.9-4.54-4.52-9.87-6.54-11.9-4.5-2.04 2.03-.02 7.36 4.5 11.9 4.54 4.52 9.87 6.54 11.9 4.5Z"/>
        <path d="M15.7 15.7c4.52-4.54 6.54-9.87 4.5-11.9-2.03-2.04-7.36-.02-11.9 4.5-4.52 4.54-6.54 9.87-4.5 11.9 2.03 2.04 7.36.02 11.9-4.5Z"/>
    </symbol>

    <symbol id="icon-cube" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="m21 16-9 5-9-5V8l9-5 9 5v8z"/>
        <path d="m3 8 9 5 9-5"/>
        <line x1="12" y1="13" x2="12" y2="22"/>
    </symbol>

    <symbol id="icon-lightning" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </symbol>

    <symbol id="icon-dna" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M2 15c6.667-6 13.333 0 20-6"/>
        <path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993"/>
        <path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993"/>
        <path d="m17 6-2.5-2.5"/>
        <path d="m14 8-1-1"/>
        <path d="m7 18 2.5 2.5"/>
        <path d="m3.5 14.5.5.5"/>
        <path d="m20 9 .5.5"/>
        <path d="m6.5 12.5 1 1"/>
        <path d="m16.5 10.5 1 1"/>
        <path d="m10 16 1.5 1.5"/>
    </symbol>

    <symbol id="icon-brain" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-1.54"/>
        <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-1.54"/>
    </symbol>

    <symbol id="icon-globe" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="2" y1="12" x2="22" y2="12"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    </symbol>

    <symbol id="icon-stars" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
        <path d="M5 3v4"/>
        <path d="M19 17v4"/>
        <path d="M3 5h4"/>
        <path d="M17 19h4"/>
    </symbol>

    <symbol id="icon-shield" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    </symbol>

    <symbol id="icon-network" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="5" r="3"/>
        <circle cx="5" cy="19" r="3"/>
        <circle cx="19" cy="19" r="3"/>
        <line x1="12" y1="8" x2="5" y2="16"/>
        <line x1="12" y1="8" x2="19" y2="16"/>
    </symbol>

    <symbol id="icon-heart" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
    </symbol>

    <symbol id="icon-question" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
    </symbol>

    <symbol id="icon-gear" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
    </symbol>

    <symbol id="icon-book" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
    </symbol>

    <symbol id="icon-link" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
    </symbol>

    <!-- Decorative Elements -->
    <symbol id="icon-divider" viewBox="0 0 200 24">
        <path d="M0 12h70M130 12h70" stroke="currentColor" stroke-width="1"/>
        <path d="M80 12l10-8 10 8-10 8z" fill="currentColor"/>
        <circle cx="100" cy="12" r="3" fill="currentColor"/>
        <path d="M110 12l10-8 10 8-10 8z" fill="currentColor"/>
    </symbol>

</svg>
```

---

## 5. Configuration Files

### 5.1 Application Settings

```yaml
# config/settings.yaml

app:
  name: "Knowledge Nexus"
  version: "1.0.0"
  description: "Interactive Knowledge Base Explorer"
  author: "Dennis 'dnoice' Smaltz"

server:
  host: "127.0.0.1"
  port: 8000
  reload: true  # Development mode
  workers: 1

paths:
  articles: "../articles"
  data: "../data"
  static: "../front-end"

cache:
  enabled: true
  ttl_seconds: 3600
  max_size_mb: 100

search:
  index_path: "../data/search_index"
  min_word_length: 2
  fuzzy_distance: 1
  highlight_fragments: 3
  results_per_page: 20

graph:
  output_path: "../data/graph.json"
  min_edge_weight: 0.3
  include_empty_categories: false

markdown:
  extensions:
    - "tables"
    - "fenced_code"
    - "codehilite"
    - "toc"
    - "footnotes"
  code_theme: "monokai"
```

### 5.2 Category Metadata

```yaml
# config/categories.yaml

categories:
  - id: "01-theoretical-frontiers"
    name: "Theoretical Frontiers"
    icon: "atom"
    description: "Foundational questions at the edge of physics and philosophy"
    color: "#8b4513"

  - id: "02-materials-fabrication"
    name: "Materials & Fabrication"
    icon: "cube"
    description: "Advanced materials science and manufacturing techniques"
    color: "#556b2f"

  - id: "03-energy-propulsion"
    name: "Energy & Propulsion"
    icon: "lightning"
    description: "Power generation and advanced propulsion systems"
    color: "#b8860b"

  - id: "04-life-sciences"
    name: "Life Sciences"
    icon: "dna"
    description: "Biology, genetics, and the mechanisms of life"
    color: "#2f4f4f"

  - id: "05-mind-cognition"
    name: "Mind & Cognition"
    icon: "brain"
    description: "Consciousness, neuroscience, and cognitive systems"
    color: "#722f37"

  - id: "06-earth-systems"
    name: "Earth Systems"
    icon: "globe"
    description: "Planetary science and environmental dynamics"
    color: "#556b2f"

  - id: "07-space-cosmos"
    name: "Space & Cosmos"
    icon: "stars"
    description: "Astronomy, cosmology, and space exploration"
    color: "#2f4f4f"

  - id: "08-information-security"
    name: "Information & Security"
    icon: "shield"
    description: "Cybersecurity, cryptography, and information theory"
    color: "#4a3c28"

  - id: "09-systems-civilization"
    name: "Systems & Civilization"
    icon: "network"
    description: "Complex systems, governance, and societal structures"
    color: "#5c4a33"

  - id: "10-human-experience"
    name: "Human Experience"
    icon: "heart"
    description: "Psychology, culture, and the human condition"
    color: "#722f37"

  - id: "11-speculative-fringe"
    name: "Speculative & Fringe"
    icon: "question"
    description: "Edge theories and unconventional ideas"
    color: "#7a6548"

  - id: "12-applied-frontiers"
    name: "Applied Frontiers"
    icon: "gear"
    description: "Practical applications of frontier research"
    color: "#8b4513"

  - id: "13-meta-learning"
    name: "Meta-Learning"
    icon: "book"
    description: "Learning methodologies and knowledge synthesis"
    color: "#4a3c28"

  - id: "14-nexus-points"
    name: "Nexus Points"
    icon: "link"
    description: "Cross-disciplinary intersections and connections"
    color: "#b8860b"
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Week 1-2)

1. Set up project structure
2. Create FastAPI backend skeleton
3. Implement markdown parser with metadata extraction
4. Build basic API endpoints (articles, categories)
5. Create CSS design token system
6. Build base HTML template with parchment theme

### Phase 2: Core Features (Week 3-4)

1. Implement search indexing with Whoosh
2. Build navigation tree component
3. Create article reader with tabbed views
4. Implement split panel layout
5. Add responsive design breakpoints

### Phase 3: Advanced Features (Week 5-6)

1. Build knowledge graph with D3.js
2. Implement faceted search interface
3. Add keyboard navigation and shortcuts
4. Create progressive disclosure sections
5. Performance optimization (lazy loading, caching)

### Phase 4: Polish (Week 7-8)

1. Parchment texture and visual refinements
2. Animation and transition polish
3. Accessibility audit (ARIA, keyboard nav)
4. Cross-browser testing
5. Documentation and deployment scripts

---

## 7. Development Commands

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate on Windows
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Build search index
python scripts/build_index.py

# Generate graph data
python scripts/generate_graph.py

# Frontend development
# Serve static files through FastAPI or use:
python -m http.server 3000 --directory front-end
```

---

## 8. Key Design Decisions

### Why FastAPI?

- Native async support for responsive API
- Automatic OpenAPI documentation
- Pydantic for data validation
- Lightweight and fast startup
- Compatible with your Python environment

### Why Vanilla JS over Framework?

- Smaller bundle size (critical for performance)
- No build step required for development
- Full control over DOM interactions
- Aligns with the scholarly, timeless aesthetic
- Easy to maintain long-term

### Why D3.js for Graph?

- Industry standard for data visualization
- Force-directed layouts work well for knowledge graphs
- Highly customizable for the parchment theme
- Good performance with hundreds of nodes

### Why Whoosh for Search?

- Pure Python (no external dependencies)
- Full-text search with stemming
- Fuzzy matching support
- Fast enough for this scale of content
- Easy to extend and customize

---

> **Signature**: ︻デ═─── ✦ ✦ ✦ | Aim Twice, Shoot Once!
