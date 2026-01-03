/**
 * Search Interface Component
 * ==========================
 * Full-featured search with suggestions, facets, and results.
 *
 * Author: Dennis 'dnoice' Smaltz
 * Signature: Aim Twice, Shoot Once!
 */

import { UIHelpers } from '../utils/ui-helpers.js';

export class SearchInterface {
    constructor(options) {
        this.searchInput = options.searchInput;
        this.suggestionsContainer = options.suggestionsContainer;
        this.resultsContainer = options.resultsContainer;
        this.facetsContainer = options.facetsContainer;
        this.store = options.store;
        this.api = options.api;
        this.eventBus = options.eventBus;

        this.currentQuery = '';
        this.currentPage = 1;
        this.pageSize = 20;
        this.selectedFacets = {
            categories: [],
            tags: [],
            readingTime: []
        };
        this.debounceTimer = null;
        this.suggestionsVisible = false;
        this.selectedSuggestionIndex = -1;
    }

    /**
     * Initialize search interface
     */
    async init() {
        if (!this.searchInput) {
            console.warn('Search input not found');
            return;
        }

        this.setupEventListeners();
        await this.loadFacets();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Search input events
        this.searchInput.addEventListener('input', (e) => {
            this.handleInput(e.target.value);
        });

        this.searchInput.addEventListener('keydown', (e) => {
            this.handleKeydown(e);
        });

        this.searchInput.addEventListener('focus', () => {
            if (this.searchInput.value.length >= 2) {
                this.showSuggestions();
            }
        });

        // Click outside to close suggestions
        document.addEventListener('click', (e) => {
            if (!this.searchInput.contains(e.target) &&
                !this.suggestionsContainer?.contains(e.target)) {
                this.hideSuggestions();
            }
        });

        // Facet changes
        this.facetsContainer?.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox') {
                this.handleFacetChange(e.target);
            }
        });

        // View toggle in results
        document.querySelectorAll('.results-view-toggle button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.toggleResultsView(btn.dataset.view);
            });
        });

        // Sort select
        document.getElementById('sort-select')?.addEventListener('change', (e) => {
            this.performSearch(this.currentQuery, 1, e.target.value);
        });
    }

    /**
     * Handle input changes with debounce
     * @param {string} value - Input value
     */
    handleInput(value) {
        clearTimeout(this.debounceTimer);

        if (value.length < 2) {
            this.hideSuggestions();
            return;
        }

        this.debounceTimer = setTimeout(() => {
            this.fetchSuggestions(value);
        }, 200);
    }

    /**
     * Handle keyboard navigation
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleKeydown(e) {
        if (!this.suggestionsVisible) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.submitSearch(this.searchInput.value);
            }
            return;
        }

        const suggestions = this.suggestionsContainer?.querySelectorAll('.suggestion-item');
        const maxIndex = suggestions?.length - 1 || 0;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedSuggestionIndex = Math.min(
                    this.selectedSuggestionIndex + 1,
                    maxIndex
                );
                this.updateSuggestionSelection(suggestions);
                break;

            case 'ArrowUp':
                e.preventDefault();
                this.selectedSuggestionIndex = Math.max(
                    this.selectedSuggestionIndex - 1,
                    -1
                );
                this.updateSuggestionSelection(suggestions);
                break;

            case 'Enter':
                e.preventDefault();
                if (this.selectedSuggestionIndex >= 0 && suggestions) {
                    suggestions[this.selectedSuggestionIndex].click();
                } else {
                    this.submitSearch(this.searchInput.value);
                }
                break;

            case 'Escape':
                this.hideSuggestions();
                break;
        }
    }

    /**
     * Fetch search suggestions
     * @param {string} query - Search query
     */
    async fetchSuggestions(query) {
        try {
            const suggestions = await this.api.getSuggestions(query);
            this.renderSuggestions(suggestions, query);
        } catch (error) {
            console.error('Failed to fetch suggestions:', error);
        }
    }

    /**
     * Render suggestions dropdown
     * @param {Array} suggestions - Suggestion items
     * @param {string} query - Current query
     */
    renderSuggestions(suggestions, query) {
        if (!this.suggestionsContainer) return;

        if (!suggestions || suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }

        this.suggestionsContainer.innerHTML = `
            <ul class="suggestions-list" role="listbox">
                ${suggestions.map((suggestion, index) => `
                    <li class="suggestion-item ${index === this.selectedSuggestionIndex ? 'selected' : ''}"
                        role="option"
                        data-value="${UIHelpers.escapeHtml(suggestion.text)}"
                        data-type="${suggestion.type || 'text'}">
                        <svg class="icon suggestion-icon" aria-hidden="true">
                            <use href="assets/icons/sprite.svg#icon-${this.getSuggestionIcon(suggestion.type)}"></use>
                        </svg>
                        <div class="suggestion-content">
                            <span class="suggestion-text">
                                ${UIHelpers.highlightMatches(suggestion.text, query)}
                            </span>
                            ${suggestion.category ? `
                                <span class="suggestion-category">${UIHelpers.escapeHtml(suggestion.category)}</span>
                            ` : ''}
                        </div>
                        ${suggestion.type ? `
                            <span class="suggestion-type badge badge-sm">${suggestion.type}</span>
                        ` : ''}
                    </li>
                `).join('')}
            </ul>
        `;

        // Add click handlers
        this.suggestionsContainer.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectSuggestion(item);
            });
        });

        this.showSuggestions();
    }

    /**
     * Get icon for suggestion type
     * @param {string} type - Suggestion type
     * @returns {string}
     */
    getSuggestionIcon(type) {
        const icons = {
            article: 'file',
            category: 'folder',
            tag: 'tag',
            text: 'search'
        };
        return icons[type] || 'search';
    }

    /**
     * Update visual selection in suggestions
     * @param {NodeList} suggestions - Suggestion elements
     */
    updateSuggestionSelection(suggestions) {
        suggestions?.forEach((item, index) => {
            item.classList.toggle('selected', index === this.selectedSuggestionIndex);
        });
    }

    /**
     * Select a suggestion
     * @param {Element} item - Selected suggestion element
     */
    selectSuggestion(item) {
        const value = item.dataset.value;
        const type = item.dataset.type;

        this.searchInput.value = value;
        this.hideSuggestions();

        if (type === 'article') {
            // Navigate directly to article
            this.eventBus.emit('article:selected', { id: value });
        } else if (type === 'category') {
            // Navigate to category
            this.eventBus.emit('category:selected', { id: value });
        } else {
            // Perform search
            this.submitSearch(value);
        }
    }

    /**
     * Show suggestions dropdown
     */
    showSuggestions() {
        if (this.suggestionsContainer) {
            this.suggestionsContainer.hidden = false;
            this.suggestionsVisible = true;
        }
    }

    /**
     * Hide suggestions dropdown
     */
    hideSuggestions() {
        if (this.suggestionsContainer) {
            this.suggestionsContainer.hidden = true;
            this.suggestionsVisible = false;
            this.selectedSuggestionIndex = -1;
        }
    }

    /**
     * Submit search
     * @param {string} query - Search query
     */
    submitSearch(query) {
        if (!query.trim()) return;

        this.hideSuggestions();
        this.eventBus.emit('search:submit', query);
    }

    /**
     * Perform search and display results
     * @param {string} query - Search query
     * @param {number} page - Page number
     * @param {string} sort - Sort option
     */
    async performSearch(query, page = 1, sort = 'relevance') {
        if (!query) return;

        this.currentQuery = query;
        this.currentPage = page;

        // Show loading state
        if (this.resultsContainer) {
            UIHelpers.setLoading(this.resultsContainer, true);
            this.resultsContainer.innerHTML = UIHelpers.renderSkeleton(5);
        }

        try {
            // Build search parameters
            const params = {
                query,
                page,
                limit: this.pageSize,
                sort
            };

            // Add facet filters
            if (this.selectedFacets.categories.length > 0) {
                params.category = this.selectedFacets.categories[0];
            }
            if (this.selectedFacets.tags.length > 0) {
                params.tags = this.selectedFacets.tags;
            }

            // Perform search
            const response = await this.api.search(params);

            // Render results
            this.renderResults(response, query);

            // Update facet counts
            if (response.facets) {
                this.updateFacetCounts(response.facets);
            }

            // Update results count
            const countEl = document.getElementById('results-count');
            if (countEl) {
                countEl.textContent = `${response.total || 0} results`;
            }
        } catch (error) {
            console.error('Search failed:', error);
            this.renderSearchError();
        } finally {
            if (this.resultsContainer) {
                UIHelpers.setLoading(this.resultsContainer, false);
            }
        }
    }

    /**
     * Render search results
     * @param {Object} response - Search response
     * @param {string} query - Search query
     */
    renderResults(response, query) {
        if (!this.resultsContainer) return;

        const results = response.results || [];

        if (results.length === 0) {
            this.resultsContainer.innerHTML = `
                <div class="search-empty parchment-card">
                    <svg class="icon icon-xl" aria-hidden="true">
                        <use href="assets/icons/sprite.svg#icon-search"></use>
                    </svg>
                    <h3>No results found</h3>
                    <p>Try adjusting your search terms or filters.</p>
                    <div class="search-tips">
                        <p>Suggestions:</p>
                        <ul>
                            <li>Check your spelling</li>
                            <li>Try more general keywords</li>
                            <li>Remove some filters</li>
                        </ul>
                    </div>
                </div>
            `;
            return;
        }

        this.resultsContainer.innerHTML = results.map(result => `
            <a href="/article/${result.id}" class="search-result-item parchment-card hover-lift">
                <div class="result-header">
                    <span class="badge badge-rust">${UIHelpers.escapeHtml(result.category_name || result.category)}</span>
                    ${result.score ? `
                        <span class="result-score">
                            <svg class="icon" aria-hidden="true">
                                <use href="assets/icons/sprite.svg#icon-star"></use>
                            </svg>
                            ${Math.round(result.score * 100)}% match
                        </span>
                    ` : ''}
                </div>
                <h3 class="result-title">
                    ${UIHelpers.highlightMatches(result.title, query)}
                </h3>
                ${result.description ? `
                    <p class="result-excerpt">
                        ${UIHelpers.highlightMatches(UIHelpers.truncate(result.description, 200), query)}
                    </p>
                ` : ''}
                ${result.highlights?.length > 0 ? `
                    <div class="result-highlights">
                        ${result.highlights.slice(0, 2).map(h => `
                            <p class="highlight-snippet">...${h}...</p>
                        `).join('')}
                    </div>
                ` : ''}
                <div class="result-meta">
                    ${result.tags?.length > 0 ? `
                        <div class="result-tags">
                            ${result.tags.slice(0, 3).map(tag => `
                                <span class="badge badge-outline badge-sm">${UIHelpers.escapeHtml(tag)}</span>
                            `).join('')}
                        </div>
                    ` : ''}
                    <span class="result-date">${UIHelpers.formatDate(result.date)}</span>
                    <span class="result-reading-time">
                        <svg class="icon" aria-hidden="true">
                            <use href="assets/icons/sprite.svg#icon-clock"></use>
                        </svg>
                        ${UIHelpers.formatReadingTime(result.reading_time)}
                    </span>
                </div>
            </a>
        `).join('');

        // Render pagination
        this.renderPagination(response.total, this.currentPage);
    }

    /**
     * Render pagination controls
     * @param {number} total - Total results
     * @param {number} currentPage - Current page
     */
    renderPagination(total, currentPage) {
        const paginationContainer = document.getElementById('search-pagination');
        if (!paginationContainer) return;

        const totalPages = Math.ceil(total / this.pageSize);
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        const pages = [];
        const maxVisible = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(totalPages, startPage + maxVisible - 1);

        if (endPage - startPage < maxVisible - 1) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            pages.push(i);
        }

        paginationContainer.innerHTML = `
            <nav class="pagination" aria-label="Search results pagination">
                <button class="pagination-btn pagination-prev"
                        ${currentPage === 1 ? 'disabled' : ''}
                        data-page="${currentPage - 1}">
                    <svg class="icon" aria-hidden="true">
                        <use href="assets/icons/sprite.svg#icon-chevron-left"></use>
                    </svg>
                    Previous
                </button>

                <div class="pagination-pages">
                    ${startPage > 1 ? `
                        <button class="pagination-btn" data-page="1">1</button>
                        ${startPage > 2 ? '<span class="pagination-ellipsis">...</span>' : ''}
                    ` : ''}

                    ${pages.map(page => `
                        <button class="pagination-btn ${page === currentPage ? 'active' : ''}"
                                data-page="${page}"
                                ${page === currentPage ? 'aria-current="page"' : ''}>
                            ${page}
                        </button>
                    `).join('')}

                    ${endPage < totalPages ? `
                        ${endPage < totalPages - 1 ? '<span class="pagination-ellipsis">...</span>' : ''}
                        <button class="pagination-btn" data-page="${totalPages}">${totalPages}</button>
                    ` : ''}
                </div>

                <button class="pagination-btn pagination-next"
                        ${currentPage === totalPages ? 'disabled' : ''}
                        data-page="${currentPage + 1}">
                    Next
                    <svg class="icon" aria-hidden="true">
                        <use href="assets/icons/sprite.svg#icon-chevron-right"></use>
                    </svg>
                </button>
            </nav>
        `;

        // Add click handlers
        paginationContainer.querySelectorAll('.pagination-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (!btn.disabled) {
                    this.performSearch(this.currentQuery, parseInt(btn.dataset.page));
                    // Scroll to top of results
                    this.resultsContainer?.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }

    /**
     * Load initial facets
     */
    async loadFacets() {
        if (!this.facetsContainer) return;

        try {
            const facets = await this.api.getFacets();
            this.renderFacets(facets);
        } catch (error) {
            console.error('Failed to load facets:', error);
        }
    }

    /**
     * Render facet filters
     * @param {Object} facets - Facet data
     */
    renderFacets(facets) {
        if (!facets) return;

        // Categories
        const categoriesContainer = document.getElementById('facet-categories');
        if (categoriesContainer && facets.categories) {
            categoriesContainer.innerHTML = facets.categories.map(cat => `
                <label class="facet-option">
                    <input type="checkbox"
                           name="category"
                           value="${UIHelpers.escapeHtml(cat.id)}"
                           ${this.selectedFacets.categories.includes(cat.id) ? 'checked' : ''}>
                    <span class="facet-label">${UIHelpers.escapeHtml(cat.name)}</span>
                    <span class="facet-count">${cat.count}</span>
                </label>
            `).join('');
        }

        // Tags
        const tagsContainer = document.getElementById('facet-tags');
        if (tagsContainer && facets.tags) {
            tagsContainer.innerHTML = facets.tags.slice(0, 15).map(tag => `
                <label class="facet-option">
                    <input type="checkbox"
                           name="tag"
                           value="${UIHelpers.escapeHtml(tag.name)}"
                           ${this.selectedFacets.tags.includes(tag.name) ? 'checked' : ''}>
                    <span class="facet-label">${UIHelpers.escapeHtml(tag.name)}</span>
                    <span class="facet-count">${tag.count}</span>
                </label>
            `).join('');
        }
    }

    /**
     * Handle facet checkbox change
     * @param {HTMLInputElement} checkbox - Changed checkbox
     */
    handleFacetChange(checkbox) {
        const { name, value, checked } = checkbox;

        if (name === 'category') {
            if (checked) {
                this.selectedFacets.categories = [value];
            } else {
                this.selectedFacets.categories = [];
            }
        } else if (name === 'tag') {
            if (checked) {
                this.selectedFacets.tags.push(value);
            } else {
                this.selectedFacets.tags = this.selectedFacets.tags.filter(t => t !== value);
            }
        } else if (name === 'reading-time') {
            if (checked) {
                this.selectedFacets.readingTime.push(value);
            } else {
                this.selectedFacets.readingTime = this.selectedFacets.readingTime.filter(r => r !== value);
            }
        }

        // Re-run search with new filters
        if (this.currentQuery) {
            this.performSearch(this.currentQuery, 1);
        }
    }

    /**
     * Update facet counts based on search results
     * @param {Object} facets - Updated facet data
     */
    updateFacetCounts(facets) {
        // Update category counts
        if (facets.categories) {
            facets.categories.forEach(cat => {
                const countEl = this.facetsContainer?.querySelector(
                    `input[value="${cat.id}"] ~ .facet-count`
                );
                if (countEl) {
                    countEl.textContent = cat.count;
                }
            });
        }
    }

    /**
     * Toggle results view mode
     * @param {string} view - View mode (list or grid)
     */
    toggleResultsView(view) {
        if (!this.resultsContainer) return;

        this.resultsContainer.classList.remove('results-list', 'results-grid');
        this.resultsContainer.classList.add(`results-${view}`);

        // Update button states
        document.querySelectorAll('.results-view-toggle button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });
    }

    /**
     * Render search error
     */
    renderSearchError() {
        if (!this.resultsContainer) return;

        this.resultsContainer.innerHTML = `
            <div class="search-error parchment-card">
                <svg class="icon icon-xl" aria-hidden="true">
                    <use href="assets/icons/sprite.svg#icon-warning"></use>
                </svg>
                <h3>Search Error</h3>
                <p>We couldn't complete your search. Please try again.</p>
                <button class="btn btn-outline" onclick="location.reload()">
                    Retry
                </button>
            </div>
        `;
    }

    /**
     * Clear search
     */
    clearSearch() {
        this.searchInput.value = '';
        this.currentQuery = '';
        this.selectedFacets = { categories: [], tags: [], readingTime: [] };
        this.hideSuggestions();

        // Clear checkboxes
        this.facetsContainer?.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = false;
        });
    }
}
