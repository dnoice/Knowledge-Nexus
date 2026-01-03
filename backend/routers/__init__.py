"""
API Routers
===========
FastAPI route handlers for the Knowledge Nexus API.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

from .articles import router as articles_router
from .categories import router as categories_router
from .search import router as search_router
from .graph import router as graph_router

__all__ = [
    "articles_router",
    "categories_router",
    "search_router",
    "graph_router",
]
