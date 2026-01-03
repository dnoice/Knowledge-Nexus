/**
 * Article Reader Component
 * ========================
 * Multi-panel article reader with tabs, notes, and citations.
 *
 * Author: Dennis 'dnoice' Smaltz
 * Signature: Aim Twice, Shoot Once!
 */

import { UIHelpers } from '../utils/ui-helpers.js';

export class ArticleReader {
    constructor(options) {
        this.container = options.container;
        this.store = options.store;
        this.api = options.api;
        this.eventBus = options.eventBus;

        this.currentArticle = null;
        this.panels = [];
        this.activeTab = 'content';
        this.tocObserver = null;
    }

    /**
     * Initialize the reader
     */
    init() {
        if (!this.container) {
            console.warn('Article reader container not found');
            return;
        }

        this.setupEventListeners();
    }

    /**
     * Load and display an article
     * @param {string} articleId - Article ID
     */
    async loadArticle(articleId) {
        if (!this.container) return;

        // Show loading state
        UIHelpers.setLoading(this.container, true);
        this.container.querySelector('.article-body')?.innerHTML = UIHelpers.renderSkeleton(5);

        try {
            // Fetch article data
            const article = await this.api.getArticle(articleId);

            if (!article) {
                throw new Error('Article not found');
            }

            // Store article
            this.currentArticle = article;
            this.store.set(`article:${articleId}`, article);

            // Render article
            this.renderArticle(article);

            // Load related content in parallel
            await Promise.all([
                this.loadNotes(articleId),
                this.loadCitations(articleId),
                this.loadRelatedArticles(articleId),
                this.loadTableOfContents(article)
            ]);

            // Emit article loaded event
            this.eventBus.emit('article:loaded', article);
        } catch (error) {
            console.error('Failed to load article:', error);
            this.renderError('Failed to load article. Please try again.');
        } finally {
            UIHelpers.setLoading(this.container, false);
        }
    }

    /**
     * Render article content
     * @param {Object} article - Article data
     */
    renderArticle(article) {
        // Update metadata
        const categoryEl = document.getElementById('article-category');
        if (categoryEl) {
            categoryEl.textContent = article.category_name || article.category;
        }

        const dateEl = document.getElementById('article-date');
        if (dateEl) {
            dateEl.textContent = UIHelpers.formatDate(article.date);
        }

        const readingTimeEl = document.getElementById('article-reading-time');
        if (readingTimeEl) {
            readingTimeEl.querySelector('span').textContent =
                `${UIHelpers.formatReadingTime(article.reading_time)} read`;
        }

        const titleEl = document.getElementById('article-title');
        if (titleEl) {
            titleEl.textContent = article.title;
        }

        const descriptionEl = document.getElementById('article-description');
        if (descriptionEl) {
            descriptionEl.textContent = article.description || '';
        }

        // Render tags
        const tagsEl = document.getElementById('article-tags');
        if (tagsEl && article.tags?.length > 0) {
            tagsEl.innerHTML = article.tags.map(tag => `
                <button class="badge badge-outline tag-btn" data-tag="${UIHelpers.escapeHtml(tag)}">
                    ${UIHelpers.escapeHtml(tag)}
                </button>
            `).join('');
        }

        // Render body content
        const bodyEl = document.getElementById('article-body');
        if (bodyEl && article.content_html) {
            bodyEl.innerHTML = this.sanitizeHtml(article.content_html);

            // Add syntax highlighting to code blocks
            this.highlightCodeBlocks(bodyEl);

            // Add anchor links to headings
            this.addHeadingAnchors(bodyEl);

            // Add image lazy loading
            this.setupLazyImages(bodyEl);
        }

        // Update document title
        document.title = `${article.title} - Knowledge Nexus`;
    }

    /**
     * Load article notes
     * @param {string} articleId - Article ID
     */
    async loadNotes(articleId) {
        const notesContainer = document.getElementById('article-notes');
        if (!notesContainer) return;

        try {
            const notes = await this.api.getArticleNotes(articleId);
            if (notes && notes.content_html) {
                notesContainer.innerHTML = this.sanitizeHtml(notes.content_html);
            } else {
                notesContainer.innerHTML = `
                    <div class="empty-state-inline">
                        <svg class="icon" aria-hidden="true">
                            <use href="assets/icons/sprite.svg#icon-file"></use>
                        </svg>
                        <span>No personal notes available for this article.</span>
                    </div>
                `;
            }
        } catch (error) {
            console.warn('Failed to load notes:', error);
            notesContainer.innerHTML = '';
        }
    }

    /**
     * Load article citations
     * @param {string} articleId - Article ID
     */
    async loadCitations(articleId) {
        const citationsContainer = document.getElementById('article-citations');
        if (!citationsContainer) return;

        try {
            const citations = await this.api.getArticleCitations(articleId);
            if (citations && citations.content_html) {
                citationsContainer.innerHTML = `
                    <div class="citations-content prose">
                        ${this.sanitizeHtml(citations.content_html)}
                    </div>
                `;
            } else {
                citationsContainer.innerHTML = `
                    <div class="empty-state-inline">
                        <svg class="icon" aria-hidden="true">
                            <use href="assets/icons/sprite.svg#icon-book"></use>
                        </svg>
                        <span>No citations available for this article.</span>
                    </div>
                `;
            }
        } catch (error) {
            console.warn('Failed to load citations:', error);
            citationsContainer.innerHTML = '';
        }
    }

    /**
     * Load related articles
     * @param {string} articleId - Article ID
     */
    async loadRelatedArticles(articleId) {
        const relatedContainer = document.getElementById('related-list');
        if (!relatedContainer) return;

        try {
            const related = await this.api.getRelatedArticles(articleId, 5);
            if (related && related.length > 0) {
                relatedContainer.innerHTML = related.map(article => `
                    <li class="related-item">
                        <a href="/article/${article.id}" class="related-link">
                            <span class="related-title">${UIHelpers.escapeHtml(article.title)}</span>
                            <span class="related-category">${UIHelpers.escapeHtml(article.category_name || article.category)}</span>
                        </a>
                    </li>
                `).join('');
            } else {
                relatedContainer.innerHTML = `
                    <li class="related-empty">No related articles found.</li>
                `;
            }
        } catch (error) {
            console.warn('Failed to load related articles:', error);
            relatedContainer.innerHTML = '';
        }
    }

    /**
     * Load and render table of contents
     * @param {Object} article - Article with TOC data
     */
    async loadTableOfContents(article) {
        const tocContainer = document.getElementById('toc-list');
        if (!tocContainer) return;

        // Extract TOC from article content headings
        const bodyEl = document.getElementById('article-body');
        const headings = bodyEl?.querySelectorAll('h2, h3, h4') || [];

        if (headings.length === 0) {
            tocContainer.innerHTML = `
                <li class="toc-empty">No sections in this article.</li>
            `;
            return;
        }

        // Build TOC structure
        const toc = [];
        headings.forEach((heading, index) => {
            const level = parseInt(heading.tagName.charAt(1));
            const id = heading.id || `section-${index}`;
            heading.id = id;

            toc.push({
                id,
                text: heading.textContent,
                level
            });
        });

        // Render TOC
        tocContainer.innerHTML = toc.map(item => `
            <li class="toc-item toc-level-${item.level}">
                <a href="#${item.id}" class="toc-link" data-section="${item.id}">
                    ${UIHelpers.escapeHtml(item.text)}
                </a>
            </li>
        `).join('');

        // Setup scroll spy
        this.setupScrollSpy(headings);
    }

    /**
     * Setup scroll spy for TOC highlighting
     * @param {NodeList} headings - Heading elements
     */
    setupScrollSpy(headings) {
        // Disconnect previous observer
        if (this.tocObserver) {
            this.tocObserver.disconnect();
        }

        // Create new observer
        this.tocObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Update active TOC item
                    const id = entry.target.id;
                    document.querySelectorAll('.toc-link').forEach(link => {
                        link.classList.toggle('active', link.dataset.section === id);
                    });
                }
            });
        }, {
            rootMargin: '-20% 0px -70% 0px'
        });

        // Observe headings
        headings.forEach(heading => {
            this.tocObserver.observe(heading);
        });
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Tab switching
        this.container.addEventListener('click', (e) => {
            const tab = e.target.closest('.panel-tab');
            if (tab) {
                this.switchTab(tab.dataset.tab);
            }

            // Tag clicks
            const tagBtn = e.target.closest('.tag-btn');
            if (tagBtn) {
                const tag = tagBtn.dataset.tag;
                this.eventBus.emit('search:submit', `tag:${tag}`);
            }
        });

        // TOC link clicks
        document.getElementById('toc-list')?.addEventListener('click', (e) => {
            const link = e.target.closest('.toc-link');
            if (link) {
                e.preventDefault();
                const target = document.getElementById(link.dataset.section);
                if (target) {
                    UIHelpers.scrollIntoView(target, { behavior: 'smooth' });
                }
            }
        });

        // Add panel button
        document.getElementById('add-panel-btn')?.addEventListener('click', () => {
            this.addPanel();
        });

        // Close panel button
        document.getElementById('close-panel-btn')?.addEventListener('click', () => {
            this.removePanel();
        });

        // Expand panel button
        document.getElementById('expand-panel-btn')?.addEventListener('click', () => {
            this.toggleFullscreen();
        });

        // Print/Export button
        document.getElementById('btn-print')?.addEventListener('click', () => {
            this.exportArticle();
        });

        // Share button
        document.getElementById('btn-share')?.addEventListener('click', () => {
            this.shareArticle();
        });

        // Related article clicks
        document.getElementById('related-list')?.addEventListener('click', (e) => {
            const link = e.target.closest('.related-link');
            if (link) {
                e.preventDefault();
                const articleId = link.getAttribute('href').split('/').pop();
                this.eventBus.emit('article:selected', { id: articleId });
            }
        });
    }

    /**
     * Switch active tab
     * @param {string} tabName - Tab name
     */
    switchTab(tabName) {
        this.activeTab = tabName;

        // Update tab buttons
        const tabs = this.container.querySelectorAll('.panel-tab');
        tabs.forEach(tab => {
            const isActive = tab.dataset.tab === tabName;
            tab.classList.toggle('active', isActive);
            tab.setAttribute('aria-selected', isActive);
        });

        // Update tab panels
        const panels = {
            content: document.getElementById('article-body')?.parentElement,
            notes: document.getElementById('panel-notes'),
            citations: document.getElementById('panel-citations')
        };

        Object.entries(panels).forEach(([name, panel]) => {
            if (panel) {
                panel.hidden = name !== tabName;
            }
        });
    }

    /**
     * Add a second reading panel
     */
    addPanel() {
        const readerContainer = document.getElementById('reader-container');
        const secondaryPanel = document.getElementById('panel-secondary');

        if (readerContainer && secondaryPanel) {
            const currentPanels = parseInt(readerContainer.dataset.panels) || 1;
            if (currentPanels < 2) {
                readerContainer.dataset.panels = '2';
                secondaryPanel.hidden = false;
            }
        }
    }

    /**
     * Remove secondary reading panel
     */
    removePanel() {
        const readerContainer = document.getElementById('reader-container');
        const secondaryPanel = document.getElementById('panel-secondary');

        if (readerContainer && secondaryPanel) {
            readerContainer.dataset.panels = '1';
            secondaryPanel.hidden = true;
        }
    }

    /**
     * Toggle fullscreen mode
     */
    toggleFullscreen() {
        const panel = document.getElementById('panel-primary');
        if (panel) {
            panel.classList.toggle('fullscreen');

            // Update button icon
            const btn = document.getElementById('expand-panel-btn');
            const isFullscreen = panel.classList.contains('fullscreen');
            const iconUse = btn?.querySelector('use');
            if (iconUse) {
                iconUse.setAttribute('href',
                    `assets/icons/sprite.svg#icon-${isFullscreen ? 'minimize' : 'maximize'}`);
            }
        }
    }

    /**
     * Export article as PDF
     */
    exportArticle() {
        if (!this.currentArticle) return;

        // Create print-friendly version
        const printContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>${UIHelpers.escapeHtml(this.currentArticle.title)}</title>
                <style>
                    body { font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 40px; }
                    h1 { font-size: 28px; margin-bottom: 10px; }
                    .meta { color: #666; margin-bottom: 30px; }
                    .content { line-height: 1.8; }
                    pre { background: #f5f5f5; padding: 16px; overflow-x: auto; }
                    code { font-family: monospace; }
                    @media print { body { padding: 0; } }
                </style>
            </head>
            <body>
                <h1>${UIHelpers.escapeHtml(this.currentArticle.title)}</h1>
                <div class="meta">
                    ${this.currentArticle.category_name || this.currentArticle.category} |
                    ${UIHelpers.formatDate(this.currentArticle.date)} |
                    ${UIHelpers.formatReadingTime(this.currentArticle.reading_time)} read
                </div>
                <div class="content">
                    ${this.currentArticle.content_html}
                </div>
            </body>
            </html>
        `;

        // Open print dialog
        const printWindow = window.open('', '_blank');
        printWindow.document.write(printContent);
        printWindow.document.close();
        printWindow.print();
    }

    /**
     * Share article
     */
    async shareArticle() {
        if (!this.currentArticle) return;

        const shareData = {
            title: this.currentArticle.title,
            text: this.currentArticle.description || '',
            url: window.location.href
        };

        try {
            if (navigator.share) {
                await navigator.share(shareData);
            } else {
                // Fallback to clipboard
                await UIHelpers.copyToClipboard(window.location.href);
            }
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Failed to share:', error);
            }
        }
    }

    /**
     * Sanitize HTML content
     * @param {string} html - Raw HTML
     * @returns {string}
     */
    sanitizeHtml(html) {
        if (typeof DOMPurify !== 'undefined') {
            return DOMPurify.sanitize(html, {
                ALLOWED_TAGS: [
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    'p', 'a', 'ul', 'ol', 'li', 'blockquote',
                    'pre', 'code', 'em', 'strong', 'del', 's',
                    'table', 'thead', 'tbody', 'tr', 'th', 'td',
                    'br', 'hr', 'img', 'figure', 'figcaption',
                    'div', 'span', 'sup', 'sub', 'mark'
                ],
                ALLOWED_ATTR: [
                    'href', 'src', 'alt', 'title', 'class', 'id',
                    'target', 'rel', 'data-*', 'loading'
                ],
                ADD_ATTR: ['target'],
                ALLOW_DATA_ATTR: true
            });
        }
        return html;
    }

    /**
     * Highlight code blocks
     * @param {Element} container - Container element
     */
    highlightCodeBlocks(container) {
        const codeBlocks = container.querySelectorAll('pre code');
        codeBlocks.forEach(block => {
            // Add language class if detected
            const parent = block.parentElement;
            if (parent) {
                parent.classList.add('code-block');

                // Add copy button
                const copyBtn = document.createElement('button');
                copyBtn.className = 'code-copy-btn';
                copyBtn.innerHTML = `
                    <svg class="icon" aria-hidden="true">
                        <use href="assets/icons/sprite.svg#icon-copy"></use>
                    </svg>
                `;
                copyBtn.addEventListener('click', () => {
                    UIHelpers.copyToClipboard(block.textContent);
                });
                parent.appendChild(copyBtn);
            }
        });
    }

    /**
     * Add anchor links to headings
     * @param {Element} container - Container element
     */
    addHeadingAnchors(container) {
        const headings = container.querySelectorAll('h2, h3, h4, h5, h6');
        headings.forEach((heading, index) => {
            if (!heading.id) {
                heading.id = `heading-${index}`;
            }

            const anchor = document.createElement('a');
            anchor.className = 'heading-anchor';
            anchor.href = `#${heading.id}`;
            anchor.innerHTML = `
                <svg class="icon" aria-hidden="true">
                    <use href="assets/icons/sprite.svg#icon-link"></use>
                </svg>
            `;
            anchor.setAttribute('aria-label', 'Link to this section');

            heading.classList.add('has-anchor');
            heading.appendChild(anchor);
        });
    }

    /**
     * Setup lazy loading for images
     * @param {Element} container - Container element
     */
    setupLazyImages(container) {
        const images = container.querySelectorAll('img');
        images.forEach(img => {
            img.setAttribute('loading', 'lazy');
            img.classList.add('article-image');
        });
    }

    /**
     * Render error state
     * @param {string} message - Error message
     */
    renderError(message) {
        const bodyEl = document.getElementById('article-body');
        if (bodyEl) {
            bodyEl.innerHTML = `
                <div class="error-state parchment-card">
                    <svg class="icon icon-xl" aria-hidden="true">
                        <use href="assets/icons/sprite.svg#icon-warning"></use>
                    </svg>
                    <p>${UIHelpers.escapeHtml(message)}</p>
                    <button class="btn btn-outline" onclick="window.history.back()">
                        Go Back
                    </button>
                </div>
            `;
        }
    }

    /**
     * Clean up when leaving reader
     */
    cleanup() {
        if (this.tocObserver) {
            this.tocObserver.disconnect();
        }
        this.currentArticle = null;
    }
}
