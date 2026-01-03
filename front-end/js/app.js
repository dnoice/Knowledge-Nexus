/**
 * Knowledge Nexus Application
 * ===========================
 * Main application entry point and orchestration.
 *
 * Author: Dennis 'dnoice' Smaltz
 * Signature: Aim Twice, Shoot Once!
 */

import { Router } from './modules/router.js';
import { Store } from './modules/store.js';
import { API } from './modules/api.js';
import { NavigationTree } from './components/navigation-tree.js';
import { ArticleReader } from './components/article-reader.js';
import { SearchInterface } from './components/search-interface.js';
import { KnowledgeGraph } from './components/knowledge-graph.js';
import { UIHelpers } from './utils/ui-helpers.js';
import { EventBus } from './utils/event-bus.js';

/**
 * Main Application Class
 */
class KnowledgeNexusApp {
    constructor() {
        this.store = new Store();
        this.api = new API();
        this.eventBus = new EventBus();
        this.router = null;
        this.components = {};
        this.initialized = false;
    }

    /**
     * Initialize the application
     */
    async init() {
        if (this.initialized) return;

        try {
            // Load SVG sprite
            await this.loadSVGSprite();

            // Initialize router
            this.router = new Router(this);

            // Initialize components
            await this.initializeComponents();

            // Setup global event listeners
            this.setupEventListeners();

            // Load initial data
            await this.loadInitialData();

            // Handle initial route
            this.router.handleRoute();

            // Mark as initialized
            this.initialized = true;

            // Emit ready event
            this.eventBus.emit('app:ready');

            console.log('Knowledge Nexus initialized successfully');
        } catch (error) {
            console.error('Failed to initialize application:', error);
            UIHelpers.showToast('Failed to load application. Please refresh.', 'error');
        }
    }

    /**
     * Load SVG sprite into the document
     */
    async loadSVGSprite() {
        try {
            const response = await fetch('assets/icons/sprite.svg');
            const svgText = await response.text();
            const container = document.getElementById('svg-sprite-container');
            if (container) {
                container.innerHTML = svgText;
            }
        } catch (error) {
            console.warn('Failed to load SVG sprite:', error);
        }
    }

    /**
     * Initialize all components
     */
    async initializeComponents() {
        // Navigation Tree
        this.components.navigationTree = new NavigationTree({
            container: document.getElementById('category-tree'),
            store: this.store,
            api: this.api,
            eventBus: this.eventBus
        });

        // Article Reader
        this.components.articleReader = new ArticleReader({
            container: document.getElementById('view-reader'),
            store: this.store,
            api: this.api,
            eventBus: this.eventBus
        });

        // Search Interface
        this.components.searchInterface = new SearchInterface({
            searchInput: document.getElementById('global-search'),
            suggestionsContainer: document.getElementById('search-suggestions'),
            resultsContainer: document.getElementById('search-results'),
            facetsContainer: document.getElementById('search-facets'),
            store: this.store,
            api: this.api,
            eventBus: this.eventBus
        });

        // Knowledge Graph
        this.components.knowledgeGraph = new KnowledgeGraph({
            container: document.getElementById('knowledge-graph'),
            legendContainer: document.getElementById('graph-legend'),
            infoPanel: document.getElementById('graph-info-panel'),
            store: this.store,
            api: this.api,
            eventBus: this.eventBus
        });

        // Initialize all components
        await Promise.all([
            this.components.navigationTree.init(),
            this.components.searchInterface.init()
        ]);
    }

    /**
     * Setup global event listeners
     */
    setupEventListeners() {
        // Mobile navigation toggle
        const navToggle = document.querySelector('.nav-toggle');
        const appNav = document.getElementById('app-navigation');
        const navOverlay = document.getElementById('nav-overlay');

        if (navToggle) {
            navToggle.addEventListener('click', () => {
                const isOpen = appNav.getAttribute('data-open') === 'true';
                appNav.setAttribute('data-open', !isOpen);
                navOverlay.setAttribute('data-visible', !isOpen);
                navToggle.setAttribute('aria-expanded', !isOpen);
            });
        }

        if (navOverlay) {
            navOverlay.addEventListener('click', () => {
                appNav.setAttribute('data-open', 'false');
                navOverlay.setAttribute('data-visible', 'false');
                navToggle.setAttribute('aria-expanded', 'false');
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+K / Cmd+K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                document.getElementById('global-search')?.focus();
            }

            // Escape to close modals/search
            if (e.key === 'Escape') {
                this.closeActiveModal();
            }
        });

        // Graph toggle button
        const graphToggle = document.getElementById('graph-toggle');
        if (graphToggle) {
            graphToggle.addEventListener('click', () => {
                this.router.navigate('/graph');
            });
        }

        // View toggle button
        const viewToggle = document.getElementById('view-toggle');
        if (viewToggle) {
            viewToggle.addEventListener('click', () => {
                this.toggleViewMode();
            });
        }

        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        // Explore graph button
        const exploreGraph = document.getElementById('explore-graph');
        if (exploreGraph) {
            exploreGraph.addEventListener('click', () => {
                this.router.navigate('/graph');
            });
        }

        // Collapse all categories
        const collapseAll = document.getElementById('collapse-all');
        if (collapseAll) {
            collapseAll.addEventListener('click', () => {
                this.components.navigationTree.collapseAll();
            });
        }

        // Listen for component events
        this.eventBus.on('article:selected', (article) => {
            this.router.navigate(`/article/${article.id}`);
        });

        this.eventBus.on('category:selected', (category) => {
            this.router.navigate(`/category/${category.id}`);
        });

        this.eventBus.on('search:submit', (query) => {
            this.router.navigate(`/search?q=${encodeURIComponent(query)}`);
        });

        this.eventBus.on('graph:node-click', (node) => {
            if (node.type === 'article') {
                this.router.navigate(`/article/${node.id}`);
            } else if (node.type === 'category') {
                this.router.navigate(`/category/${node.id}`);
            }
        });
    }

    /**
     * Load initial data from API
     */
    async loadInitialData() {
        try {
            // Fetch categories and basic stats in parallel
            const [categories, stats] = await Promise.all([
                this.api.getCategories(),
                this.api.getGraphStatistics()
            ]);

            // Store data
            this.store.set('categories', categories);
            this.store.set('stats', stats);

            // Update UI with stats
            this.updateStats(stats);

            // Emit data loaded event
            this.eventBus.emit('data:loaded', { categories, stats });
        } catch (error) {
            console.error('Failed to load initial data:', error);
            throw error;
        }
    }

    /**
     * Update statistics display
     */
    updateStats(stats) {
        const totalArticles = document.getElementById('total-articles');
        const totalCategories = document.getElementById('total-categories');
        const totalConnections = document.getElementById('total-connections');

        if (totalArticles) totalArticles.textContent = stats?.total_nodes || '--';
        if (totalCategories) totalCategories.textContent = stats?.category_count || '--';
        if (totalConnections) totalConnections.textContent = stats?.total_edges || '--';
    }

    /**
     * Show specific view
     */
    showView(viewId) {
        const views = document.querySelectorAll('.view');
        views.forEach(view => {
            view.hidden = view.id !== viewId;
            view.classList.toggle('active', view.id === viewId);
        });

        // Update aside visibility based on view
        const aside = document.getElementById('app-aside');
        if (aside) {
            aside.hidden = !['view-reader'].includes(viewId);
        }
    }

    /**
     * Toggle between list and grid view modes
     */
    toggleViewMode() {
        const currentMode = this.store.get('viewMode') || 'list';
        const newMode = currentMode === 'list' ? 'grid' : 'list';
        this.store.set('viewMode', newMode);
        this.eventBus.emit('viewMode:changed', newMode);

        // Update button icon
        const viewToggle = document.getElementById('view-toggle');
        const icon = viewToggle?.querySelector('use');
        if (icon) {
            icon.setAttribute('href', `assets/icons/sprite.svg#icon-${newMode === 'list' ? 'grid' : 'list'}`);
        }
    }

    /**
     * Toggle color theme
     */
    toggleTheme() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme') || 'parchment';
        const newTheme = currentTheme === 'parchment' ? 'dark' : 'parchment';
        html.setAttribute('data-theme', newTheme);
        this.store.set('theme', newTheme);
        localStorage.setItem('kn-theme', newTheme);
    }

    /**
     * Close active modal
     */
    closeActiveModal() {
        const searchModal = document.getElementById('search-modal');
        if (searchModal && !searchModal.hidden) {
            searchModal.hidden = true;
        }

        // Close mobile nav
        const appNav = document.getElementById('app-navigation');
        const navOverlay = document.getElementById('nav-overlay');
        if (appNav?.getAttribute('data-open') === 'true') {
            appNav.setAttribute('data-open', 'false');
            navOverlay?.setAttribute('data-visible', 'false');
        }
    }

    /**
     * Update breadcrumb navigation
     */
    updateBreadcrumb(items) {
        const breadcrumb = document.getElementById('breadcrumb');
        if (!breadcrumb) return;

        breadcrumb.innerHTML = `
            <li class="breadcrumb-item">
                <a href="/" class="breadcrumb-link">
                    <svg class="icon" aria-hidden="true">
                        <use href="assets/icons/sprite.svg#icon-home"></use>
                    </svg>
                    <span>Home</span>
                </a>
            </li>
            ${items.map((item, index) => `
                <li class="breadcrumb-item">
                    ${index === items.length - 1
                        ? `<span class="breadcrumb-current" aria-current="page">${item.label}</span>`
                        : `<a href="${item.href}" class="breadcrumb-link">${item.label}</a>`
                    }
                </li>
            `).join('')}
        `;

        // Add click handlers for SPA navigation
        breadcrumb.querySelectorAll('.breadcrumb-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.router.navigate(link.getAttribute('href'));
            });
        });
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Restore theme preference
    const savedTheme = localStorage.getItem('kn-theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    }

    // Create and initialize app
    window.knApp = new KnowledgeNexusApp();
    window.knApp.init();
});
