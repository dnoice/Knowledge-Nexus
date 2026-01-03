"""
Knowledge Graph Builder Service
===============================
Builds the knowledge graph from articles and their relationships.

Author: Dennis 'dnoice' Smaltz
Signature: Aim Twice, Shoot Once!
"""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import networkx as nx

from ..config import get_settings, get_categories
from ..models.graph import (
    GraphNode,
    GraphEdge,
    KnowledgeGraph,
    GraphNeighborhood,
    GraphStatistics,
)

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """
    Builds and manages the knowledge graph for article visualization.

    The graph includes:
    - Category nodes (larger, with icons)
    - Article nodes (smaller, linked to categories)
    - Edges based on:
        - Category membership (article -> category)
        - Shared tags (article <-> article)
        - Cross-references in content (article <-> article)
        - Manual connections (from config)
    """

    # Category colors from config
    DEFAULT_CATEGORY_COLOR = "#8b4513"
    DEFAULT_ARTICLE_COLOR = "#5c4a33"

    # Node sizes
    CATEGORY_NODE_SIZE = 28
    ARTICLE_NODE_SIZE = 14

    def __init__(self):
        self.settings = get_settings()
        self.categories_config = get_categories()
        self.graph = nx.Graph()
        self._category_colors: dict[str, str] = {}
        self._category_icons: dict[str, str] = {}

        self._load_category_styles()

    def _load_category_styles(self) -> None:
        """Load category colors and icons from config."""
        for cat in self.categories_config.categories:
            self._category_colors[cat.id] = cat.color
            self._category_icons[cat.id] = cat.icon

    def build_graph(
        self,
        articles: list[dict],
        manual_connections: Optional[dict] = None
    ) -> KnowledgeGraph:
        """
        Build the complete knowledge graph.

        Args:
            articles: List of article dictionaries
            manual_connections: Optional dict of manual connection definitions

        Returns:
            KnowledgeGraph ready for visualization
        """
        logger.info(f"Building knowledge graph from {len(articles)} articles")

        self.graph.clear()

        # Step 1: Add category nodes
        self._add_category_nodes()

        # Step 2: Add article nodes
        self._add_article_nodes(articles)

        # Step 3: Add category membership edges
        self._add_category_edges(articles)

        # Step 4: Add tag-based connections
        self._add_tag_connections(articles)

        # Step 5: Add cross-reference connections
        self._add_reference_connections(articles)

        # Step 6: Add manual connections
        if manual_connections:
            self._add_manual_connections(manual_connections)

        # Step 7: Filter weak edges
        self._filter_weak_edges()

        # Export to D3 format
        return self._export_graph()

    def _add_category_nodes(self) -> None:
        """Add category nodes to the graph."""
        for cat in self.categories_config.categories:
            self.graph.add_node(
                cat.id,
                type='category',
                label=cat.name,
                description=cat.description,
                size=self.CATEGORY_NODE_SIZE,
                color=cat.color,
                icon=cat.icon,
                category_id=None,
                subcategory=None,
                word_count=None,
            )

    def _add_article_nodes(self, articles: list[dict]) -> None:
        """Add article nodes to the graph."""
        for article in articles:
            category_id = article.get('category_id', '')
            color = self._category_colors.get(category_id, self.DEFAULT_ARTICLE_COLOR)

            # Adjust color brightness for article (slightly lighter)
            adjusted_color = self._adjust_color(color, 0.2)

            self.graph.add_node(
                article['id'],
                type='article',
                label=article.get('title', article['id']),
                description=article.get('description', ''),
                size=self.ARTICLE_NODE_SIZE,
                color=adjusted_color,
                icon='file-text',
                category_id=category_id,
                subcategory=article.get('subcategory', ''),
                word_count=article.get('word_count', 0),
            )

    def _add_category_edges(self, articles: list[dict]) -> None:
        """Add edges from articles to their categories."""
        weight = self.settings.graph.category_connection_weight

        for article in articles:
            category_id = article.get('category_id')
            if category_id and self.graph.has_node(category_id):
                self.graph.add_edge(
                    article['id'],
                    category_id,
                    weight=weight,
                    type='category',
                )

    def _add_tag_connections(self, articles: list[dict]) -> None:
        """Add edges between articles that share tags."""
        weight = self.settings.graph.tag_connection_weight

        # Build tag -> articles mapping
        tag_to_articles: dict[str, list[str]] = defaultdict(list)

        for article in articles:
            for tag in article.get('tags', []):
                tag_lower = tag.lower().strip()
                if tag_lower:
                    tag_to_articles[tag_lower].append(article['id'])

        # Create edges for shared tags
        for tag, article_ids in tag_to_articles.items():
            if len(article_ids) < 2:
                continue

            for i, a1_id in enumerate(article_ids):
                for a2_id in article_ids[i + 1:]:
                    if self.graph.has_edge(a1_id, a2_id):
                        # Strengthen existing edge
                        self.graph[a1_id][a2_id]['weight'] += weight
                    else:
                        # Create new edge
                        self.graph.add_edge(
                            a1_id,
                            a2_id,
                            weight=weight,
                            type='tag',
                        )

    def _add_reference_connections(self, articles: list[dict]) -> None:
        """Add edges based on cross-references in content."""
        weight = self.settings.graph.reference_connection_weight

        # Build title -> id mapping for reference detection
        title_to_id: dict[str, str] = {}
        for article in articles:
            title = article.get('title', '').lower()
            if title:
                title_to_id[title] = article['id']

                # Also add slug-based variants
                slug = article.get('slug', article['id'])
                title_to_id[slug.lower()] = article['id']

        # Search for references in content
        for article in articles:
            content = article.get('content', '').lower()
            article_id = article['id']

            for title, target_id in title_to_id.items():
                if target_id == article_id:
                    continue

                # Check if title appears in content
                if title in content:
                    if self.graph.has_edge(article_id, target_id):
                        self.graph[article_id][target_id]['weight'] += weight
                    else:
                        self.graph.add_edge(
                            article_id,
                            target_id,
                            weight=weight,
                            type='reference',
                        )

    def _add_manual_connections(self, connections: dict) -> None:
        """Add manually defined connections."""
        for source, targets in connections.items():
            if not self.graph.has_node(source):
                continue

            for target in targets:
                if not self.graph.has_node(target):
                    continue

                if self.graph.has_edge(source, target):
                    self.graph[source][target]['weight'] += 2.0
                else:
                    self.graph.add_edge(
                        source,
                        target,
                        weight=2.0,
                        type='manual',
                    )

    def _filter_weak_edges(self) -> None:
        """Remove edges below the minimum weight threshold."""
        min_weight = self.settings.graph.min_edge_weight

        edges_to_remove = [
            (u, v) for u, v, data in self.graph.edges(data=True)
            if data.get('weight', 0) < min_weight
            and data.get('type') != 'category'  # Keep category edges
        ]

        self.graph.remove_edges_from(edges_to_remove)

    def _export_graph(self) -> KnowledgeGraph:
        """Export the graph to D3.js format."""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append(GraphNode(
                id=node_id,
                type=data.get('type', 'article'),
                label=data.get('label', node_id),
                description=data.get('description', ''),
                size=data.get('size', self.ARTICLE_NODE_SIZE),
                color=data.get('color', self.DEFAULT_ARTICLE_COLOR),
                icon=data.get('icon', 'circle'),
                category_id=data.get('category_id'),
                subcategory=data.get('subcategory'),
                word_count=data.get('word_count'),
            ))

        links = []
        for u, v, data in self.graph.edges(data=True):
            links.append(GraphEdge(
                source=u,
                target=v,
                weight=data.get('weight', 1.0),
                type=data.get('type', 'category'),
            ))

        graph = KnowledgeGraph(
            nodes=nodes,
            links=links,
            generated_at=datetime.now().isoformat(),
            version="1.0",
        )

        # Compute statistics
        graph.statistics = graph.compute_statistics()

        return graph

    def get_neighborhood(
        self,
        center_id: str,
        depth: int = 2
    ) -> Optional[GraphNeighborhood]:
        """
        Get the neighborhood subgraph around a specific node.

        Args:
            center_id: The focal node ID
            depth: How many hops from center (1-3)

        Returns:
            GraphNeighborhood or None if center not found
        """
        if not self.graph.has_node(center_id):
            return None

        depth = max(1, min(3, depth))

        # Get nodes within depth hops using BFS
        neighbor_ids = {center_id}
        current_frontier = {center_id}

        for _ in range(depth):
            next_frontier = set()
            for node_id in current_frontier:
                for neighbor in self.graph.neighbors(node_id):
                    if neighbor not in neighbor_ids:
                        next_frontier.add(neighbor)
                        neighbor_ids.add(neighbor)
            current_frontier = next_frontier

        # Build subgraph
        subgraph = self.graph.subgraph(neighbor_ids)

        # Get center node
        center_data = self.graph.nodes[center_id]
        center_node = GraphNode(
            id=center_id,
            type=center_data.get('type', 'article'),
            label=center_data.get('label', center_id),
            description=center_data.get('description', ''),
            size=center_data.get('size', self.ARTICLE_NODE_SIZE),
            color=center_data.get('color', self.DEFAULT_ARTICLE_COLOR),
            icon=center_data.get('icon', 'circle'),
            category_id=center_data.get('category_id'),
            subcategory=center_data.get('subcategory'),
            word_count=center_data.get('word_count'),
        )

        # Build nodes list
        nodes = []
        for node_id, data in subgraph.nodes(data=True):
            nodes.append(GraphNode(
                id=node_id,
                type=data.get('type', 'article'),
                label=data.get('label', node_id),
                description=data.get('description', ''),
                size=data.get('size', self.ARTICLE_NODE_SIZE),
                color=data.get('color', self.DEFAULT_ARTICLE_COLOR),
                icon=data.get('icon', 'circle'),
                category_id=data.get('category_id'),
                subcategory=data.get('subcategory'),
                word_count=data.get('word_count'),
            ))

        # Build links list
        links = []
        for u, v, data in subgraph.edges(data=True):
            links.append(GraphEdge(
                source=u,
                target=v,
                weight=data.get('weight', 1.0),
                type=data.get('type', 'category'),
            ))

        return GraphNeighborhood(
            center_node=center_node,
            nodes=nodes,
            links=links,
            depth=depth,
        )

    def save_graph(self, graph: KnowledgeGraph, path: Optional[Path] = None) -> None:
        """Save the graph to a JSON file."""
        if path is None:
            path = self.settings.data_path / "graph.json"

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(graph.model_dump(), f, indent=2, default=str)

        logger.info(f"Saved knowledge graph to {path}")

    def load_graph(self, path: Optional[Path] = None) -> Optional[KnowledgeGraph]:
        """Load the graph from a JSON file."""
        if path is None:
            path = self.settings.data_path / "graph.json"

        if not path.exists():
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return KnowledgeGraph(**data)

        except Exception as e:
            logger.error(f"Error loading graph: {e}")
            return None

    @staticmethod
    def _adjust_color(hex_color: str, factor: float) -> str:
        """Adjust color brightness."""
        hex_color = hex_color.lstrip('#')

        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            # Lighten
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))

            return f"#{r:02x}{g:02x}{b:02x}"

        except (ValueError, IndexError):
            return hex_color
