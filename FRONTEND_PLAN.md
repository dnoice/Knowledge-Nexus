# Knowledge Nexus Front-End Implementation Plan

<!--
✒ Metadata
    - Title: Knowledge Nexus Front-End Plan (digiSpace Edition - v1.0)
    - File Name: FRONTEND_PLAN.md
    - Relative Path: FRONTEND_PLAN.md
    - Artifact Type: docs
    - Version: 1.0.0
    - Date: 2026-01-03
    - Update: Friday, January 03, 2026
    - Author: Dennis 'dnoice' Smaltz
    - A.I. Acknowledgement: Anthropic - Claude Opus 4.5
    - Signature: ︻デ═─── ✦ ✦ ✦ | Aim Twice, Shoot Once!

✒ Description:
    Comprehensive implementation plan for building a robust, beautiful, and intuitive
    front-end solution for the Knowledge Nexus knowledge management system.

✒ Key Features:
    - Feature 1: Python-powered FastAPI backend with full article processing
    - Feature 2: Interactive knowledge graph visualization with D3.js/Cytoscape
    - Feature 3: Full-text search with faceted filtering
    - Feature 4: Responsive, modern UI with dark/light themes
    - Feature 5: Category-based navigation with completion status indicators
    - Feature 6: Article reader with notes and citations sidebar
    - Feature 7: Cross-reference linking between related articles
    - Feature 8: Progress tracking for learning journeys
    - Feature 9: Export capabilities (PDF, Markdown bundles)
    - Feature 10: Real-time article indexing for future content

✒ Other Important Information:
    - Dependencies: Python 3.11+, FastAPI, modern browser
    - Compatible platforms: Windows, Linux, macOS
---------
-->

> **Philosophy:** *"︻デ═─── ✦ ✦ ✦ | Aim Twice, Shoot Once!"*

---

## 📋 Executive Summary

This plan outlines the architecture and implementation strategy for a **Python-powered knowledge exploration platform** that transforms your markdown article collection into an interactive, visually stunning learning experience.

### Core Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Backend API** | FastAPI + Uvicorn | Async performance, auto-docs, Python native |
| **Search Engine** | Whoosh | Full-text search, Python native, no external deps |
| **Graph Engine** | NetworkX + PyVis | Knowledge graph generation and analysis |
| **Markdown Processing** | markdown-it-py + python-frontmatter | Rich parsing with extensions |
| **Frontend Framework** | Vanilla JS + HTMX + Alpine.js | Lightweight, fast, no build step |
| **Visualization** | D3.js + Cytoscape.js | Interactive knowledge graph |
| **Styling** | Tailwind CSS + Custom Design System | Beautiful, responsive, themeable |
| **Icons** | Lucide Icons | Clean, consistent iconography |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE NEXUS                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   Browser    │◄──►│  FastAPI     │◄──►│  File System         │  │
│  │   (UI)       │    │  Backend     │    │  (Markdown Articles) │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│         │                   │                      │                │
│         │                   ▼                      │                │
│         │           ┌──────────────┐               │                │
│         │           │   Services   │               │                │
│         │           ├──────────────┤               │                │
│         │           │ • Parser     │◄──────────────┘                │
│         │           │ • Indexer    │                                │
│         │           │ • Graph      │                                │
│         │           │ • Cache      │                                │
│         │           └──────────────┘                                │
│         │                   │                                       │
│         │                   ▼                                       │
│         │           ┌──────────────┐                                │
│         │           │   Data       │                                │
│         │           ├──────────────┤                                │
│         │           │ • Search Idx │                                │
│         │           │ • Graph JSON │                                │
│         │           │ • Cache      │                                │
│         └──────────►│ • Static     │                                │
│                     └──────────────┘                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Proposed Directory Structure

```
knowledge-nexus/
├── articles/                    # Existing markdown content (unchanged)
│   ├── 01-theoretical-frontiers/
│   ├── 02-materials-fabrication/
│   └── ... (03-14)
│
├── backend/                     # Python FastAPI application
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Configuration management
│   │
│   ├── api/                     # API route handlers
│   │   ├── __init__.py
│   │   ├── articles.py          # Article CRUD endpoints
│   │   ├── categories.py        # Category listing/filtering
│   │   ├── search.py            # Full-text search API
│   │   └── graph.py             # Knowledge graph endpoints
│   │
│   ├── services/                # Business logic
│   │   ├── __init__.py
│   │   ├── article_parser.py    # Markdown parsing + metadata extraction
│   │   ├── search_indexer.py    # Whoosh indexing
│   │   ├── graph_builder.py     # NetworkX graph construction
│   │   ├── cross_referencer.py  # Article linking detection
│   │   └── cache_manager.py     # In-memory caching
│   │
│   ├── models/                  # Pydantic data models
│   │   ├── __init__.py
│   │   ├── article.py
│   │   ├── category.py
│   │   └── search.py
│   │
│   └── utils/                   # Helper utilities
│       ├── __init__.py
│       └── helpers.py
│
├── frontend/                    # Static web assets
│   ├── index.html               # Main SPA shell
│   │
│   ├── css/
│   │   ├── main.css             # Custom styles
│   │   ├── tokens.css           # Design system tokens
│   │   ├── components.css       # Component styles
│   │   ├── graph.css            # Knowledge graph styles
│   │   └── themes/
│   │       ├── light.css
│   │       └── dark.css
│   │
│   ├── js/
│   │   ├── app.js               # Main application
│   │   ├── router.js            # Client-side routing
│   │   ├── store.js             # State management
│   │   │
│   │   ├── components/          # UI components
│   │   │   ├── navigation.js    # Sidebar navigation
│   │   │   ├── article-reader.js
│   │   │   ├── search-interface.js
│   │   │   ├── knowledge-graph.js
│   │   │   ├── category-grid.js
│   │   │   └── progress-tracker.js
│   │   │
│   │   └── utils/
│   │       ├── api-client.js    # Backend API wrapper
│   │       ├── markdown-renderer.js
│   │       └── helpers.js
│   │
│   └── assets/
│       ├── icons/
│       └── images/
│
├── data/                        # Generated data (gitignored)
│   ├── search_index/            # Whoosh search index
│   ├── graph.json               # Computed knowledge graph
│   └── cache/                   # Runtime cache
│
├── scripts/                     # Utility scripts
│   ├── build_index.py           # Rebuild search index
│   ├── generate_graph.py        # Regenerate knowledge graph
│   └── validate_articles.py     # Content validation
│
├── categories.yaml              # Existing category config
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
└── README.md
```

---

## 🎨 UI/UX Design Concept

### Design Principles

1. **Parchment Aesthetic** - Warm, scholarly feel with subtle textures
2. **Information Density** - Show more, scroll less
3. **Progressive Disclosure** - Details on demand
4. **Visual Hierarchy** - Clear content prioritization
5. **Seamless Navigation** - Never lose your place

### Color System (from categories.yaml)

```css
/* Primary Palette */
--color-theoretical:    #6b5b95;  /* Purple - Deep thought */
--color-materials:      #88b04b;  /* Green - Physical world */
--color-energy:         #f7cac9;  /* Coral - Power */
--color-life:           #92a8d1;  /* Blue - Biological */
--color-mind:           #955251;  /* Rust - Cognition */
--color-earth:          #b565a7;  /* Magenta - Planetary */
--color-space:          #009b77;  /* Teal - Cosmic */
--color-infosec:        #dd4124;  /* Red - Security */
--color-systems:        #45b8ac;  /* Teal-green - Civilization */
--color-human:          #efc050;  /* Gold - Experience */
--color-fringe:         #5b5ea6;  /* Indigo - Speculative */
--color-applied:        #9b2335;  /* Dark red - Practical */
--color-meta:           #dfcfbe;  /* Beige - Learning */
--color-nexus:          #55b4b0;  /* Blue-green - Connections */

/* UI Colors */
--bg-primary:           #faf8f5;  /* Warm white */
--bg-secondary:         #f5f2ed;  /* Parchment */
--text-primary:         #2d2a26;  /* Rich black */
--text-secondary:       #5c5954;  /* Warm gray */
--accent:               #c9a227;  /* Scholar's gold */
```

### Page Layouts

#### 1. Home / Dashboard
```
┌────────────────────────────────────────────────────────────────────┐
│  ☰ KNOWLEDGE NEXUS                          🔍 Search    ◐ Theme  │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   Welcome, Scholar                              Learning Progress  │
│   ────────────────                              ─────────────────  │
│   19 of 127 articles complete                   ████░░░░░░ 15%    │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   EXPLORE BY CATEGORY                                              │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                │
│   │ ◈ Theo- │ │ ◆ Mate- │ │ ⚡ Ener-│ │ 🧬 Life │                │
│   │  retical│ │  rials  │ │   gy    │ │ Science │                │
│   │ 11/11 ✓ │ │ 8/9     │ │ 0/8     │ │ 0/10    │                │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘                │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                │
│   │ 🧠 Mind │ │ 🌍 Earth│ │ 🚀 Space│ │ 🔐 Info │                │
│   │ Cognit. │ │ Systems │ │ Cosmos  │ │ Security│                │
│   │ 0/10    │ │ 0/9     │ │ 0/9     │ │ 0/8     │                │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘                │
│   ... (remaining categories)                                       │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   KNOWLEDGE GRAPH                              [Expand Full View]  │
│   ┌────────────────────────────────────────────────────────────┐  │
│   │                    ◉ Quantum                               │  │
│   │               ╱         ╲                                  │  │
│   │          ◉ Time        ◉ Consciousness                     │  │
│   │             │              │                               │  │
│   │          ◉ Origin      ◉ Emergence                         │  │
│   │               ╲         ╱                                  │  │
│   │                  ◉ Information                             │  │
│   └────────────────────────────────────────────────────────────┘  │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   RECENT & RECOMMENDED                                             │
│   ├── Quantum Weirdness         [01-theoretical] ──── Continue →  │
│   ├── Nanomaterials             [02-materials]   ──── Read →      │
│   └── Ancient Materials         [02-materials]   ──── Read →      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### 2. Category View
```
┌────────────────────────────────────────────────────────────────────┐
│  ← Back    01 THEORETICAL FRONTIERS                    🔍 Filter   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   Exploring the deepest questions at the edges of human           │
│   knowledge, where established theories meet their limits.         │
│                                                                    │
│   ████████████████████████████████████████ 11/11 Complete         │
│                                                                    │
├─────────────────────────┬──────────────────────────────────────────┤
│   ARTICLES              │   QUICK PREVIEW                          │
│   ─────────────         │                                          │
│   ✓ Consciousness       │   # Quantum Weirdness                    │
│   ✓ Dark Sector         │                                          │
│   ✓ Emergence           │   > The quantum realm continues to       │
│   ✓ Foundations         │   > defy classical intuition...          │
│   ✓ Infinity & Zero     │                                          │
│   ✓ Information         │   ## Key Topics                          │
│   ✓ Computation Limits  │   • Negative Time Phenomenon             │
│   ✓ Model Breakdowns    │   • Temporal Tsirelson Bound             │
│   ✓ Origin Questions    │   • Room-Temperature Quantum Comm        │
│  [✓ Quantum Weirdness]  │   • Quantum Consciousness                │
│   ✓ Time Problem        │                                          │
│                         │   📄 Main  📝 Notes  📚 Citations        │
│                         │                                          │
│                         │            [Open Article →]              │
└─────────────────────────┴──────────────────────────────────────────┘
```

#### 3. Article Reader
```
┌────────────────────────────────────────────────────────────────────┐
│  ← Category    QUANTUM WEIRDNESS           📄 📝 📚    ◐ Theme    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                                                              │ │
│  │  # Quantum Weirdness                                        │ │
│  │                                                              │ │
│  │  > "The more success the quantum theory has, the sillier   │ │
│  │  > it looks." — Albert Einstein                            │ │
│  │                                                              │ │
│  │  The quantum realm continues to defy classical intuition,  │ │
│  │  with 2024-2025 discoveries pushing the boundaries of...   │ │
│  │                                                              │ │
│  │  ## Table of Contents                                       │ │
│  │  1. Negative Time Phenomenon                                │ │
│  │  2. Temporal Tsirelson Bound Violation                      │ │
│  │  3. Emergent Photons in Quantum Spin Liquids               │ │
│  │  ...                                                        │ │
│  │                                                              │ │
│  │  ## Negative Time Phenomenon                                │ │
│  │                                                              │ │
│  │  In a groundbreaking 2024 study, physicists observed...    │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  ON THIS PAGE          │  RELATED ARTICLES                  │  │
│  │  ─────────────         │  ─────────────────                 │  │
│  │  • Negative Time       │  → Time Problem                    │  │
│  │  • Tsirelson Bound     │  → Consciousness Hard Problem      │  │
│  │  • Spin Liquids        │  → Information as Substrate        │  │
│  │  • Fractional Excitons │  → Foundations That Crack          │  │
│  │  • Room-Temp Quantum   │                                    │  │
│  │  • Metal-Insulator     │  READING PROGRESS                  │  │
│  │  • Two Arrows          │  ████████░░░░░░░ 52%               │  │
│  │  • Consciousness       │                                    │  │
│  │  • Liquid Crystals     │  Est. time: 12 min                 │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### 4. Knowledge Graph (Full View)
```
┌────────────────────────────────────────────────────────────────────┐
│  ← Back    KNOWLEDGE GRAPH                   Filter: [All ▼]  ⟲  │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌────────────────────────────────────────────────────────────┐  │
│   │                                                            │  │
│   │                      ◉ Quantum Weirdness                   │  │
│   │                    ╱   │   ╲                               │  │
│   │         ◉ Time ──┘    │    └── ◉ Consciousness             │  │
│   │            │          │           │                        │  │
│   │         ◉ Origin      │        ◉ Emergence                 │  │
│   │            │          │           │                        │  │
│   │            └──── ◉ Information ───┘                        │  │
│   │                       │                                    │  │
│   │                  ◉ Computation                             │  │
│   │                       │                                    │  │
│   │              ◉ Foundations                                 │  │
│   │                                                            │  │
│   │                 ◉ Dark Sector                              │  │
│   │                       │                                    │  │
│   │              ◉ Model Breakdowns                            │  │
│   │                                                            │  │
│   │   [Drag to pan • Scroll to zoom • Click node for details] │  │
│   └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│   ┌─────────────────┐                                             │
│   │ LEGEND          │   Selected: Quantum Weirdness               │
│   │ ● Complete (19) │   Connections: 5                            │
│   │ ○ Placeholder   │   Category: 01-theoretical-frontiers        │
│   │ ─ Strong link   │                                             │
│   │ ┈ Weak link     │   [View Article →]                          │
│   └─────────────────┘                                             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### 5. Search Interface
```
┌────────────────────────────────────────────────────────────────────┐
│  ☰ KNOWLEDGE NEXUS                                                │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   🔍 ┌────────────────────────────────────────────────────────┐   │
│      │ quantum entanglement                              ⏎    │   │
│      └────────────────────────────────────────────────────────┘   │
│                                                                    │
│   FILTERS                                                         │
│   ┌─────────────────────────────────────────────────────────────┐ │
│   │ Category: [All ▼]  Status: [Complete ▼]  Sort: [Relevance▼]│ │
│   └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│   12 RESULTS for "quantum entanglement"                           │
│   ─────────────────────────────────────                           │
│                                                                    │
│   ┌─────────────────────────────────────────────────────────────┐ │
│   │ ◈ QUANTUM WEIRDNESS                        [01-theoretical] │ │
│   │   ...room-temperature **quantum entanglement** achieved     │ │
│   │   through novel photonic crystal structures...              │ │
│   │   📄 Article  📝 Notes  📚 Citations                        │ │
│   └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│   ┌─────────────────────────────────────────────────────────────┐ │
│   │ ◈ CONSCIOUSNESS HARD PROBLEM               [01-theoretical] │ │
│   │   ...integrated information theory posits that **quantum    │ │
│   │   entanglement** may play a role in conscious experience... │ │
│   │   📄 Article  📝 Notes  📚 Citations                        │ │
│   └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│   ... (more results)                                              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Phases

### Phase 1: Foundation (Backend Core)
**Goal:** Establish the Python backend that powers everything

#### 1.1 Project Scaffolding
- [ ] Create directory structure
- [ ] Set up Python virtual environment
- [ ] Install dependencies (FastAPI, Uvicorn, etc.)
- [ ] Create configuration management

#### 1.2 Article Parser Service
- [ ] Parse markdown files with metadata extraction
- [ ] Extract frontmatter from HTML comments
- [ ] Generate article slugs and URLs
- [ ] Link main articles with notes and citations
- [ ] Detect completion status (content vs placeholder)

#### 1.3 Category Service
- [ ] Load and parse `categories.yaml`
- [ ] Build category hierarchy
- [ ] Calculate completion statistics
- [ ] Generate category metadata

#### 1.4 Data Models
- [ ] Article model (main, notes, citations)
- [ ] Category model with subcategories
- [ ] Search result model
- [ ] Graph node/edge models

### Phase 2: Search & Discovery
**Goal:** Enable finding content efficiently

#### 2.1 Search Indexer
- [ ] Initialize Whoosh index schema
- [ ] Index article content, titles, categories
- [ ] Index personal notes separately
- [ ] Incremental index updates

#### 2.2 Search API
- [ ] Full-text search endpoint
- [ ] Faceted filtering (category, status, date)
- [ ] Search highlighting
- [ ] Relevance ranking

#### 2.3 Cross-Reference Detection
- [ ] Parse internal links between articles
- [ ] Detect conceptual relationships
- [ ] Build article-to-article connections
- [ ] Generate "related articles" suggestions

### Phase 3: Knowledge Graph
**Goal:** Visualize the interconnected knowledge

#### 3.1 Graph Builder
- [ ] Generate NetworkX graph from articles
- [ ] Create nodes for each article
- [ ] Create edges from cross-references
- [ ] Calculate centrality metrics
- [ ] Cluster by category

#### 3.2 Graph Export
- [ ] Export to JSON for D3.js/Cytoscape
- [ ] Generate force-directed layout coordinates
- [ ] Include metadata for visualization
- [ ] Cache generated graph

### Phase 4: Frontend Foundation
**Goal:** Build the UI shell and navigation

#### 4.1 HTML Shell
- [ ] Create index.html SPA container
- [ ] Set up HTMX for dynamic content
- [ ] Set up Alpine.js for reactivity
- [ ] Configure client-side routing

#### 4.2 Design System
- [ ] Define CSS custom properties (tokens)
- [ ] Create component styles
- [ ] Implement light/dark themes
- [ ] Set up responsive breakpoints

#### 4.3 Navigation Components
- [ ] Sidebar category tree
- [ ] Breadcrumb navigation
- [ ] Search bar with autocomplete
- [ ] Theme toggle

### Phase 5: Core Views
**Goal:** Implement main user interfaces

#### 5.1 Home Dashboard
- [ ] Category grid with completion indicators
- [ ] Progress statistics
- [ ] Recent articles
- [ ] Mini knowledge graph preview

#### 5.2 Category View
- [ ] Article list with status indicators
- [ ] Quick preview panel
- [ ] Filtering and sorting
- [ ] Category description

#### 5.3 Article Reader
- [ ] Markdown rendering with syntax highlighting
- [ ] Table of contents sidebar
- [ ] Tab switching (main/notes/citations)
- [ ] Related articles panel
- [ ] Reading progress indicator

#### 5.4 Knowledge Graph View
- [ ] Full interactive graph (Cytoscape.js)
- [ ] Zoom, pan, drag interactions
- [ ] Node click for details
- [ ] Category filtering
- [ ] Legend and controls

#### 5.5 Search Results
- [ ] Result cards with highlights
- [ ] Faceted filters
- [ ] Sorting options
- [ ] Pagination

### Phase 6: Polish & Enhancement
**Goal:** Refine the experience

#### 6.1 Performance
- [ ] Implement caching (articles, search)
- [ ] Lazy load article content
- [ ] Optimize graph rendering
- [ ] Add loading states

#### 6.2 User Experience
- [ ] Keyboard shortcuts
- [ ] Bookmark articles
- [ ] Reading history
- [ ] Progress persistence (localStorage)

#### 6.3 Export Features
- [ ] Export article to PDF
- [ ] Export notes bundle
- [ ] Export knowledge graph as image

---

## 📦 Dependencies

### requirements.txt
```txt
# Web Framework
fastapi>=0.109.0
uvicorn[standard]>=0.25.0
python-multipart>=0.0.6

# Data Validation
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Markdown Processing
markdown>=3.5.0
markdown-it-py>=3.0.0
python-frontmatter>=1.1.0
pygments>=2.17.0

# Search
whoosh>=2.7.4

# Graph Processing
networkx>=3.2.0
pyvis>=0.3.2

# Configuration
pyyaml>=6.0.1
python-slugify>=8.0.1

# Utilities
watchfiles>=0.21.0
rich>=13.7.0
typer>=0.9.0

# Development
pytest>=7.4.0
httpx>=0.26.0
```

---

## 🚀 Quick Start Commands

```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Build search index
python scripts/build_index.py

# Generate knowledge graph
python scripts/generate_graph.py

# Start development server
python run.py
# or
uvicorn backend.main:app --reload --port 8000

# Open browser
# http://localhost:8000
```

---

## 📊 Data Flow

```
                    User Request
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Router                          │
│  /api/articles  /api/categories  /api/search  /api/graph   │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                           │
│  ArticleParser  CategoryService  SearchIndexer  GraphBuilder│
└─────────────────────────────────────────────────────────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Markdown │  │  Whoosh  │  │ NetworkX │
    │  Files   │  │  Index   │  │  Graph   │
    └──────────┘  └──────────┘  └──────────┘
```

---

## 🎯 Success Metrics

| Metric | Target |
|--------|--------|
| Initial page load | < 2 seconds |
| Search response time | < 200ms |
| Graph render time | < 1 second (127 nodes) |
| Mobile responsiveness | Full support |
| Lighthouse score | > 90 |
| Article index build | < 30 seconds |

---

## 🔮 Future Enhancements (Post-MVP)

1. **AI-Powered Features**
   - Semantic search with embeddings
   - Auto-generated article summaries
   - Smart cross-reference suggestions

2. **Collaboration**
   - Multi-user support
   - Annotations and highlights
   - Discussion threads

3. **Learning Features**
   - Spaced repetition flashcards
   - Quiz generation
   - Learning path recommendations

4. **Content Management**
   - Markdown editor integration
   - Draft/publish workflow
   - Version history

---

## ✅ Ready to Begin

This plan provides a complete roadmap from backend foundation to polished UI. The modular approach allows for incremental development while maintaining a clear vision of the end goal.

**Next Steps:**
1. Review and approve this plan
2. Begin Phase 1: Foundation
3. Iterate based on feedback

---

> **︻デ═─── ✦ ✦ ✦ | Aim Twice, Shoot Once!**
