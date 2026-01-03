/**
 * Client-Side Router
 * ==================
 * SPA routing for Knowledge Nexus with history API support.
 *
 * Author: Dennis 'dnoice' Smaltz
 * Signature: Aim Twice, Shoot Once!
 */

export class Router {
    constructor(app) {
        this.app = app;
        this.routes = new Map();
        this.currentRoute = null;

        // Register routes
        this.registerRoutes();

        // Listen for popstate events
        window.addEventListener('popstate', () => this.handleRoute());

        // Intercept link clicks
        document.addEventListener('click', (e) => this.handleLinkClick(e));
    }

    /**
     * Register all application routes
     */
    registerRoutes() {
        // Home route
        this.routes.set('/', {
            view: 'view-home',
            handler: () => this.handleHome()
        });

        // Category route
        this.routes.set('/category/:id', {
            view: 'view-category',
            handler: (params) => this.handleCategory(params.id)
        });

        // Article route
        this.routes.set('/article/:id', {
            view: 'view-reader',
            handler: (params) => this.handleArticle(params.id)
        });

        // Search route
        this.routes.set('/search', {
            view: 'view-search',
            handler: () => this.handleSearch()
        });

        // Graph route
        this.routes.set('/graph', {
            view: 'view-graph',
            handler: () => this.handleGraph()
        });
    }

    /**
     * Navigate to a path
     */
    navigate(path, replace = false) {
        if (path === this.currentRoute) return;

        if (replace) {
            window.history.replaceState({}, '', path);
        } else {
            window.history.pushState({}, '', path);
        }

        this.handleRoute();
    }

    /**
     * Handle current route
     */
    handleRoute() {
        const path = window.location.pathname;
        const searchParams = new URLSearchParams(window.location.search);

        // Find matching route
        let matchedRoute = null;
        let params = {};

        for (const [pattern, route] of this.routes) {
            const match = this.matchRoute(pattern, path);
            if (match) {
                matchedRoute = route;
                params = match.params;
                break;
            }
        }

        if (!matchedRoute) {
            // Default to home for unknown routes
            matchedRoute = this.routes.get('/');
        }

        // Store current route
        this.currentRoute = path;

        // Show the appropriate view
        this.app.showView(matchedRoute.view);

        // Call route handler
        matchedRoute.handler({ ...params, searchParams });
    }

    /**
     * Match a route pattern against a path
     */
    matchRoute(pattern, path) {
        // Convert pattern to regex
        const paramNames = [];
        const regexPattern = pattern.replace(/:([^/]+)/g, (_, name) => {
            paramNames.push(name);
            return '([^/]+)';
        });

        const regex = new RegExp(`^${regexPattern}$`);
        const match = path.match(regex);

        if (!match) return null;

        // Extract params
        const params = {};
        paramNames.forEach((name, index) => {
            params[name] = decodeURIComponent(match[index + 1]);
        });

        return { params };
    }

    /**
     * Handle link clicks for SPA navigation
     */
    handleLinkClick(e) {
        const link = e.target.closest('a[href]');
        if (!link) return;

        const href = link.getAttribute('href');

        // Skip external links
        if (href.startsWith('http') || href.startsWith('//')) return;

        // Skip special links
        if (href.startsWith('#') || href.startsWith('javascript:')) return;

        // Handle internal links
        e.preventDefault();
        this.navigate(href);
    }

    /**
     * Home route handler
     */
    async handleHome() {
        this.app.updateBreadcrumb([]);

        try {
            // Load featured categories
            const categories = this.app.store.get('categories') || [];
            this.renderFeaturedCategories(categories);

            // Load recent articles
            const articles = await this.app.api.getArticles({ limit: 6, sort: 'date-desc' });
            this.renderRecentArticles(articles);

            // Load mini graph preview
            await this.app.components.knowledgeGraph.renderPreview(
                document.getElementById('graph-preview')
            );
        } catch (error) {
            console.error('Failed to load home view:', error);
        }
    }

    /**
     * Category route handler
     */
    async handleCategory(categoryId) {
        try {
            // Fetch category data
            const category = await this.app.api.getCategory(categoryId);
            if (!category) {
                this.navigate('/');
                return;
            }

            // Update breadcrumb
            this.app.updateBreadcrumb([
                { label: category.name, href: `/category/${categoryId}` }
            ]);

            // Update view content
            this.renderCategoryView(category);

            // Fetch category articles
            const articles = await this.app.api.getArticles({
                category: categoryId,
                limit: 50
            });
            this.renderCategoryArticles(articles);

            // Highlight in navigation
            this.app.eventBus.emit('navigation:highlight', categoryId);
        } catch (error) {
            console.error('Failed to load category:', error);
        }
    }

    /**
     * Article route handler
     */
    async handleArticle(articleId) {
        try {
            // Load article through reader component
            await this.app.components.articleReader.loadArticle(articleId);

            // Get article data for breadcrumb
            const article = this.app.store.get(`article:${articleId}`);
            if (article) {
                this.app.updateBreadcrumb([
                    { label: article.category_name, href: `/category/${article.category}` },
                    { label: article.title, href: `/article/${articleId}` }
                ]);
            }
        } catch (error) {
            console.error('Failed to load article:', error);
        }
    }

    /**
     * Search route handler
     */
    async handleSearch() {
        const searchParams = new URLSearchParams(window.location.search);
        const query = searchParams.get('q') || '';

        this.app.updateBreadcrumb([
            { label: 'Search', href: '/search' }
        ]);

        // Update search input
        const searchInput = document.getElementById('global-search');
        if (searchInput) {
            searchInput.value = query;
        }

        // Update search query display
        const queryDisplay = document.getElementById('search-query');
        if (queryDisplay) {
            queryDisplay.textContent = query;
        }

        // Perform search
        if (query) {
            await this.app.components.searchInterface.performSearch(query);
        }
    }

    /**
     * Graph route handler
     */
    async handleGraph() {
        this.app.updateBreadcrumb([
            { label: 'Knowledge Graph', href: '/graph' }
        ]);

        // Initialize graph visualization
        await this.app.components.knowledgeGraph.init();
        await this.app.components.knowledgeGraph.render();
    }

    /**
     * Render featured categories on home page
     */
    renderFeaturedCategories(categories) {
        const container = document.getElementById('featured-categories');
        if (!container) return;

        container.innerHTML = categories.map(category => `
            <a href="/category/${category.id}" class="category-card parchment-card hover-lift">
                <div class="category-card-icon" style="background-color: ${category.color || 'var(--color-accent-rust)'}20">
                    <svg class="icon icon-lg" aria-hidden="true">
                        <use href="assets/icons/sprite.svg#icon-${category.icon || 'book'}"></use>
                    </svg>
                </div>
                <h3 class="category-card-title">${category.name}</h3>
                <p class="category-card-description">${category.description || ''}</p>
                <span class="category-card-count">${category.article_count || 0} articles</span>
            </a>
        `).join('');
    }

    /**
     * Render recent articles on home page
     */
    renderRecentArticles(articles) {
        const container = document.getElementById('recent-articles');
        if (!container) return;

        container.innerHTML = articles.map(article => `
            <a href="/article/${article.id}" class="article-card parchment-card hover-lift">
                <div class="article-card-header">
                    <span class="badge badge-rust">${article.category_name || article.category}</span>
                    <span class="article-date">${this.formatDate(article.date)}</span>
                </div>
                <h3 class="article-card-title">${article.title}</h3>
                <p class="article-card-excerpt">${article.description || ''}</p>
                <div class="article-card-meta">
                    <span class="reading-time">
                        <svg class="icon" aria-hidden="true">
                            <use href="assets/icons/sprite.svg#icon-clock"></use>
                        </svg>
                        ${article.reading_time || '--'} min read
                    </span>
                </div>
            </a>
        `).join('');
    }

    /**
     * Render category view
     */
    renderCategoryView(category) {
        // Update category header
        document.getElementById('category-title').textContent = category.name;
        document.getElementById('category-description').textContent = category.description || '';

        // Update category icon
        const iconContainer = document.getElementById('category-icon-container');
        if (iconContainer) {
            iconContainer.innerHTML = `
                <svg class="icon icon-xl" aria-hidden="true" style="color: ${category.color || 'var(--color-accent-rust)'}">
                    <use href="assets/icons/sprite.svg#icon-${category.icon || 'book'}"></use>
                </svg>
            `;
        }

        // Update article count
        const countEl = document.getElementById('category-article-count');
        if (countEl) {
            countEl.querySelector('span').textContent = `${category.article_count || 0} articles`;
        }

        // Render subcategories if any
        const subcategoriesContainer = document.getElementById('subcategories-container');
        if (subcategoriesContainer && category.subcategories?.length > 0) {
            subcategoriesContainer.innerHTML = `
                <h2 class="section-title">Subcategories</h2>
                <div class="subcategories-grid">
                    ${category.subcategories.map(sub => `
                        <button class="subcategory-btn" data-subcategory="${sub.id}">
                            ${sub.name}
                            <span class="subcategory-count">${sub.article_count || 0}</span>
                        </button>
                    `).join('')}
                </div>
            `;
        } else {
            subcategoriesContainer.innerHTML = '';
        }
    }

    /**
     * Render category articles
     */
    renderCategoryArticles(articles) {
        const container = document.getElementById('category-articles');
        if (!container) return;

        if (articles.length === 0) {
            container.innerHTML = `
                <div class="empty-state parchment-card">
                    <svg class="icon icon-xl" aria-hidden="true">
                        <use href="assets/icons/sprite.svg#icon-file"></use>
                    </svg>
                    <p>No articles found in this category.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = articles.map(article => `
            <a href="/article/${article.id}" class="article-list-item parchment-card hover-lift">
                <div class="article-list-content">
                    <h3 class="article-list-title">${article.title}</h3>
                    <p class="article-list-excerpt">${article.description || ''}</p>
                    <div class="article-list-meta">
                        ${article.tags?.length > 0 ? `
                            <div class="article-tags">
                                ${article.tags.slice(0, 3).map(tag => `
                                    <span class="badge badge-outline">${tag}</span>
                                `).join('')}
                            </div>
                        ` : ''}
                        <span class="reading-time">
                            <svg class="icon" aria-hidden="true">
                                <use href="assets/icons/sprite.svg#icon-clock"></use>
                            </svg>
                            ${article.reading_time || '--'} min
                        </span>
                    </div>
                </div>
                <svg class="icon article-list-arrow" aria-hidden="true">
                    <use href="assets/icons/sprite.svg#icon-chevron-right"></use>
                </svg>
            </a>
        `).join('');
    }

    /**
     * Format date for display
     */
    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
}
