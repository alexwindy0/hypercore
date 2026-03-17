/**
 * Hypercore E-commerce - Utility Functions
 */

// API Configuration
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000/api' 
    : '/api';

// Local Storage Keys
const STORAGE_KEYS = {
    CART: 'hypercore_cart',
    USER: 'hypercore_user',
    TOKEN: 'hypercore_token',
    THEME: 'hypercore_theme'
};

/**
 * Make API request
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise} - Response data
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        credentials: 'include'
    };
    
    // Add auth token if available
    const token = getToken();
    if (token) {
        defaultOptions.headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Get stored auth token
 * @returns {string|null} - JWT token
 */
function getToken() {
    return localStorage.getItem(STORAGE_KEYS.TOKEN);
}

/**
 * Set auth token
 * @param {string} token - JWT token
 */
function setToken(token) {
    localStorage.setItem(STORAGE_KEYS.TOKEN, token);
}

/**
 * Remove auth token
 */
function removeToken() {
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
}

/**
 * Get current user from storage
 * @returns {Object|null} - User data
 */
function getUser() {
    const user = localStorage.getItem(STORAGE_KEYS.USER);
    return user ? JSON.parse(user) : null;
}

/**
 * Set current user
 * @param {Object} user - User data
 */
function setUser(user) {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
}

/**
 * Remove current user
 */
function removeUser() {
    localStorage.removeItem(STORAGE_KEYS.USER);
}

/**
 * Check if user is logged in
 * @returns {boolean}
 */
function isLoggedIn() {
    return !!getToken() && !!getUser();
}

/**
 * Check if user is admin
 * @returns {boolean}
 */
function isAdmin() {
    const user = getUser();
    return user && user.role === 'admin';
}

/**
 * Logout user
 */
async function logout() {
    try {
        await apiRequest('/auth/logout', { method: 'POST' });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        removeToken();
        removeUser();
        window.location.href = '/';
    }
}

// ==================== CART FUNCTIONS ====================

/**
 * Get cart from localStorage
 * @returns {Array} - Cart items
 */
function getCart() {
    const cart = localStorage.getItem(STORAGE_KEYS.CART);
    return cart ? JSON.parse(cart) : [];
}

/**
 * Save cart to localStorage
 * @param {Array} cart - Cart items
 */
function saveCart(cart) {
    localStorage.setItem(STORAGE_KEYS.CART, JSON.stringify(cart));
    updateCartBadge();
}

/**
 * Add item to cart
 * @param {Object} item - Item to add
 */
function addToCart(item) {
    const cart = getCart();
    
    // Check if item already exists (same product and size)
    const existingIndex = cart.findIndex(
        i => i.product_id === item.product_id && i.size === item.size
    );
    
    if (existingIndex >= 0) {
        // Update quantity
        cart[existingIndex].quantity += item.quantity;
    } else {
        // Add new item
        cart.push(item);
    }
    
    saveCart(cart);
    showToast('Item added to cart', 'success');
}

/**
 * Remove item from cart
 * @param {number} productId - Product ID
 * @param {string} size - Size
 */
function removeFromCart(productId, size) {
    let cart = getCart();
    cart = cart.filter(item => !(item.product_id === productId && item.size === size));
    saveCart(cart);
}

/**
 * Update cart item quantity
 * @param {number} productId - Product ID
 * @param {string} size - Size
 * @param {number} quantity - New quantity
 */
function updateCartQuantity(productId, size, quantity) {
    const cart = getCart();
    const item = cart.find(i => i.product_id === productId && i.size === size);
    
    if (item) {
        if (quantity <= 0) {
            removeFromCart(productId, size);
        } else {
            item.quantity = quantity;
            saveCart(cart);
        }
    }
}

/**
 * Clear cart
 */
function clearCart() {
    localStorage.removeItem(STORAGE_KEYS.CART);
    updateCartBadge();
}

/**
 * Get cart total
 * @returns {number} - Total price
 */
function getCartTotal() {
    const cart = getCart();
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
}

/**
 * Get cart item count
 * @returns {number} - Item count
 */
function getCartCount() {
    const cart = getCart();
    return cart.reduce((count, item) => count + item.quantity, 0);
}

/**
 * Update cart badge in header
 */
function updateCartBadge() {
    const badge = document.querySelector('.cart-badge');
    if (badge) {
        const count = getCartCount();
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
    }
}

/**
 * Sync cart with server (when user logs in)
 */
async function syncCartWithServer() {
    if (!isLoggedIn()) return;
    
    const cart = getCart();
    if (cart.length === 0) return;
    
    try {
        const response = await apiRequest('/cart/sync', {
            method: 'POST',
            body: JSON.stringify({ items: cart })
        });
        
        if (response.success) {
            clearCart();
        }
    } catch (error) {
        console.error('Cart sync error:', error);
    }
}

// ==================== UI FUNCTIONS ====================

/**
 * Show toast notification
 * @param {string} message - Message to show
 * @param {string} type - Toast type (success, error, warning, info)
 * @param {number} duration - Duration in ms
 */
function showToast(message, type = 'info', duration = 3000) {
    // Create toast container if not exists
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    // Icon based on type
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    toast.innerHTML = `
        <span>${icons[type] || icons.info}</span>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Remove after duration
    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Show loading spinner
 * @param {HTMLElement} element - Element to show spinner in
 */
function showLoading(element) {
    element.innerHTML = '<div class="spinner"></div>';
    element.disabled = true;
}

/**
 * Hide loading spinner
 * @param {HTMLElement} element - Element to restore
 * @param {string} originalContent - Original content
 */
function hideLoading(element, originalContent) {
    element.innerHTML = originalContent;
    element.disabled = false;
}

/**
 * Format currency
 * @param {number} amount - Amount to format
 * @returns {string} - Formatted currency
 */
function formatCurrency(amount) {
    return `₦${parseFloat(amount).toLocaleString('en-NG', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;
}

/**
 * Format currency without decimals
 * @param {number} amount - Amount to format
 * @returns {string} - Formatted currency
 */
function formatCurrencyShort(amount) {
    return `₦${parseFloat(amount).toLocaleString('en-NG', {
        maximumFractionDigits: 0
    })}`;
}

/**
 * Format date
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-NG', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Truncate text
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} - Truncated text
 */
function truncateText(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Debounce function
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} - Debounced function
 */
function debounce(func, wait = 300) {
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
 * Create skeleton loader
 * @param {string} type - Skeleton type (card, text, image)
 * @returns {string} - Skeleton HTML
 */
function createSkeleton(type = 'card') {
    const skeletons = {
        card: `
            <div class="card">
                <div class="skeleton" style="aspect-ratio: 1;"></div>
                <div class="card-content">
                    <div class="skeleton" style="height: 20px; width: 80%; margin-bottom: 8px;"></div>
                    <div class="skeleton" style="height: 16px; width: 40%;"></div>
                </div>
            </div>
        `,
        text: `<div class="skeleton" style="height: 16px; width: 100%;"></div>`,
        image: `<div class="skeleton" style="aspect-ratio: 1;"></div>`
    };
    return skeletons[type] || skeletons.text;
}

// ==================== FORM FUNCTIONS ====================

/**
 * Validate email
 * @param {string} email - Email to validate
 * @returns {boolean}
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate Nigerian phone number
 * @param {string} phone - Phone to validate
 * @returns {boolean}
 */
function isValidPhone(phone) {
    const cleaned = phone.replace(/\D/g, '');
    return cleaned.length >= 10 && cleaned.length <= 14;
}

/**
 * Show form error
 * @param {HTMLElement} input - Input element
 * @param {string} message - Error message
 */
function showFormError(input, message) {
    input.classList.add('error');
    
    // Remove existing error
    const existingError = input.parentElement.querySelector('.form-error');
    if (existingError) existingError.remove();
    
    // Add error message
    const error = document.createElement('span');
    error.className = 'form-error';
    error.textContent = message;
    input.parentElement.appendChild(error);
}

/**
 * Clear form error
 * @param {HTMLElement} input - Input element
 */
function clearFormError(input) {
    input.classList.remove('error');
    const error = input.parentElement.querySelector('.form-error');
    if (error) error.remove();
}

/**
 * Clear all form errors
 * @param {HTMLFormElement} form - Form element
 */
function clearAllFormErrors(form) {
    form.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
    form.querySelectorAll('.form-error').forEach(el => el.remove());
}

// ==================== URL & NAVIGATION ====================

/**
 * Get URL parameter
 * @param {string} name - Parameter name
 * @returns {string|null}
 */
function getUrlParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

/**
 * Update URL parameter
 * @param {string} name - Parameter name
 * @param {string} value - Parameter value
 */
function updateUrlParam(name, value) {
    const url = new URL(window.location);
    if (value) {
        url.searchParams.set(name, value);
    } else {
        url.searchParams.delete(name);
    }
    window.history.pushState({}, '', url);
}

/**
 * Navigate to page
 * @param {string} path - Page path
 */
function navigateTo(path) {
    window.location.href = path;
}

// ==================== INITIALIZATION ====================

/**
 * Initialize common functionality
 */
function initCommon() {
    // Update cart badge
    updateCartBadge();
    
    // Setup mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', () => {
            menuToggle.classList.toggle('active');
            mobileMenu.classList.toggle('active');
            document.body.style.overflow = mobileMenu.classList.contains('active') ? 'hidden' : '';
        });
    }
    
    // Setup search toggle
    const searchToggle = document.querySelector('.search-toggle');
    const searchBar = document.querySelector('.search-bar');
    const searchClose = document.querySelector('.search-close');
    
    if (searchToggle && searchBar) {
        searchToggle.addEventListener('click', () => {
            searchBar.classList.add('active');
            searchBar.querySelector('input').focus();
        });
    }
    
    if (searchClose && searchBar) {
        searchClose.addEventListener('click', () => {
            searchBar.classList.remove('active');
        });
    }
    
    // Setup logout button
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initCommon);

// Export functions for use in other scripts
window.Hypercore = {
    apiRequest,
    getToken,
    setToken,
    removeToken,
    getUser,
    setUser,
    removeUser,
    isLoggedIn,
    isAdmin,
    logout,
    getCart,
    saveCart,
    addToCart,
    removeFromCart,
    updateCartQuantity,
    clearCart,
    getCartTotal,
    getCartCount,
    syncCartWithServer,
    showToast,
    showLoading,
    hideLoading,
    formatCurrency,
    formatCurrencyShort,
    formatDate,
    truncateText,
    debounce,
    createSkeleton,
    isValidEmail,
    isValidPhone,
    showFormError,
    clearFormError,
    clearAllFormErrors,
    getUrlParam,
    updateUrlParam,
    navigateTo
};
