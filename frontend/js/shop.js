/**
 * Shop Page JavaScript
 */

// State
let currentPage = 1;
let totalPages = 1;
let activeFilters = {
    gender: [],
    min_price: null,
    max_price: null,
    size: null,
    sort: 'newest',
    search: null
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    parseUrlParams();
    loadProducts();
    setupSearch();
});

/**
 * Parse URL parameters and set initial filters
 */
function parseUrlParams() {
    const params = new URLSearchParams(window.location.search);
    
    // Gender filter
    const gender = params.get('gender');
    if (gender) {
        activeFilters.gender = [gender];
        document.querySelector(`input[name="gender"][value="${gender}"]`).checked = true;
        document.getElementById('shopTitle').textContent = gender === 'men' ? "Men's Collection" : "Women's Collection";
    }
    
    // Search
    const search = params.get('search');
    if (search) {
        activeFilters.search = search;
        document.getElementById('searchInput').value = search;
        document.getElementById('shopTitle').textContent = `Search: "${search}"`;
    }
    
    // Featured
    const featured = params.get('featured');
    if (featured === 'true') {
        document.getElementById('shopTitle').textContent = 'New Arrivals';
    }
}

/**
 * Load products with current filters
 */
async function loadProducts() {
    const container = document.getElementById('productsGrid');
    const emptyState = document.getElementById('emptyState');
    const pagination = document.getElementById('pagination');
    
    // Show loading skeletons
    container.innerHTML = Array(8).fill(0).map(() => `
        <div class="card">
            <div class="skeleton" style="aspect-ratio: 1;"></div>
            <div class="card-content">
                <div class="skeleton" style="height: 20px; width: 80%; margin-bottom: 8px;"></div>
                <div class="skeleton" style="height: 16px; width: 40%;"></div>
            </div>
        </div>
    `).join('');
    
    // Build query string
    const params = new URLSearchParams();
    params.set('page', currentPage);
    params.set('per_page', 20);
    params.set('sort', activeFilters.sort);
    
    if (activeFilters.gender.length > 0) {
        params.set('gender', activeFilters.gender[0]);
    }
    if (activeFilters.min_price) {
        params.set('min_price', activeFilters.min_price);
    }
    if (activeFilters.max_price) {
        params.set('max_price', activeFilters.max_price);
    }
    if (activeFilters.size) {
        params.set('size', activeFilters.size);
    }
    if (activeFilters.search) {
        params.set('search', activeFilters.search);
    }
    
    try {
        const response = await Hypercore.apiRequest(`/products/?${params.toString()}`);
        
        if (response.success) {
            const { products, pagination: pageInfo } = response;
            
            // Update count
            document.getElementById('shopCount').textContent = `${pageInfo.total} products`;
            
            // Update pagination
            currentPage = pageInfo.page;
            totalPages = pageInfo.total_pages;
            
            if (products.length === 0) {
                container.innerHTML = '';
                container.classList.add('hidden');
                emptyState.classList.remove('hidden');
                pagination.innerHTML = '';
            } else {
                container.classList.remove('hidden');
                emptyState.classList.add('hidden');
                container.innerHTML = products.map(product => createProductCard(product)).join('');
                renderPagination();
            }
        }
    } catch (error) {
        console.error('Failed to load products:', error);
        container.innerHTML = '<p class="text-center text-gray">Failed to load products. Please try again.</p>';
    }
}

/**
 * Create product card HTML
 */
function createProductCard(product) {
    const image = product.images && product.images.length > 0 
        ? product.images[0] 
        : 'assets/images/placeholder.jpg';
    
    const sizes = product.sizes || ['S', 'M', 'L', 'XL', 'XXL'];
    const stock = product.stock || {};
    
    return `
        <div class="product-card">
            <a href="/product.html?id=${product.id}" class="product-image">
                <img src="${image}" alt="${product.name}" loading="lazy">
            </a>
            <div class="product-info">
                <a href="/product.html?id=${product.id}">
                    <h3 class="product-name">${product.name}</h3>
                </a>
                <p class="product-price">${Hypercore.formatCurrency(product.price)}</p>
                <div class="product-sizes">
                    ${sizes.map(size => `
                        <button class="size-btn" 
                                onclick="quickAdd(event, ${product.id}, '${size}', ${product.price}, '${product.name.replace(/'/g, "\\'")}', '${image}')"
                                ${stock[size] === 0 ? 'disabled' : ''}>
                            ${size}
                        </button>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

/**
 * Quick add to cart
 */
function quickAdd(event, productId, size, price, name, image) {
    event.preventDefault();
    event.stopPropagation();
    
    Hypercore.addToCart({
        product_id: productId,
        size: size,
        quantity: 1,
        price: price,
        name: name,
        image: image
    });
}

/**
 * Render pagination
 */
function renderPagination() {
    const container = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    html += `
        <button class="pagination-btn" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
            ←
        </button>
    `;
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">
                ${i}
            </button>
        `;
    }
    
    // Next button
    html += `
        <button class="pagination-btn" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
            →
        </button>
    `;
    
    container.innerHTML = html;
}

/**
 * Go to page
 */
function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadProducts();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Apply filters
 */
function applyFilters() {
    // Get gender filters
    const genderCheckboxes = document.querySelectorAll('input[name="gender"]:checked');
    activeFilters.gender = Array.from(genderCheckboxes).map(cb => cb.value);
    
    // Get price filters
    const minPrice = document.getElementById('minPrice').value;
    const maxPrice = document.getElementById('maxPrice').value;
    activeFilters.min_price = minPrice ? parseFloat(minPrice) : null;
    activeFilters.max_price = maxPrice ? parseFloat(maxPrice) : null;
    
    // Get sort
    activeFilters.sort = document.getElementById('sortSelect').value;
    
    // Reset to first page and load
    currentPage = 1;
    loadProducts();
}

/**
 * Toggle size filter
 */
function toggleSizeFilter(btn) {
    const size = btn.dataset.size;
    
    // Remove active from all
    document.querySelectorAll('.size-filter-btn').forEach(b => b.classList.remove('active'));
    
    if (activeFilters.size === size) {
        // Deselect
        activeFilters.size = null;
    } else {
        // Select
        btn.classList.add('active');
        activeFilters.size = size;
    }
    
    currentPage = 1;
    loadProducts();
}

/**
 * Clear all filters
 */
function clearFilters() {
    // Reset filter state
    activeFilters = {
        gender: [],
        min_price: null,
        max_price: null,
        size: null,
        sort: 'newest',
        search: null
    };
    
    // Reset UI
    document.querySelectorAll('input[name="gender"]').forEach(cb => cb.checked = false);
    document.getElementById('minPrice').value = '';
    document.getElementById('maxPrice').value = '';
    document.getElementById('sortSelect').value = 'newest';
    document.querySelectorAll('.size-filter-btn').forEach(b => b.classList.remove('active'));
    
    // Update URL
    window.history.pushState({}, '', '/shop.html');
    document.getElementById('shopTitle').textContent = 'All Products';
    
    currentPage = 1;
    loadProducts();
}

/**
 * Toggle mobile filters
 */
function toggleMobileFilters() {
    const sidebar = document.getElementById('filtersSidebar');
    
    // Create overlay if not exists
    let overlay = document.querySelector('.filters-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'filters-overlay';
        overlay.onclick = toggleMobileFilters;
        document.body.appendChild(overlay);
    }
    
    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
    document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : '';
}

/**
 * Setup search functionality
 */
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (query) {
                activeFilters.search = query;
                document.getElementById('shopTitle').textContent = `Search: "${query}"`;
                currentPage = 1;
                loadProducts();
                
                // Close search bar
                document.querySelector('.search-bar').classList.remove('active');
            }
        }
    });
}
