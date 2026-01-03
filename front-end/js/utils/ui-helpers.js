/**
 * UI Helper Utilities
 * ===================
 * Common UI utility functions for Knowledge Nexus.
 *
 * Author: Dennis 'dnoice' Smaltz
 * Signature: Aim Twice, Shoot Once!
 */

export const UIHelpers = {
    /**
     * Show a toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type (success, error, warning, info)
     * @param {number} duration - Duration in milliseconds
     */
    showToast(message, type = 'info', duration = 4000) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type} animate-slide-in-right`;
        toast.innerHTML = `
            <svg class="icon toast-icon" aria-hidden="true">
                <use href="assets/icons/sprite.svg#icon-${this.getToastIcon(type)}"></use>
            </svg>
            <span class="toast-message">${this.escapeHtml(message)}</span>
            <button class="toast-close" aria-label="Close notification">
                <svg class="icon" aria-hidden="true">
                    <use href="assets/icons/sprite.svg#icon-close"></use>
                </svg>
            </button>
        `;

        // Add close handler
        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.removeToast(toast);
        });

        container.appendChild(toast);

        // Auto-remove after duration
        setTimeout(() => {
            this.removeToast(toast);
        }, duration);
    },

    /**
     * Get toast icon based on type
     */
    getToastIcon(type) {
        const icons = {
            success: 'check',
            error: 'close',
            warning: 'question',
            info: 'info'
        };
        return icons[type] || 'info';
    },

    /**
     * Remove a toast element
     */
    removeToast(toast) {
        toast.classList.add('animate-fade-out');
        setTimeout(() => toast.remove(), 300);
    },

    /**
     * Escape HTML special characters
     * @param {string} str - String to escape
     * @returns {string}
     */
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    /**
     * Debounce a function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function}
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle a function
     * @param {Function} func - Function to throttle
     * @param {number} limit - Limit in milliseconds
     * @returns {Function}
     */
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Format a date string
     * @param {string} dateStr - ISO date string
     * @param {Object} options - Intl.DateTimeFormat options
     * @returns {string}
     */
    formatDate(dateStr, options = {}) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            ...options
        });
    },

    /**
     * Format reading time
     * @param {number} minutes - Reading time in minutes
     * @returns {string}
     */
    formatReadingTime(minutes) {
        if (!minutes) return '--';
        if (minutes < 1) return '< 1 min';
        if (minutes === 1) return '1 min';
        return `${Math.round(minutes)} min`;
    },

    /**
     * Truncate text with ellipsis
     * @param {string} text - Text to truncate
     * @param {number} maxLength - Maximum length
     * @returns {string}
     */
    truncate(text, maxLength = 100) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength).trim() + '...';
    },

    /**
     * Generate a unique ID
     * @param {string} prefix - ID prefix
     * @returns {string}
     */
    generateId(prefix = 'id') {
        return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    },

    /**
     * Scroll element into view smoothly
     * @param {Element} element - Element to scroll to
     * @param {Object} options - Scroll options
     */
    scrollIntoView(element, options = {}) {
        if (!element) return;
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
            ...options
        });
    },

    /**
     * Check if element is in viewport
     * @param {Element} element - Element to check
     * @returns {boolean}
     */
    isInViewport(element) {
        if (!element) return false;
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    },

    /**
     * Copy text to clipboard
     * @param {string} text - Text to copy
     * @returns {Promise<void>}
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copied to clipboard', 'success', 2000);
        } catch (error) {
            console.error('Failed to copy:', error);
            this.showToast('Failed to copy', 'error');
        }
    },

    /**
     * Create an element from HTML string
     * @param {string} html - HTML string
     * @returns {Element}
     */
    createElement(html) {
        const template = document.createElement('template');
        template.innerHTML = html.trim();
        return template.content.firstChild;
    },

    /**
     * Show loading state on element
     * @param {Element} element - Element to show loading on
     * @param {boolean} loading - Loading state
     */
    setLoading(element, loading) {
        if (!element) return;
        if (loading) {
            element.setAttribute('data-loading', 'true');
            element.setAttribute('aria-busy', 'true');
        } else {
            element.removeAttribute('data-loading');
            element.removeAttribute('aria-busy');
        }
    },

    /**
     * Render loading skeleton
     * @param {number} count - Number of skeleton items
     * @returns {string}
     */
    renderSkeleton(count = 3) {
        return Array(count).fill('<div class="skeleton-item"></div>').join('');
    },

    /**
     * Render empty state
     * @param {string} message - Empty state message
     * @param {string} icon - Icon name
     * @returns {string}
     */
    renderEmptyState(message, icon = 'file') {
        return `
            <div class="empty-state parchment-card">
                <svg class="icon icon-xl" aria-hidden="true">
                    <use href="assets/icons/sprite.svg#icon-${icon}"></use>
                </svg>
                <p>${this.escapeHtml(message)}</p>
            </div>
        `;
    },

    /**
     * Parse query string parameters
     * @param {string} queryString - Query string
     * @returns {Object}
     */
    parseQueryString(queryString = window.location.search) {
        const params = new URLSearchParams(queryString);
        const result = {};
        for (const [key, value] of params) {
            if (result[key]) {
                if (Array.isArray(result[key])) {
                    result[key].push(value);
                } else {
                    result[key] = [result[key], value];
                }
            } else {
                result[key] = value;
            }
        }
        return result;
    },

    /**
     * Build query string from object
     * @param {Object} params - Parameters object
     * @returns {string}
     */
    buildQueryString(params) {
        const searchParams = new URLSearchParams();
        for (const [key, value] of Object.entries(params)) {
            if (Array.isArray(value)) {
                value.forEach(v => searchParams.append(key, v));
            } else if (value !== null && value !== undefined && value !== '') {
                searchParams.set(key, value);
            }
        }
        return searchParams.toString();
    },

    /**
     * Highlight text matches
     * @param {string} text - Text to highlight
     * @param {string} query - Search query
     * @returns {string}
     */
    highlightMatches(text, query) {
        if (!query || !text) return this.escapeHtml(text);

        const escaped = this.escapeHtml(text);
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        return escaped.replace(regex, '<mark class="highlight">$1</mark>');
    },

    /**
     * Escape regex special characters
     * @param {string} str - String to escape
     * @returns {string}
     */
    escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    },

    /**
     * Format file size
     * @param {number} bytes - Size in bytes
     * @returns {string}
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Animate element on scroll into view
     * @param {string} selector - Element selector
     * @param {string} animationClass - Animation class to add
     */
    animateOnScroll(selector, animationClass = 'animate-fade-in') {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add(animationClass);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll(selector).forEach(el => {
            observer.observe(el);
        });
    }
};
