/**
 * LiverWatch - Core Utilities Module
 * ===================================
 * 
 * Core utility functions used across the application.
 */

const LiverWatch = (function() {
    'use strict';

    // Configuration
    const config = {
        animationDuration: 300,
        debounceDelay: 250,
        toastDuration: 5000,
        apiBaseUrl: '/api',
    };

    // =========================================
    // DOM Utilities
    // =========================================

    /**
     * Safely query a single element
     */
    function $(selector, parent = document) {
        return parent.querySelector(selector);
    }

    /**
     * Safely query multiple elements
     */
    function $$(selector, parent = document) {
        return Array.from(parent.querySelectorAll(selector));
    }

    /**
     * Create element with attributes and children
     */
    function createElement(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'dataset') {
                Object.entries(value).forEach(([dataKey, dataValue]) => {
                    element.dataset[dataKey] = dataValue;
                });
            } else if (key.startsWith('on') && typeof value === 'function') {
                element.addEventListener(key.slice(2).toLowerCase(), value);
            } else {
                element.setAttribute(key, value);
            }
        });

        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else if (child instanceof Node) {
                element.appendChild(child);
            }
        });

        return element;
    }

    /**
     * Add event listener with delegation support
     */
    function on(element, event, selector, handler) {
        if (typeof selector === 'function') {
            handler = selector;
            element.addEventListener(event, handler);
        } else {
            element.addEventListener(event, function(e) {
                const target = e.target.closest(selector);
                if (target && element.contains(target)) {
                    handler.call(target, e, target);
                }
            });
        }
    }

    /**
     * Remove element with animation
     */
    function removeElement(element, animation = 'fadeOut') {
        element.style.animation = `${animation} ${config.animationDuration}ms ease forwards`;
        setTimeout(() => element.remove(), config.animationDuration);
    }

    // =========================================
    // Utility Functions
    // =========================================

    /**
     * Debounce function
     */
    function debounce(func, wait = config.debounceDelay) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Throttle function
     */
    function throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Format date to localized string
     */
    function formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };
        return new Date(date).toLocaleDateString('en-US', { ...defaultOptions, ...options });
    }

    /**
     * Format relative time (e.g., "2 hours ago")
     */
    function formatRelativeTime(date) {
        const now = new Date();
        const past = new Date(date);
        const diffMs = now - past;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffSecs < 60) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return formatDate(date);
    }

    /**
     * Format number with commas
     */
    function formatNumber(num) {
        return new Intl.NumberFormat('en-US').format(num);
    }

    /**
     * Truncate text with ellipsis
     */
    function truncate(text, length = 100) {
        if (text.length <= length) return text;
        return text.slice(0, length).trim() + '...';
    }

    /**
     * Generate unique ID
     */
    function generateId() {
        return `lw-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Deep clone object
     */
    function deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    }

    /**
     * Check if element is in viewport
     */
    function isInViewport(element, threshold = 0) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top + threshold < window.innerHeight &&
            rect.bottom > threshold &&
            rect.left + threshold < window.innerWidth &&
            rect.right > threshold
        );
    }

    // =========================================
    // API Utilities
    // =========================================

    /**
     * Fetch wrapper with error handling
     */
    async function api(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: { ...defaultOptions.headers, ...options.headers }
        };

        if (options.body && typeof options.body === 'object') {
            mergedOptions.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(`${config.apiBaseUrl}${endpoint}`, mergedOptions);
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.message || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // =========================================
    // Storage Utilities
    // =========================================

    const storage = {
        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch {
                return defaultValue;
            }
        },

        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch {
                return false;
            }
        },

        remove(key) {
            localStorage.removeItem(key);
        },

        clear() {
            localStorage.clear();
        }
    };

    // =========================================
    // Event Bus (Pub/Sub)
    // =========================================

    const eventBus = {
        events: {},

        on(event, callback) {
            if (!this.events[event]) {
                this.events[event] = [];
            }
            this.events[event].push(callback);
            return () => this.off(event, callback);
        },

        off(event, callback) {
            if (!this.events[event]) return;
            this.events[event] = this.events[event].filter(cb => cb !== callback);
        },

        emit(event, data) {
            if (!this.events[event]) return;
            this.events[event].forEach(callback => callback(data));
        }
    };

    // =========================================
    // Public API
    // =========================================

    return {
        config,
        $,
        $$,
        createElement,
        on,
        removeElement,
        debounce,
        throttle,
        formatDate,
        formatRelativeTime,
        formatNumber,
        truncate,
        generateId,
        deepClone,
        isInViewport,
        api,
        storage,
        eventBus
    };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LiverWatch;
}
