/**
 * Navigation Tree Component
 * =========================
 * Hierarchical category navigation with expandable tree structure.
 *
 * Author: Dennis 'dnoice' Smaltz
 * Signature: Aim Twice, Shoot Once!
 */

import { UIHelpers } from '../utils/ui-helpers.js';

export class NavigationTree {
    constructor(options) {
        this.container = options.container;
        this.store = options.store;
        this.api = options.api;
        this.eventBus = options.eventBus;

        this.expandedNodes = new Set();
        this.selectedNode = null;
        this.categories = [];
    }

    /**
     * Initialize the navigation tree
     */
    async init() {
        if (!this.container) {
            console.warn('Navigation tree container not found');
            return;
        }

        try {
            // Load categories
            await this.loadCategories();

            // Render the tree
            this.render();

            // Setup event listeners
            this.setupEventListeners();

            // Restore expanded state from localStorage
            this.restoreExpandedState();
        } catch (error) {
            console.error('Failed to initialize navigation tree:', error);
            this.container.innerHTML = UIHelpers.renderEmptyState('Failed to load categories', 'warning');
        }
    }

    /**
     * Load categories from API
     */
    async loadCategories() {
        this.categories = await this.api.getCategoryTree();
        this.store.set('categoryTree', this.categories);
    }

    /**
     * Render the navigation tree
     */
    render() {
        if (!this.categories || this.categories.length === 0) {
            this.container.innerHTML = UIHelpers.renderEmptyState('No categories found', 'folder');
            return;
        }

        this.container.innerHTML = this.renderTree(this.categories);
    }

    /**
     * Render tree recursively
     * @param {Array} nodes - Tree nodes
     * @param {number} level - Nesting level
     * @returns {string} HTML string
     */
    renderTree(nodes, level = 0) {
        return `
            <ul class="nav-tree-list" role="${level === 0 ? 'tree' : 'group'}">
                ${nodes.map(node => this.renderNode(node, level)).join('')}
            </ul>
        `;
    }

    /**
     * Render a single tree node
     * @param {Object} node - Node data
     * @param {number} level - Nesting level
     * @returns {string} HTML string
     */
    renderNode(node, level) {
        const hasChildren = node.subcategories && node.subcategories.length > 0;
        const isExpanded = this.expandedNodes.has(node.id);
        const isSelected = this.selectedNode === node.id;
        const articleCount = node.article_count || 0;

        return `
            <li class="nav-tree-item ${hasChildren ? 'has-children' : ''} ${isExpanded ? 'expanded' : ''}"
                role="treeitem"
                aria-expanded="${hasChildren ? isExpanded : undefined}"
                aria-selected="${isSelected}"
                data-id="${node.id}"
                data-level="${level}">

                <div class="nav-tree-node ${isSelected ? 'selected' : ''}"
                     style="--depth: ${level}">

                    ${hasChildren ? `
                        <button class="nav-tree-toggle"
                                aria-label="${isExpanded ? 'Collapse' : 'Expand'} ${node.name}"
                                data-action="toggle">
                            <svg class="icon nav-toggle-icon" aria-hidden="true">
                                <use href="assets/icons/sprite.svg#icon-chevron-right"></use>
                            </svg>
                        </button>
                    ` : `
                        <span class="nav-tree-spacer"></span>
                    `}

                    <a href="/category/${node.id}"
                       class="nav-tree-link"
                       data-action="navigate">
                        <svg class="icon nav-tree-icon" aria-hidden="true"
                             style="color: ${node.color || 'var(--color-accent-rust)'}">
                            <use href="assets/icons/sprite.svg#icon-${node.icon || 'folder'}"></use>
                        </svg>
                        <span class="nav-tree-label">${UIHelpers.escapeHtml(node.name)}</span>
                        ${articleCount > 0 ? `
                            <span class="nav-tree-count badge badge-sm">${articleCount}</span>
                        ` : ''}
                    </a>
                </div>

                ${hasChildren ? `
                    <div class="nav-tree-children ${isExpanded ? '' : 'collapsed'}">
                        ${this.renderTree(node.subcategories, level + 1)}

                        ${node.articles && node.articles.length > 0 ? `
                            <ul class="nav-tree-articles" role="group">
                                ${node.articles.slice(0, 5).map(article => `
                                    <li class="nav-tree-article" role="treeitem">
                                        <a href="/article/${article.id}"
                                           class="nav-tree-article-link"
                                           data-action="article">
                                            <svg class="icon" aria-hidden="true">
                                                <use href="assets/icons/sprite.svg#icon-file"></use>
                                            </svg>
                                            <span>${UIHelpers.escapeHtml(UIHelpers.truncate(article.title, 40))}</span>
                                        </a>
                                    </li>
                                `).join('')}
                                ${node.articles.length > 5 ? `
                                    <li class="nav-tree-more">
                                        <a href="/category/${node.id}" class="nav-tree-more-link">
                                            +${node.articles.length - 5} more articles
                                        </a>
                                    </li>
                                ` : ''}
                            </ul>
                        ` : ''}
                    </div>
                ` : ''}
            </li>
        `;
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Delegate click events
        this.container.addEventListener('click', (e) => {
            const toggle = e.target.closest('[data-action="toggle"]');
            const navigate = e.target.closest('[data-action="navigate"]');
            const article = e.target.closest('[data-action="article"]');

            if (toggle) {
                e.preventDefault();
                e.stopPropagation();
                const item = toggle.closest('.nav-tree-item');
                this.toggleNode(item.dataset.id);
            } else if (navigate) {
                e.preventDefault();
                const item = navigate.closest('.nav-tree-item');
                this.selectNode(item.dataset.id);
                this.eventBus.emit('category:selected', {
                    id: item.dataset.id
                });
            } else if (article) {
                e.preventDefault();
                const articleId = article.getAttribute('href').split('/').pop();
                this.eventBus.emit('article:selected', { id: articleId });
            }
        });

        // Keyboard navigation
        this.container.addEventListener('keydown', (e) => {
            this.handleKeyboard(e);
        });

        // Listen for external highlight requests
        this.eventBus.on('navigation:highlight', (categoryId) => {
            this.highlightCategory(categoryId);
        });

        // Listen for data reload
        this.eventBus.on('data:loaded', () => {
            this.loadCategories().then(() => this.render());
        });
    }

    /**
     * Toggle a node's expanded state
     * @param {string} nodeId - Node ID
     */
    toggleNode(nodeId) {
        const item = this.container.querySelector(`[data-id="${nodeId}"]`);
        if (!item) return;

        const isExpanded = this.expandedNodes.has(nodeId);

        if (isExpanded) {
            this.expandedNodes.delete(nodeId);
            item.classList.remove('expanded');
            item.setAttribute('aria-expanded', 'false');
            const children = item.querySelector('.nav-tree-children');
            if (children) children.classList.add('collapsed');
        } else {
            this.expandedNodes.add(nodeId);
            item.classList.add('expanded');
            item.setAttribute('aria-expanded', 'true');
            const children = item.querySelector('.nav-tree-children');
            if (children) children.classList.remove('collapsed');
        }

        // Save expanded state
        this.saveExpandedState();
    }

    /**
     * Select a node
     * @param {string} nodeId - Node ID
     */
    selectNode(nodeId) {
        // Remove previous selection
        const previousSelected = this.container.querySelector('.nav-tree-node.selected');
        if (previousSelected) {
            previousSelected.classList.remove('selected');
            previousSelected.closest('.nav-tree-item')?.setAttribute('aria-selected', 'false');
        }

        // Add new selection
        const item = this.container.querySelector(`[data-id="${nodeId}"]`);
        if (item) {
            const node = item.querySelector('.nav-tree-node');
            node?.classList.add('selected');
            item.setAttribute('aria-selected', 'true');
            this.selectedNode = nodeId;

            // Ensure the node is visible by expanding parents
            this.expandParents(nodeId);
        }
    }

    /**
     * Expand all parent nodes of a given node
     * @param {string} nodeId - Node ID
     */
    expandParents(nodeId) {
        const item = this.container.querySelector(`[data-id="${nodeId}"]`);
        if (!item) return;

        let parent = item.parentElement?.closest('.nav-tree-item');
        while (parent) {
            const parentId = parent.dataset.id;
            if (!this.expandedNodes.has(parentId)) {
                this.toggleNode(parentId);
            }
            parent = parent.parentElement?.closest('.nav-tree-item');
        }
    }

    /**
     * Highlight a category (expand parents and select)
     * @param {string} categoryId - Category ID
     */
    highlightCategory(categoryId) {
        this.selectNode(categoryId);

        // Scroll into view
        const item = this.container.querySelector(`[data-id="${categoryId}"]`);
        if (item) {
            UIHelpers.scrollIntoView(item, { block: 'center' });
        }
    }

    /**
     * Collapse all nodes
     */
    collapseAll() {
        this.expandedNodes.clear();
        this.container.querySelectorAll('.nav-tree-item.expanded').forEach(item => {
            item.classList.remove('expanded');
            item.setAttribute('aria-expanded', 'false');
            const children = item.querySelector('.nav-tree-children');
            if (children) children.classList.add('collapsed');
        });
        this.saveExpandedState();
    }

    /**
     * Expand all nodes
     */
    expandAll() {
        this.container.querySelectorAll('.nav-tree-item.has-children').forEach(item => {
            const nodeId = item.dataset.id;
            this.expandedNodes.add(nodeId);
            item.classList.add('expanded');
            item.setAttribute('aria-expanded', 'true');
            const children = item.querySelector('.nav-tree-children');
            if (children) children.classList.remove('collapsed');
        });
        this.saveExpandedState();
    }

    /**
     * Handle keyboard navigation
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleKeyboard(e) {
        const focusedItem = document.activeElement.closest('.nav-tree-item');
        if (!focusedItem) return;

        const nodeId = focusedItem.dataset.id;

        switch (e.key) {
            case 'ArrowRight':
                if (focusedItem.classList.contains('has-children')) {
                    if (!this.expandedNodes.has(nodeId)) {
                        this.toggleNode(nodeId);
                    } else {
                        // Focus first child
                        const firstChild = focusedItem.querySelector('.nav-tree-children .nav-tree-link');
                        firstChild?.focus();
                    }
                }
                e.preventDefault();
                break;

            case 'ArrowLeft':
                if (this.expandedNodes.has(nodeId)) {
                    this.toggleNode(nodeId);
                } else {
                    // Focus parent
                    const parent = focusedItem.parentElement?.closest('.nav-tree-item');
                    const parentLink = parent?.querySelector(':scope > .nav-tree-node .nav-tree-link');
                    parentLink?.focus();
                }
                e.preventDefault();
                break;

            case 'ArrowDown':
                this.focusNextItem(focusedItem);
                e.preventDefault();
                break;

            case 'ArrowUp':
                this.focusPreviousItem(focusedItem);
                e.preventDefault();
                break;

            case 'Enter':
            case ' ':
                const link = focusedItem.querySelector(':scope > .nav-tree-node .nav-tree-link');
                link?.click();
                e.preventDefault();
                break;

            case 'Home':
                const firstItem = this.container.querySelector('.nav-tree-link');
                firstItem?.focus();
                e.preventDefault();
                break;

            case 'End':
                const allItems = this.container.querySelectorAll('.nav-tree-link');
                allItems[allItems.length - 1]?.focus();
                e.preventDefault();
                break;
        }
    }

    /**
     * Focus next visible item
     * @param {Element} currentItem - Current focused item
     */
    focusNextItem(currentItem) {
        const allLinks = Array.from(this.container.querySelectorAll('.nav-tree-link:not(.nav-tree-children.collapsed .nav-tree-link)'));
        const currentLink = currentItem.querySelector(':scope > .nav-tree-node .nav-tree-link');
        const currentIndex = allLinks.indexOf(currentLink);

        if (currentIndex < allLinks.length - 1) {
            allLinks[currentIndex + 1]?.focus();
        }
    }

    /**
     * Focus previous visible item
     * @param {Element} currentItem - Current focused item
     */
    focusPreviousItem(currentItem) {
        const allLinks = Array.from(this.container.querySelectorAll('.nav-tree-link:not(.nav-tree-children.collapsed .nav-tree-link)'));
        const currentLink = currentItem.querySelector(':scope > .nav-tree-node .nav-tree-link');
        const currentIndex = allLinks.indexOf(currentLink);

        if (currentIndex > 0) {
            allLinks[currentIndex - 1]?.focus();
        }
    }

    /**
     * Save expanded state to localStorage
     */
    saveExpandedState() {
        localStorage.setItem('kn-nav-expanded', JSON.stringify([...this.expandedNodes]));
    }

    /**
     * Restore expanded state from localStorage
     */
    restoreExpandedState() {
        try {
            const saved = localStorage.getItem('kn-nav-expanded');
            if (saved) {
                const expanded = JSON.parse(saved);
                expanded.forEach(nodeId => {
                    if (this.container.querySelector(`[data-id="${nodeId}"]`)) {
                        this.expandedNodes.add(nodeId);
                    }
                });
                this.render();
            }
        } catch (error) {
            console.warn('Failed to restore navigation state:', error);
        }
    }

    /**
     * Filter tree by search query
     * @param {string} query - Search query
     */
    filter(query) {
        if (!query) {
            this.render();
            return;
        }

        const lowerQuery = query.toLowerCase();
        this.container.querySelectorAll('.nav-tree-item').forEach(item => {
            const label = item.querySelector('.nav-tree-label')?.textContent.toLowerCase() || '';
            const matches = label.includes(lowerQuery);

            if (matches) {
                item.style.display = '';
                this.expandParents(item.dataset.id);
            } else {
                const hasMatchingChild = item.querySelector(`.nav-tree-item:not([style*="display: none"])`);
                item.style.display = hasMatchingChild ? '' : 'none';
            }
        });
    }

    /**
     * Get category by ID
     * @param {string} categoryId - Category ID
     * @returns {Object|null}
     */
    findCategory(categoryId, nodes = this.categories) {
        for (const node of nodes) {
            if (node.id === categoryId) return node;
            if (node.subcategories) {
                const found = this.findCategory(categoryId, node.subcategories);
                if (found) return found;
            }
        }
        return null;
    }
}
