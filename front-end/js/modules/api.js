/**
 * API Client
 * ==========
 * HTTP client for communicating with the Knowledge Nexus backend.
 *
 * Author: Dennis 'dnoice' Smaltz
 * Signature: Aim Twice, Shoot Once!
 */

export class API {
    constructor(baseUrl = '/api') {
        this.baseUrl = baseUrl;
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Make an HTTP request
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise<any>}
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const cacheKey = `${options.method || 'GET'}:${url}`;

        // Check cache for GET requests
        if (!options.method || options.method === 'GET') {
            const cached = this.getFromCache(cacheKey);
            if (cached) return cached;
        }

        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();

            // Cache GET requests
            if (!options.method || options.method === 'GET') {
                this.setInCache(cacheKey, data);
            }

            return data;
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    /**
     * Get cached data
     */
    getFromCache(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;

        if (Date.now() - cached.timestamp > this.cacheTimeout) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    /**
     * Set cached data
     */
    setInCache(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Clear cache
     */
    clearCache() {
        this.cache.clear();
    }

    // =========================================================================
    // ARTICLES API
    // =========================================================================

    /**
     * Get list of articles
     * @param {Object} params - Query parameters
     * @returns {Promise<Article[]>}
     */
    async getArticles(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/articles${queryString ? `?${queryString}` : ''}`);
    }

    /**
     * Get a single article by ID
     * @param {string} id - Article ID
     * @returns {Promise<Article>}
     */
    async getArticle(id) {
        return this.request(`/articles/${encodeURIComponent(id)}`);
    }

    /**
     * Get article notes
     * @param {string} id - Article ID
     * @returns {Promise<string>}
     */
    async getArticleNotes(id) {
        return this.request(`/articles/${encodeURIComponent(id)}/notes`);
    }

    /**
     * Get article citations
     * @param {string} id - Article ID
     * @returns {Promise<string>}
     */
    async getArticleCitations(id) {
        return this.request(`/articles/${encodeURIComponent(id)}/citations`);
    }

    /**
     * Get related articles
     * @param {string} id - Article ID
     * @param {number} limit - Maximum number of related articles
     * @returns {Promise<Article[]>}
     */
    async getRelatedArticles(id, limit = 5) {
        return this.request(`/articles/${encodeURIComponent(id)}/related?limit=${limit}`);
    }

    // =========================================================================
    // CATEGORIES API
    // =========================================================================

    /**
     * Get all categories
     * @returns {Promise<Category[]>}
     */
    async getCategories() {
        return this.request('/categories');
    }

    /**
     * Get category tree
     * @returns {Promise<CategoryTree>}
     */
    async getCategoryTree() {
        return this.request('/categories/tree');
    }

    /**
     * Get a single category
     * @param {string} id - Category ID
     * @returns {Promise<Category>}
     */
    async getCategory(id) {
        return this.request(`/categories/${encodeURIComponent(id)}`);
    }

    // =========================================================================
    // SEARCH API
    // =========================================================================

    /**
     * Perform a search
     * @param {Object} params - Search parameters
     * @returns {Promise<SearchResponse>}
     */
    async search(params) {
        const queryString = new URLSearchParams();

        if (params.query) queryString.set('q', params.query);
        if (params.category) queryString.set('category', params.category);
        if (params.tags) params.tags.forEach(tag => queryString.append('tags', tag));
        if (params.page) queryString.set('page', params.page);
        if (params.limit) queryString.set('limit', params.limit);
        if (params.sort) queryString.set('sort', params.sort);

        return this.request(`/search?${queryString.toString()}`);
    }

    /**
     * Get search suggestions
     * @param {string} query - Partial query
     * @returns {Promise<SearchSuggestion[]>}
     */
    async getSuggestions(query) {
        return this.request(`/search/suggest?q=${encodeURIComponent(query)}`);
    }

    /**
     * Get search facets
     * @returns {Promise<SearchFacets>}
     */
    async getFacets() {
        return this.request('/search/facets');
    }

    /**
     * Trigger search reindex
     * @returns {Promise<void>}
     */
    async reindex() {
        return this.request('/search/reindex', { method: 'POST' });
    }

    // =========================================================================
    // GRAPH API
    // =========================================================================

    /**
     * Get the full knowledge graph
     * @returns {Promise<KnowledgeGraph>}
     */
    async getGraph() {
        return this.request('/graph');
    }

    /**
     * Get neighborhood around a node
     * @param {string} nodeId - Node ID
     * @param {number} depth - Depth of neighborhood
     * @returns {Promise<GraphNeighborhood>}
     */
    async getNeighborhood(nodeId, depth = 2) {
        return this.request(`/graph/neighborhood/${encodeURIComponent(nodeId)}?depth=${depth}`);
    }

    /**
     * Get category subgraph
     * @param {string} categoryId - Category ID
     * @returns {Promise<KnowledgeGraph>}
     */
    async getCategoryGraph(categoryId) {
        return this.request(`/graph/category/${encodeURIComponent(categoryId)}`);
    }

    /**
     * Get graph statistics
     * @returns {Promise<GraphStatistics>}
     */
    async getGraphStatistics() {
        const graph = await this.getGraph();
        return {
            total_nodes: graph?.nodes?.length || 0,
            total_edges: graph?.edges?.length || 0,
            category_count: new Set(graph?.nodes?.map(n => n.category)).size || 0
        };
    }

    /**
     * Rebuild knowledge graph
     * @returns {Promise<void>}
     */
    async rebuildGraph() {
        return this.request('/graph/rebuild', { method: 'POST' });
    }
}
