"""
Knowledge Nexus API
===================
FastAPI backend for the Knowledge Nexus knowledge base explorer.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!

Run with:
    uvicorn backend.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .config import get_settings, get_project_root
from .routers import (
    articles_router,
    categories_router,
    search_router,
    graph_router,
)
from .services.content_loader import get_content_loader
from .services.indexer import SearchIndexer
from .services.graph_builder import KnowledgeGraphBuilder
from .services.cache import get_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    settings = get_settings()
    logger.info(f"Starting {settings.app.name} v{settings.app.version}")

    # Startup: Load content and build indexes
    loader = get_content_loader()
    article_count = loader.load_all()
    logger.info(f"Loaded {article_count} articles")

    if settings.cache.preload_on_startup:
        # Build search index
        indexer = SearchIndexer()
        articles = loader.get_all_articles()
        indexer.build_index(articles)
        logger.info("Search index built")

        # Build knowledge graph
        builder = KnowledgeGraphBuilder()
        graph = builder.build_graph(articles)
        builder.save_graph(graph)
        logger.info(f"Knowledge graph built: {graph.statistics.node_count} nodes, {graph.statistics.edge_count} edges")

    yield

    # Shutdown
    logger.info("Shutting down...")
    cache = get_cache()
    cache.clear()


# Create FastAPI application
settings = get_settings()

app = FastAPI(
    title=settings.app.name,
    description=settings.app.description,
    version=settings.app.version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(articles_router)
app.include_router(categories_router)
app.include_router(search_router)
app.include_router(graph_router)


# Mount static files
static_path = settings.static_path
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# =============================================================================
# Root endpoints
# =============================================================================

@app.get("/api", tags=["meta"])
async def api_root():
    """API root - returns API information."""
    return {
        "name": settings.app.name,
        "version": settings.app.version,
        "description": settings.app.description,
        "author": settings.app.author,
        "signature": settings.app.signature,
        "endpoints": {
            "articles": "/api/articles",
            "categories": "/api/categories",
            "search": "/api/search",
            "graph": "/api/graph",
            "docs": "/api/docs",
        },
    }


@app.get("/api/health", tags=["meta"])
async def health_check():
    """Health check endpoint."""
    cache = get_cache()
    cache_stats = cache.get_stats()

    loader = get_content_loader()

    return {
        "status": "healthy",
        "articles_loaded": len(loader._articles),
        "cache": cache_stats,
    }


@app.get("/api/stats", tags=["meta"])
async def get_stats():
    """Get application statistics."""
    loader = get_content_loader()
    tree = loader.get_category_tree()

    return {
        "total_categories": tree.total_categories,
        "total_subcategories": tree.total_subcategories,
        "total_articles": tree.total_articles,
        "categories": [
            {
                "id": cat.id,
                "name": cat.name,
                "article_count": cat.article_count,
            }
            for cat in tree.categories
        ],
    }


# =============================================================================
# SPA fallback - serve index.html for client-side routing
# =============================================================================

@app.get("/", tags=["frontend"])
async def serve_spa():
    """Serve the main SPA entry point."""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(
        status_code=200,
        content={
            "message": "Welcome to Knowledge Nexus API",
            "docs": "/api/docs",
        }
    )


@app.get("/{full_path:path}", tags=["frontend"])
async def spa_fallback(full_path: str):
    """
    SPA fallback - serve index.html for client-side routing.
    API routes are handled by routers above.
    """
    # Skip API routes
    if full_path.startswith("api/"):
        return JSONResponse(
            status_code=404,
            content={"detail": "Not found"}
        )

    # Try to serve static file
    file_path = static_path / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))

    # Fallback to index.html for SPA routing
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

    return JSONResponse(
        status_code=404,
        content={"detail": "Not found"}
    )


# =============================================================================
# Error handlers
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.server.reload else "An error occurred",
        }
    )


# =============================================================================
# CLI entry point
# =============================================================================

def run():
    """Run the development server."""
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
    )


if __name__ == "__main__":
    run()
