/**
 * Product Detail Page JavaScript
 */

let currentProduct = null;
let selectedSize = null;
let quantity = 1;

document.addEventListener('DOMContentLoaded', () => {
    loadProduct();
});

/**
 * Load product details
 */
async function loadProduct() {
    const productId = new URLSearchParams(window.location.search).get('id');
    
    if (!productId) {
        window.location.href = '/shop.html';
        return;
    }
    
    try {
        const response = await Hypercore.apiRequest(`/products/${productId}`);
        
        if (response.success) {
            currentProduct = response.product;
            renderProduct(response.product);
            renderRelatedProducts(response.related_products);
            document.title = `${response.product.name} | Hypercore`;
        } else {
            window.location.href = '/shop.html';
        }
    } catch (error) {
        console.error('Failed to load product:', error);
        window.location.href = '/shop.html';
    }
}

/**
 * Render product details
 */
function renderProduct(product) {
    const container = document.getElementById('productDetail');
    const images = product.images || [];
    const mainImage = images[0] || 'assets/images/placeholder.jpg';
    const sizes = product.sizes || ['S', 'M', 'L', 'XL', 'XXL'];
    const stock = product.stock || {};
    
    container.innerHTML = `
        <!-- Product Gallery -->
        <div class="product-gallery">
            <div class="gallery-main">
                <img src="${mainImage}" alt="${product.name}" id="mainImage">
            </div>
            ${images.length > 1 ? `
                <div class="gallery-thumbs">
                    ${images.map((img, i) => `
                        <button class="gallery-thumb ${i === 0 ? 'active' : ''}" onclick="changeImage('${img}', this)">
                            <img src="${img}" alt="${product.name} - view ${i + 1}">
                        </button>
                    `).join('')}
                </div>
            ` : ''}
        </div>
        
        <!-- Product Info -->
        <div class="product-info-detail">
            <h1 class="product-title-detail">${product.name}</h1>
            <p class="product-price-detail">${Hypercore.formatCurrency(product.price)}</p>
            
            <div class="product-description">
                <p>${product.description || 'Premium quality gym wear designed for peak performance.'}</p>
            </div>
            
            <!-- Size Selector -->
            <div class="size-selector">
                <div class="size-selector-header">
                    <h4>Select Size</h4>
                    <a href="#" class="size-guide-link" onclick="showSizeGuide(event)">Size Guide</a>
                </div>
                <div class="size-options">
                    ${sizes.map(size => `
                        <button class="size-option ${stock[size] === 0 ? 'disabled' : ''}"
                                onclick="selectSize('${size}', this)"
                                ${stock[size] === 0 ? 'disabled' : ''}>
                            ${size}
                        </button>
                    `).join('')}
                </div>
            </div>
            
            <!-- Quantity -->
            <div class="quantity-selector">
                <h4>Quantity</h4>
                <div class="quantity-controls">
                    <button class="quantity-btn" onclick="updateQuantity(-1)">-</button>
                    <input type="number" class="quantity-input" value="1" min="1" max="10" id="quantityInput" readonly>
                    <button class="quantity-btn" onclick="updateQuantity(1)">+</button>
                </div>
            </div>
            
            <!-- Add to Cart -->
            <button class="btn btn-primary btn-lg add-to-cart-btn" onclick="addToCart()" id="addToCartBtn">
                Add to Cart
            </button>
            
            <!-- Product Meta -->
            <div class="product-meta">
                <div class="product-meta-item">
                    <span>Category:</span>
                    <span>${product.gender === 'men' ? "Men's" : "Women's"} ${product.category || 'Apparel'}</span>
                </div>
                <div class="product-meta-item">
                    <span>Availability:</span>
                    <span>${product.total_stock > 0 ? 'In Stock' : 'Out of Stock'}</span>
                </div>
            </div>
        </div>
    `;
}

/**
 * Change main image
 */
function changeImage(src, thumb) {
    document.getElementById('mainImage').src = src;
    document.querySelectorAll('.gallery-thumb').forEach(t => t.classList.remove('active'));
    thumb.classList.add('active');
}

/**
 * Select size
 */
function selectSize(size, btn) {
    selectedSize = size;
    document.querySelectorAll('.size-option').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

/**
 * Update quantity
 */
function updateQuantity(change) {
    const input = document.getElementById('quantityInput');
    let newQty = parseInt(input.value) + change;
    
    if (newQty < 1) newQty = 1;
    if (newQty > 10) newQty = 10;
    
    quantity = newQty;
    input.value = quantity;
}

/**
 * Add to cart
 */
function addToCart() {
    if (!selectedSize) {
        Hypercore.showToast('Please select a size', 'warning');
        return;
    }
    
    if (!currentProduct) return;
    
    const image = currentProduct.images && currentProduct.images.length > 0 
        ? currentProduct.images[0] 
        : 'assets/images/placeholder.jpg';
    
    Hypercore.addToCart({
        product_id: currentProduct.id,
        size: selectedSize,
        quantity: quantity,
        price: currentProduct.price,
        name: currentProduct.name,
        image: image
    });
}

/**
 * Render related products
 */
function renderRelatedProducts(products) {
    const container = document.getElementById('relatedProducts');
    
    if (!products || products.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = products.map(product => `
        <div class="product-card">
            <a href="/product.html?id=${product.id}" class="product-image">
                <img src="${product.images && product.images[0] ? product.images[0] : 'assets/images/placeholder.jpg'}" 
                     alt="${product.name}" loading="lazy">
            </a>
            <div class="product-info">
                <a href="/product.html?id=${product.id}">
                    <h3 class="product-name">${product.name}</h3>
                </a>
                <p class="product-price">${Hypercore.formatCurrency(product.price)}</p>
            </div>
        </div>
    `).join('');
}

/**
 * Show size guide modal
 */
function showSizeGuide(event) {
    event.preventDefault();
    
    const modal = document.createElement('div');
    modal.className = 'modal-overlay active';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">Size Guide</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button>
            </div>
            <div class="modal-body">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f5f5f5;">
                            <th style="padding: 12px; text-align: left;">Size</th>
                            <th style="padding: 12px; text-align: left;">Chest (in)</th>
                            <th style="padding: 12px; text-align: left;">Waist (in)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td style="padding: 12px; border-bottom: 1px solid #eee;">S</td><td style="padding: 12px; border-bottom: 1px solid #eee;">36-38</td><td style="padding: 12px; border-bottom: 1px solid #eee;">30-32</td></tr>
                        <tr><td style="padding: 12px; border-bottom: 1px solid #eee;">M</td><td style="padding: 12px; border-bottom: 1px solid #eee;">38-40</td><td style="padding: 12px; border-bottom: 1px solid #eee;">32-34</td></tr>
                        <tr><td style="padding: 12px; border-bottom: 1px solid #eee;">L</td><td style="padding: 12px; border-bottom: 1px solid #eee;">40-42</td><td style="padding: 12px; border-bottom: 1px solid #eee;">34-36</td></tr>
                        <tr><td style="padding: 12px; border-bottom: 1px solid #eee;">XL</td><td style="padding: 12px; border-bottom: 1px solid #eee;">42-44</td><td style="padding: 12px; border-bottom: 1px solid #eee;">36-38</td></tr>
                        <tr><td style="padding: 12px;">XXL</td><td style="padding: 12px;">44-46</td><td style="padding: 12px;">38-40</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };
    
    document.body.appendChild(modal);
}
