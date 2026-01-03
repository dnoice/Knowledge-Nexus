/**
 * Application State Store
 * =======================
 * Centralized state management with reactive updates.
 *
 * Author: Dennis 'dnoice' Smaltz
 * Signature: Aim Twice, Shoot Once!
 */

export class Store {
    constructor() {
        this.state = new Map();
        this.listeners = new Map();
    }

    /**
     * Get a value from the store
     * @param {string} key - State key
     * @returns {any} Stored value
     */
    get(key) {
        return this.state.get(key);
    }

    /**
     * Set a value in the store
     * @param {string} key - State key
     * @param {any} value - Value to store
     */
    set(key, value) {
        const oldValue = this.state.get(key);
        this.state.set(key, value);

        // Notify listeners
        const keyListeners = this.listeners.get(key);
        if (keyListeners) {
            keyListeners.forEach(callback => {
                try {
                    callback(value, oldValue, key);
                } catch (error) {
                    console.error(`Store listener error for key "${key}":`, error);
                }
            });
        }

        // Notify wildcard listeners
        const wildcardListeners = this.listeners.get('*');
        if (wildcardListeners) {
            wildcardListeners.forEach(callback => {
                try {
                    callback(value, oldValue, key);
                } catch (error) {
                    console.error('Store wildcard listener error:', error);
                }
            });
        }
    }

    /**
     * Update a value using a function
     * @param {string} key - State key
     * @param {Function} updater - Function that receives current value and returns new value
     */
    update(key, updater) {
        const currentValue = this.get(key);
        const newValue = updater(currentValue);
        this.set(key, newValue);
    }

    /**
     * Delete a value from the store
     * @param {string} key - State key
     */
    delete(key) {
        const oldValue = this.state.get(key);
        this.state.delete(key);

        // Notify listeners
        const keyListeners = this.listeners.get(key);
        if (keyListeners) {
            keyListeners.forEach(callback => {
                try {
                    callback(undefined, oldValue, key);
                } catch (error) {
                    console.error(`Store listener error for key "${key}":`, error);
                }
            });
        }
    }

    /**
     * Check if a key exists
     * @param {string} key - State key
     * @returns {boolean}
     */
    has(key) {
        return this.state.has(key);
    }

    /**
     * Subscribe to changes for a specific key
     * @param {string} key - State key (use '*' for all changes)
     * @param {Function} callback - Callback function (newValue, oldValue, key)
     * @returns {Function} Unsubscribe function
     */
    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, new Set());
        }
        this.listeners.get(key).add(callback);

        // Return unsubscribe function
        return () => {
            this.listeners.get(key)?.delete(callback);
        };
    }

    /**
     * Clear all state
     */
    clear() {
        this.state.clear();
    }

    /**
     * Get all keys in the store
     * @returns {string[]}
     */
    keys() {
        return Array.from(this.state.keys());
    }

    /**
     * Get the entire state as an object
     * @returns {Object}
     */
    toObject() {
        const obj = {};
        for (const [key, value] of this.state) {
            obj[key] = value;
        }
        return obj;
    }

    /**
     * Batch update multiple values
     * @param {Object} updates - Object with key-value pairs
     */
    batch(updates) {
        for (const [key, value] of Object.entries(updates)) {
            this.set(key, value);
        }
    }

    /**
     * Get or set a value with a default
     * @param {string} key - State key
     * @param {any} defaultValue - Default value if key doesn't exist
     * @returns {any}
     */
    getOrSet(key, defaultValue) {
        if (!this.has(key)) {
            this.set(key, defaultValue);
        }
        return this.get(key);
    }
}
