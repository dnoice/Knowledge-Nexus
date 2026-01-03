/**
 * Knowledge Graph Component
 * =========================
 * Interactive D3.js force-directed graph visualization.
 *
 * Author: Dennis 'dnoice' Smaltz
 * Signature: Aim Twice, Shoot Once!
 */

import { UIHelpers } from '../utils/ui-helpers.js';

export class KnowledgeGraph {
    constructor(options) {
        this.container = options.container;
        this.legendContainer = options.legendContainer;
        this.infoPanel = options.infoPanel;
        this.store = options.store;
        this.api = options.api;
        this.eventBus = options.eventBus;

        this.svg = null;
        this.simulation = null;
        this.graphData = null;
        this.zoom = null;
        this.width = 0;
        this.height = 0;

        // Configuration
        this.config = {
            nodeRadius: {
                category: 24,
                article: 12
            },
            linkDistance: 100,
            chargeStrength: -300,
            collisionRadius: 30,
            colors: {
                default: '#8B7355',
                hover: '#B8860B',
                selected: '#DAA520'
            }
        };

        this.selectedNode = null;
        this.highlightedNodes = new Set();
    }

    /**
     * Initialize the graph
     */
    async init() {
        if (!this.container || typeof d3 === 'undefined') {
            console.warn('Graph container or D3 not available');
            return;
        }

        // Get container dimensions
        this.updateDimensions();

        // Create SVG
        this.createSVG();

        // Setup zoom behavior
        this.setupZoom();

        // Setup resize handler
        this.setupResizeHandler();
    }

    /**
     * Update container dimensions
     */
    updateDimensions() {
        const rect = this.container.getBoundingClientRect();
        this.width = rect.width || 800;
        this.height = rect.height || 600;
    }

    /**
     * Create SVG element
     */
    createSVG() {
        // Clear existing content
        this.container.innerHTML = '';

        // Create SVG
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', `0 0 ${this.width} ${this.height}`)
            .attr('class', 'knowledge-graph-svg');

        // Add defs for gradients and markers
        const defs = this.svg.append('defs');

        // Arrow marker for edges
        defs.append('marker')
            .attr('id', 'arrow')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('fill', 'var(--color-border-medium)')
            .attr('d', 'M0,-5L10,0L0,5');

        // Create main group for zoom
        this.mainGroup = this.svg.append('g')
            .attr('class', 'graph-main-group');

        // Create groups for links and nodes
        this.linksGroup = this.mainGroup.append('g').attr('class', 'links');
        this.nodesGroup = this.mainGroup.append('g').attr('class', 'nodes');
    }

    /**
     * Setup zoom behavior
     */
    setupZoom() {
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.mainGroup.attr('transform', event.transform);
            });

        this.svg.call(this.zoom);

        // Zoom controls
        document.getElementById('graph-zoom-in')?.addEventListener('click', () => {
            this.svg.transition().call(this.zoom.scaleBy, 1.3);
        });

        document.getElementById('graph-zoom-out')?.addEventListener('click', () => {
            this.svg.transition().call(this.zoom.scaleBy, 0.7);
        });

        document.getElementById('graph-reset')?.addEventListener('click', () => {
            this.resetView();
        });
    }

    /**
     * Setup window resize handler
     */
    setupResizeHandler() {
        const resizeObserver = new ResizeObserver(
            UIHelpers.debounce(() => {
                this.updateDimensions();
                if (this.svg) {
                    this.svg.attr('viewBox', `0 0 ${this.width} ${this.height}`);
                }
                if (this.simulation) {
                    this.simulation
                        .force('center', d3.forceCenter(this.width / 2, this.height / 2));
                    this.simulation.alpha(0.3).restart();
                }
            }, 250)
        );

        resizeObserver.observe(this.container);
    }

    /**
     * Load and render the full graph
     */
    async render() {
        // Show loading state
        this.showLoading(true);

        try {
            // Fetch graph data
            this.graphData = await this.api.getGraph();

            if (!this.graphData || !this.graphData.nodes || this.graphData.nodes.length === 0) {
                this.showEmpty();
                return;
            }

            // Process data
            const processedData = this.processData(this.graphData);

            // Create simulation
            this.createSimulation(processedData);

            // Render elements
            this.renderLinks(processedData.links);
            this.renderNodes(processedData.nodes);

            // Render legend
            this.renderLegend(processedData.categories);

            // Setup category filter
            this.setupCategoryFilter(processedData.categories);

            // Hide loading
            this.showLoading(false);

        } catch (error) {
            console.error('Failed to render graph:', error);
            this.showError('Failed to load knowledge graph');
        }
    }

    /**
     * Render a preview graph for home page
     * @param {Element} container - Preview container
     */
    async renderPreview(container) {
        if (!container || typeof d3 === 'undefined') return;

        try {
            // Fetch limited graph data
            const graphData = await this.api.getGraph();
            if (!graphData || !graphData.nodes) return;

            // Limit nodes for preview
            const maxNodes = 30;
            const nodes = graphData.nodes.slice(0, maxNodes);
            const nodeIds = new Set(nodes.map(n => n.id));
            const links = graphData.edges.filter(e =>
                nodeIds.has(e.source) && nodeIds.has(e.target)
            );

            // Create mini SVG
            const width = container.clientWidth || 400;
            const height = 300;

            container.innerHTML = '';

            const svg = d3.select(container)
                .append('svg')
                .attr('width', '100%')
                .attr('height', height)
                .attr('viewBox', `0 0 ${width} ${height}`)
                .attr('class', 'graph-preview-svg');

            const g = svg.append('g');

            // Create simulation
            const simulation = d3.forceSimulation(nodes)
                .force('link', d3.forceLink(links).id(d => d.id).distance(50))
                .force('charge', d3.forceManyBody().strength(-100))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(15));

            // Render links
            const link = g.append('g')
                .attr('class', 'preview-links')
                .selectAll('line')
                .data(links)
                .join('line')
                .attr('stroke', 'var(--color-border-light)')
                .attr('stroke-opacity', 0.6);

            // Render nodes
            const node = g.append('g')
                .attr('class', 'preview-nodes')
                .selectAll('circle')
                .data(nodes)
                .join('circle')
                .attr('r', d => d.type === 'category' ? 10 : 6)
                .attr('fill', d => d.color || 'var(--color-accent-rust)')
                .attr('stroke', 'var(--color-bg-elevated)')
                .attr('stroke-width', 2);

            // Update positions on tick
            simulation.on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);

                node
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);
            });

            // Stop after a bit
            setTimeout(() => simulation.stop(), 3000);

        } catch (error) {
            console.warn('Failed to render graph preview:', error);
        }
    }

    /**
     * Process raw graph data
     * @param {Object} data - Raw graph data
     * @returns {Object} Processed data
     */
    processData(data) {
        const nodes = data.nodes.map(node => ({
            ...node,
            radius: node.type === 'category'
                ? this.config.nodeRadius.category
                : this.config.nodeRadius.article
        }));

        const links = data.edges.map(edge => ({
            source: edge.source,
            target: edge.target,
            type: edge.type || 'related',
            weight: edge.weight || 1
        }));

        // Extract unique categories
        const categories = [...new Set(nodes.filter(n => n.type === 'category').map(n => ({
            id: n.id,
            name: n.label,
            color: n.color
        })))];

        return { nodes, links, categories };
    }

    /**
     * Create force simulation
     * @param {Object} data - Processed data
     */
    createSimulation(data) {
        if (this.simulation) {
            this.simulation.stop();
        }

        this.simulation = d3.forceSimulation(data.nodes)
            .force('link', d3.forceLink(data.links)
                .id(d => d.id)
                .distance(d => {
                    const sourceType = typeof d.source === 'object' ? d.source.type : 'article';
                    const targetType = typeof d.target === 'object' ? d.target.type : 'article';
                    if (sourceType === 'category' || targetType === 'category') {
                        return this.config.linkDistance * 1.5;
                    }
                    return this.config.linkDistance;
                })
            )
            .force('charge', d3.forceManyBody()
                .strength(d => d.type === 'category'
                    ? this.config.chargeStrength * 2
                    : this.config.chargeStrength
                )
            )
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide()
                .radius(d => d.radius + 5)
            )
            .force('x', d3.forceX(this.width / 2).strength(0.05))
            .force('y', d3.forceY(this.height / 2).strength(0.05));

        // Update positions on tick
        this.simulation.on('tick', () => this.ticked());
    }

    /**
     * Render link elements
     * @param {Array} links - Link data
     */
    renderLinks(links) {
        const link = this.linksGroup.selectAll('.graph-link')
            .data(links, d => `${d.source.id || d.source}-${d.target.id || d.target}`)
            .join(
                enter => enter.append('line')
                    .attr('class', 'graph-link')
                    .attr('stroke', 'var(--color-border-medium)')
                    .attr('stroke-opacity', 0.4)
                    .attr('stroke-width', d => Math.max(1, d.weight || 1)),
                update => update,
                exit => exit.remove()
            );

        this.links = link;
    }

    /**
     * Render node elements
     * @param {Array} nodes - Node data
     */
    renderNodes(nodes) {
        const self = this;

        const node = this.nodesGroup.selectAll('.graph-node')
            .data(nodes, d => d.id)
            .join(
                enter => {
                    const g = enter.append('g')
                        .attr('class', d => `graph-node node-${d.type}`)
                        .attr('data-id', d => d.id)
                        .call(this.drag());

                    // Node circle
                    g.append('circle')
                        .attr('r', d => d.radius)
                        .attr('fill', d => d.color || this.config.colors.default)
                        .attr('stroke', 'var(--color-bg-elevated)')
                        .attr('stroke-width', 2)
                        .attr('class', 'node-circle');

                    // Icon for categories
                    g.filter(d => d.type === 'category')
                        .append('text')
                        .attr('class', 'node-icon')
                        .attr('text-anchor', 'middle')
                        .attr('dominant-baseline', 'central')
                        .attr('fill', 'white')
                        .attr('font-size', '14px')
                        .text(d => this.getCategoryIcon(d.icon));

                    // Label
                    g.append('text')
                        .attr('class', 'node-label')
                        .attr('dy', d => d.radius + 14)
                        .attr('text-anchor', 'middle')
                        .attr('fill', 'var(--color-text-secondary)')
                        .attr('font-size', d => d.type === 'category' ? '12px' : '10px')
                        .text(d => UIHelpers.truncate(d.label, 20));

                    return g;
                },
                update => update,
                exit => exit.remove()
            );

        // Event handlers
        node
            .on('mouseover', function(event, d) {
                self.handleNodeHover(d, true);
            })
            .on('mouseout', function(event, d) {
                self.handleNodeHover(d, false);
            })
            .on('click', function(event, d) {
                event.stopPropagation();
                self.handleNodeClick(d);
            });

        this.nodes = node;
    }

    /**
     * Get icon character for category
     * @param {string} iconName - Icon name
     * @returns {string}
     */
    getCategoryIcon(iconName) {
        const icons = {
            'atom': '⚛',
            'cube': '◆',
            'lightning': '⚡',
            'dna': '🧬',
            'brain': '🧠',
            'globe': '🌐',
            'stars': '✦',
            'shield': '🛡',
            'network': '⬡',
            'heart': '♥',
            'question': '?',
            'gear': '⚙',
            'book': '📖',
            'link': '🔗'
        };
        return icons[iconName] || '◉';
    }

    /**
     * Create drag behavior
     */
    drag() {
        const simulation = this.simulation;

        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }

    /**
     * Update positions on simulation tick
     */
    ticked() {
        if (this.links) {
            this.links
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
        }

        if (this.nodes) {
            this.nodes.attr('transform', d => `translate(${d.x},${d.y})`);
        }
    }

    /**
     * Handle node hover
     * @param {Object} node - Hovered node
     * @param {boolean} isHover - Is hovering
     */
    handleNodeHover(node, isHover) {
        if (isHover) {
            // Highlight connected nodes
            this.highlightConnected(node);
        } else {
            // Reset highlights
            this.resetHighlight();
        }
    }

    /**
     * Highlight connected nodes
     * @param {Object} node - Selected node
     */
    highlightConnected(node) {
        const connectedIds = new Set([node.id]);

        // Find connected nodes
        if (this.graphData?.edges) {
            this.graphData.edges.forEach(edge => {
                if (edge.source === node.id || edge.source.id === node.id) {
                    connectedIds.add(edge.target.id || edge.target);
                }
                if (edge.target === node.id || edge.target.id === node.id) {
                    connectedIds.add(edge.source.id || edge.source);
                }
            });
        }

        // Dim non-connected nodes
        this.nodes?.classed('dimmed', d => !connectedIds.has(d.id));
        this.links?.classed('dimmed', d => {
            const sourceId = d.source.id || d.source;
            const targetId = d.target.id || d.target;
            return sourceId !== node.id && targetId !== node.id;
        });

        // Highlight connected nodes
        this.nodes?.classed('highlighted', d => connectedIds.has(d.id) && d.id !== node.id);
    }

    /**
     * Reset node highlighting
     */
    resetHighlight() {
        this.nodes?.classed('dimmed', false).classed('highlighted', false);
        this.links?.classed('dimmed', false);
    }

    /**
     * Handle node click
     * @param {Object} node - Clicked node
     */
    handleNodeClick(node) {
        this.selectedNode = node;

        // Show info panel
        this.showNodeInfo(node);

        // Emit event
        this.eventBus.emit('graph:node-click', node);
    }

    /**
     * Show node info panel
     * @param {Object} node - Node data
     */
    showNodeInfo(node) {
        if (!this.infoPanel) return;

        const infoContent = document.getElementById('node-info');
        if (!infoContent) return;

        infoContent.innerHTML = `
            <div class="node-info-header">
                <div class="node-info-icon" style="background-color: ${node.color || this.config.colors.default}">
                    <span>${node.type === 'category' ? this.getCategoryIcon(node.icon) : '📄'}</span>
                </div>
                <div>
                    <h3 class="node-info-title">${UIHelpers.escapeHtml(node.label)}</h3>
                    <span class="node-info-type badge badge-sm">${node.type}</span>
                </div>
            </div>
            ${node.description ? `
                <p class="node-info-description">${UIHelpers.escapeHtml(node.description)}</p>
            ` : ''}
            <div class="node-info-actions">
                <button class="btn btn-primary btn-sm" id="node-view-btn">
                    ${node.type === 'category' ? 'View Category' : 'Read Article'}
                </button>
                <button class="btn btn-outline btn-sm" id="node-focus-btn">
                    Focus View
                </button>
            </div>
        `;

        // Setup action handlers
        document.getElementById('node-view-btn')?.addEventListener('click', () => {
            if (node.type === 'category') {
                this.eventBus.emit('category:selected', { id: node.id });
            } else {
                this.eventBus.emit('article:selected', { id: node.id });
            }
        });

        document.getElementById('node-focus-btn')?.addEventListener('click', () => {
            this.focusOnNode(node);
        });

        // Close button
        this.infoPanel.querySelector('.panel-close')?.addEventListener('click', () => {
            this.infoPanel.hidden = true;
        });

        this.infoPanel.hidden = false;
    }

    /**
     * Focus view on a specific node
     * @param {Object} node - Node to focus on
     */
    focusOnNode(node) {
        const scale = 2;
        const x = this.width / 2 - node.x * scale;
        const y = this.height / 2 - node.y * scale;

        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, d3.zoomIdentity.translate(x, y).scale(scale));
    }

    /**
     * Reset view to default
     */
    resetView() {
        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, d3.zoomIdentity);
    }

    /**
     * Render legend
     * @param {Array} categories - Category data
     */
    renderLegend(categories) {
        if (!this.legendContainer) return;

        this.legendContainer.innerHTML = `
            <div class="legend-items">
                ${categories.map(cat => `
                    <div class="legend-item" data-category="${cat.id}">
                        <span class="legend-color" style="background-color: ${cat.color || this.config.colors.default}"></span>
                        <span class="legend-label">${UIHelpers.escapeHtml(cat.name)}</span>
                    </div>
                `).join('')}
            </div>
        `;

        // Legend item click to filter
        this.legendContainer.querySelectorAll('.legend-item').forEach(item => {
            item.addEventListener('click', () => {
                this.filterByCategory(item.dataset.category);
            });
        });
    }

    /**
     * Setup category filter dropdown
     * @param {Array} categories - Category data
     */
    setupCategoryFilter(categories) {
        const filter = document.getElementById('graph-category-filter');
        if (!filter) return;

        filter.innerHTML = `
            <option value="">All Categories</option>
            ${categories.map(cat => `
                <option value="${cat.id}">${UIHelpers.escapeHtml(cat.name)}</option>
            `).join('')}
        `;

        filter.addEventListener('change', (e) => {
            this.filterByCategory(e.target.value);
        });
    }

    /**
     * Filter graph by category
     * @param {string} categoryId - Category ID to filter
     */
    filterByCategory(categoryId) {
        if (!categoryId) {
            // Show all
            this.nodes?.classed('filtered-out', false);
            this.links?.classed('filtered-out', false);
            return;
        }

        // Get nodes in category
        const categoryNodes = new Set([categoryId]);
        this.graphData?.nodes.forEach(node => {
            if (node.category === categoryId) {
                categoryNodes.add(node.id);
            }
        });

        // Filter nodes
        this.nodes?.classed('filtered-out', d => !categoryNodes.has(d.id));

        // Filter links
        this.links?.classed('filtered-out', d => {
            const sourceId = d.source.id || d.source;
            const targetId = d.target.id || d.target;
            return !categoryNodes.has(sourceId) || !categoryNodes.has(targetId);
        });
    }

    /**
     * Show loading state
     * @param {boolean} loading - Is loading
     */
    showLoading(loading) {
        const loadingEl = this.container.querySelector('.graph-loading');
        if (loadingEl) {
            loadingEl.style.display = loading ? 'flex' : 'none';
        }
    }

    /**
     * Show empty state
     */
    showEmpty() {
        this.container.innerHTML = `
            <div class="graph-empty parchment-card">
                <svg class="icon icon-xl" aria-hidden="true">
                    <use href="assets/icons/sprite.svg#icon-network"></use>
                </svg>
                <h3>No Knowledge Graph Data</h3>
                <p>Add some articles to build your knowledge graph.</p>
            </div>
        `;
    }

    /**
     * Show error state
     * @param {string} message - Error message
     */
    showError(message) {
        this.container.innerHTML = `
            <div class="graph-error parchment-card">
                <svg class="icon icon-xl" aria-hidden="true">
                    <use href="assets/icons/sprite.svg#icon-warning"></use>
                </svg>
                <h3>Error Loading Graph</h3>
                <p>${UIHelpers.escapeHtml(message)}</p>
                <button class="btn btn-outline" onclick="location.reload()">
                    Retry
                </button>
            </div>
        `;
    }

    /**
     * Clean up resources
     */
    destroy() {
        if (this.simulation) {
            this.simulation.stop();
        }
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}
