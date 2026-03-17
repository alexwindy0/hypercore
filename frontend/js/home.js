/**
 * Home Page JavaScript
 */

// Load featured products
document.addEventListener('DOMContentLoaded', async () => {
    await loadFeaturedProducts();
    setupNewsletterForm();
    updateUserUI();
});

/**
 * Load featured products
 */
async function loadFeaturedProducts() {
    const container = document.getElementById('featuredProducts');
    if (!container) return;
    
    // Show skeleton loading
    container.innerHTML = Array(4).fill(0).map(() => `
        <div class="card">
            <div class="skeleton" style="aspect-ratio: 1;"></div>
            <div class="card-content">
                <div class="skeleton" style="height: 20px; width: 80%; margin-bottom: 8px;"></div>
                <div class="skeleton" style="height: 16px; width: 40%;"></div>
            </div>
        </div>
    `).join('');
    
    try {
        const response = await Hypercore.apiRequest('/products/featured');
        
        if (response.success && response.products.length > 0) {
            container.innerHTML = response.products.map(product => createProductCard(product)).join('');
        } else {
            container.innerHTML = '<p class="text-center text-gray">No featured products available</p>';
        }
    } catch (error) {
        console.error('Failed to load featured products:', error);
        container.innerHTML = '<p class="text-center text-gray">Failed to load products</p>';
    }
}

/**
 * Create product card HTML
 * @param {Object} product - Product data
 * @returns {string} - Card HTML
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
                ${product.is_featured ? '<span class="badge badge-primary product-badge">Featured</span>' : ''}
            </a>
            <div class="product-info">
                <a href="/product.html?id=${product.id}">
                    <h3 class="product-name">${product.name}</h3>
                </a>
                <p class="product-price">${Hypercore.formatCurrency(product.price)}</p>
                <div class="product-sizes">
                    ${sizes.map(size => `
                        <button class="size-btn" 
                                onclick="quickAddToCart(event, ${product.id}, '${size}', ${product.price}, '${product.name.replace(/'/g, "\\'")}', '${image}')"
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
 * @param {Event} event - Click event
 * @param {number} productId - Product ID
 * @param {string} size - Size
 * @param {number} price - Price
 * @param {string} name - Product name
 * @param {string} image - Product image
 */
function quickAddToCart(event, productId, size, price, name, image) {
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
 * Setup newsletter form
 */
function setupNewsletterForm() {
    const form = document.getElementById('newsletterForm');
    if (!form) return;
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = form.querySelector('input[type="email"]').value;
        
        // Show success message (in production, this would subscribe the user)
        Hypercore.showToast('Thank you for subscribing!', 'success');
        form.reset();
    });
}

/**
 * Update UI based on user login state
 */
function updateUserUI() {
    const user = Hypercore.getUser();
    const mobileUserSection = document.getElementById('mobileUserSection');
    
    if (user && mobileUserSection) {
        mobileUserSection.innerHTML = `
            <div class="mobile-user-name">${user.name}</div>
            <div class="mobile-user-email">${user.email}</div>
        `;
    }
}
