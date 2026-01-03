"""
Graph Router
============
API endpoints for knowledge graph data.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

from typing import Optional

from fastapi import APIRouter, Query, Path, HTTPException

from ..models.graph import KnowledgeGraph, GraphNeighborhood, GraphStatistics
from ..services.graph_builder import KnowledgeGraphBuilder
from ..services.content_loader import get_content_loader
from ..services.cache import get_cache

router = APIRouter(prefix="/api/graph", tags=["graph"])

# Global graph builder instance
_builder: Optional[KnowledgeGraphBuilder] = None


def get_builder() -> KnowledgeGraphBuilder:
    """Get or create the graph builder."""
    global _builder
    if _builder is None:
        _builder = KnowledgeGraphBuilder()
    return _builder


@router.get(
    "",
    response_model=KnowledgeGraph,
    summary="Get Knowledge Graph",
    description="Get the complete knowledge graph for visualization.",
)
async def get_graph(
    rebuild: bool = Query(
        False,
        description="Force rebuild the graph from articles"
    ),
):
    """
    Get the complete knowledge graph.

    The graph includes:
    - Category nodes (larger, with category colors)
    - Article nodes (smaller, linked to categories)
    - Edges based on category membership, shared tags, and cross-references

    The graph format is compatible with D3.js force-directed layouts.
    """
    cache = get_cache()
    builder = get_builder()

    # Try cache first
    if not rebuild:
        cached = cache.get_graph()
        if cached:
            return KnowledgeGraph(**cached)

        # Try loading from file
        graph = builder.load_graph()
        if graph:
            cache.set_graph(graph.model_dump())
            return graph

    # Build fresh graph
    loader = get_content_loader()
    articles = loader.get_all_articles()

    graph = builder.build_graph(articles)

    # Cache and save
    cache.set_graph(graph.model_dump())
    builder.save_graph(graph)

    return graph


@router.get(
    "/neighborhood/{node_id:path}",
    response_model=GraphNeighborhood,
    summary="Get Node Neighborhood",
    description="Get the local graph around a specific node.",
)
async def get_neighborhood(
    node_id: str = Path(
        ...,
        description="Node ID (article ID or category ID)"
    ),
    depth: int = Query(
        2,
        ge=1,
        le=3,
        description="Depth of neighborhood (1-3 hops)"
    ),
):
    """
    Get the neighborhood subgraph around a specific node.

    Useful for focused exploration of connections around
    a single article or category.

    Args:
        node_id: The ID of the center node
        depth: How many hops from center to include (1-3)

    Returns:
        GraphNeighborhood with center node and connected subgraph
    """
    builder = get_builder()

    # Ensure graph is built
    loader = get_content_loader()
    articles = loader.get_all_articles()
    builder.build_graph(articles)

    neighborhood = builder.get_neighborhood(node_id, depth=depth)

    if not neighborhood:
        raise HTTPException(
            status_code=404,
            detail=f"Node not found: {node_id}"
        )

    return neighborhood


@router.get(
    "/categories",
    response_model=KnowledgeGraph,
    summary="Get Category Graph",
    description="Get a simplified graph showing only categories.",
)
async def get_category_graph():
    """
    Get a simplified graph with only category nodes and their
    connections based on shared articles.

    Useful for high-level overview of knowledge domains.
    """
    builder = get_builder()

    # Ensure graph is built
    loader = get_content_loader()
    articles = loader.get_all_articles()
    full_graph = builder.build_graph(articles)

    # Filter to only category nodes
    category_nodes = [
        node for node in full_graph.nodes
        if node.type == "category"
    ]

    # Build category-to-category edges based on shared articles
    category_edges = []
    category_articles: dict[str, set[str]] = {}

    # Map articles to categories
    for article in articles:
        cat_id = article.get('category_id')
        if cat_id:
            if cat_id not in category_articles:
                category_articles[cat_id] = set()
            # Add tags as pseudo-articles for connection detection
            for tag in article.get('tags', []):
                category_articles[cat_id].add(tag)

    # Find categories with shared tags
    cat_ids = list(category_articles.keys())
    for i, cat1 in enumerate(cat_ids):
        for cat2 in cat_ids[i + 1:]:
            shared = category_articles[cat1] & category_articles[cat2]
            if len(shared) >= 2:  # Require at least 2 shared tags
                from ..models.graph import GraphEdge
                category_edges.append(GraphEdge(
                    source=cat1,
                    target=cat2,
                    weight=len(shared) * 0.5,
                    type="tag",
                ))

    return KnowledgeGraph(
        nodes=category_nodes,
        links=category_edges,
        generated_at=full_graph.generated_at,
        version=full_graph.version,
    )


@router.get(
    "/stats",
    response_model=GraphStatistics,
    summary="Get Graph Statistics",
    description="Get statistics about the knowledge graph.",
)
async def get_graph_stats():
    """
    Get statistics about the knowledge graph.

    Returns counts, averages, and connectivity metrics.
    """
    # Get cached graph
    cache = get_cache()
    cached = cache.get_graph()

    if cached:
        graph = KnowledgeGraph(**cached)
    else:
        builder = get_builder()
        loader = get_content_loader()
        articles = loader.get_all_articles()
        graph = builder.build_graph(articles)

    return graph.compute_statistics()


@router.post(
    "/rebuild",
    summary="Rebuild Knowledge Graph",
    description="Rebuild the knowledge graph from all articles.",
)
async def rebuild_graph():
    """
    Rebuild the knowledge graph from all articles.

    This should be called after adding or modifying articles
    to update the graph connections.
    """
    builder = get_builder()
    loader = get_content_loader()
    cache = get_cache()

    # Force reload articles
    loader.load_all(force=True)

    # Get all articles
    articles = loader.get_all_articles()

    # Build graph
    graph = builder.build_graph(articles)

    # Cache and save
    cache.set_graph(graph.model_dump())
    builder.save_graph(graph)

    stats = graph.compute_statistics()

    return {
        "status": "success",
        "nodes": stats.node_count,
        "edges": stats.edge_count,
        "categories": stats.category_count,
        "articles": stats.article_count,
    }
