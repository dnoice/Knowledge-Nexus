"""
Knowledge Graph Models
======================
Data models for the knowledge graph visualization.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, computed_field


class GraphNode(BaseModel):
    """
    A node in the knowledge graph.
    Can represent either a category or an article.
    """
    id: str = Field(..., description="Unique node identifier")
    type: Literal["category", "article"] = Field(
        ...,
        description="Node type"
    )
    label: str = Field(..., description="Display label")
    description: str = Field(default="", description="Node description/tooltip")

    # Visual properties
    size: int = Field(default=15, description="Node radius")
    color: str = Field(default="#5c4a33", description="Node color (hex)")
    icon: str = Field(default="circle", description="Icon identifier")

    # Category-specific
    category_id: Optional[str] = Field(
        default=None,
        description="Parent category ID (for articles)"
    )

    # Article-specific
    subcategory: Optional[str] = Field(
        default=None,
        description="Subcategory slug (for articles)"
    )
    word_count: Optional[int] = Field(
        default=None,
        description="Article word count"
    )

    # Position (can be preset or computed by force simulation)
    x: Optional[float] = Field(default=None, description="X position")
    y: Optional[float] = Field(default=None, description="Y position")
    fx: Optional[float] = Field(default=None, description="Fixed X position")
    fy: Optional[float] = Field(default=None, description="Fixed Y position")

    @computed_field
    @property
    def is_category(self) -> bool:
        """Check if node is a category."""
        return self.type == "category"

    @computed_field
    @property
    def is_article(self) -> bool:
        """Check if node is an article."""
        return self.type == "article"


class GraphEdge(BaseModel):
    """
    An edge (connection) between two nodes in the knowledge graph.
    """
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    weight: float = Field(default=1.0, ge=0, description="Edge strength/weight")
    type: Literal["category", "tag", "reference", "manual"] = Field(
        default="category",
        description="Type of connection"
    )

    # Visual properties
    color: Optional[str] = Field(default=None, description="Edge color override")
    width: Optional[float] = Field(default=None, description="Edge width override")
    dashed: bool = Field(default=False, description="Render as dashed line")

    @computed_field
    @property
    def computed_width(self) -> float:
        """Compute edge width from weight."""
        if self.width is not None:
            return self.width
        return max(1.0, min(5.0, self.weight * 2))


class GraphStatistics(BaseModel):
    """Statistics about the knowledge graph."""
    node_count: int = Field(default=0, description="Total nodes")
    edge_count: int = Field(default=0, description="Total edges")
    category_count: int = Field(default=0, description="Category nodes")
    article_count: int = Field(default=0, description="Article nodes")
    avg_connections: float = Field(default=0.0, description="Average connections per node")
    max_connections: int = Field(default=0, description="Maximum connections on a node")
    density: float = Field(default=0.0, description="Graph density (0-1)")
    connected_components: int = Field(default=1, description="Number of connected components")


class KnowledgeGraph(BaseModel):
    """
    Complete knowledge graph representation.
    Format compatible with D3.js force-directed graph.
    """
    nodes: list[GraphNode] = Field(
        default_factory=list,
        description="Graph nodes"
    )
    links: list[GraphEdge] = Field(
        default_factory=list,
        description="Graph edges (D3 calls them links)"
    )
    statistics: Optional[GraphStatistics] = Field(
        default=None,
        description="Graph statistics"
    )

    # Metadata
    generated_at: Optional[str] = Field(
        default=None,
        description="Generation timestamp"
    )
    version: str = Field(default="1.0", description="Graph format version")

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Find a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_neighbors(self, node_id: str) -> list[str]:
        """Get IDs of neighboring nodes."""
        neighbors = set()
        for edge in self.links:
            if edge.source == node_id:
                neighbors.add(edge.target)
            elif edge.target == node_id:
                neighbors.add(edge.source)
        return list(neighbors)

    def get_edges_for_node(self, node_id: str) -> list[GraphEdge]:
        """Get all edges connected to a node."""
        return [
            edge for edge in self.links
            if edge.source == node_id or edge.target == node_id
        ]

    def compute_statistics(self) -> GraphStatistics:
        """Compute graph statistics."""
        if not self.nodes:
            return GraphStatistics()

        node_count = len(self.nodes)
        edge_count = len(self.links)
        category_count = sum(1 for n in self.nodes if n.type == "category")
        article_count = sum(1 for n in self.nodes if n.type == "article")

        # Count connections per node
        connections = {node.id: 0 for node in self.nodes}
        for edge in self.links:
            connections[edge.source] = connections.get(edge.source, 0) + 1
            connections[edge.target] = connections.get(edge.target, 0) + 1

        connection_counts = list(connections.values())
        avg_connections = sum(connection_counts) / len(connection_counts) if connection_counts else 0
        max_connections = max(connection_counts) if connection_counts else 0

        # Graph density: actual edges / possible edges
        # For undirected graph: 2 * E / (N * (N-1))
        possible_edges = node_count * (node_count - 1) / 2 if node_count > 1 else 1
        density = edge_count / possible_edges if possible_edges > 0 else 0

        return GraphStatistics(
            node_count=node_count,
            edge_count=edge_count,
            category_count=category_count,
            article_count=article_count,
            avg_connections=round(avg_connections, 2),
            max_connections=max_connections,
            density=round(density, 4),
            connected_components=1,  # Simplified; would need proper graph traversal
        )


class GraphNeighborhood(BaseModel):
    """
    A subgraph showing the neighborhood around a specific node.
    Used for focused exploration of connections.
    """
    center_node: GraphNode = Field(..., description="The focal node")
    nodes: list[GraphNode] = Field(
        default_factory=list,
        description="Nodes in the neighborhood"
    )
    links: list[GraphEdge] = Field(
        default_factory=list,
        description="Edges in the neighborhood"
    )
    depth: int = Field(default=1, ge=1, le=3, description="Depth of neighborhood")

    @computed_field
    @property
    def node_count(self) -> int:
        """Total nodes including center."""
        return len(self.nodes)

    @computed_field
    @property
    def direct_connections(self) -> int:
        """Number of direct connections to center node."""
        return sum(
            1 for edge in self.links
            if edge.source == self.center_node.id or edge.target == self.center_node.id
        )


class GraphLayoutConfig(BaseModel):
    """Configuration for graph layout algorithm."""
    force_strength: float = Field(default=-300, description="Repulsion force")
    link_distance: float = Field(default=100, description="Preferred link distance")
    collision_radius: float = Field(default=30, description="Collision detection radius")
    center_x: Optional[float] = Field(default=None, description="Center X coordinate")
    center_y: Optional[float] = Field(default=None, description="Center Y coordinate")
    alpha: float = Field(default=1.0, ge=0, le=1, description="Initial simulation alpha")
    alpha_decay: float = Field(default=0.0228, ge=0, description="Alpha decay rate")
    velocity_decay: float = Field(default=0.4, ge=0, le=1, description="Velocity damping")
