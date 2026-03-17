/**
 * Cart Page JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    renderCart();
});

/**
 * Render cart
 */
function renderCart() {
    const container = document.getElementById('cartLayout');
    const cart = Hypercore.getCart();
    
    if (cart.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🛒</div>
                <h3 class="empty-state-title">Your cart is empty</h3>
                <p class="empty-state-text">Looks like you haven't added anything yet</p>
                <a href="/shop.html" class="btn btn-primary">Start Shopping</a>
            </div>
        `;
        return;
    }
    
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const deliveryFee = 2000; // Default mainland
    const total = subtotal + deliveryFee;
    
    container.innerHTML = `
        <!-- Cart Items -->
        <div class="cart-items">
            ${cart.map(item => `
                <div class="cart-item">
                    <div class="cart-item-image">
                        <img src="${item.image || 'assets/images/placeholder.jpg'}" alt="${item.name}">
                    </div>
                    <div class="cart-item-details">
                        <h4 class="cart-item-name">${item.name}</h4>
                        <p class="cart-item-meta">Size: ${item.size}</p>
                        <p class="cart-item-price">${Hypercore.formatCurrency(item.price)}</p>
                        <div class="cart-item-actions">
                            <div class="quantity-controls">
                                <button class="quantity-btn" onclick="updateItemQty(${item.product_id}, '${item.size}', -1)">-</button>
                                <input type="number" class="quantity-input" value="${item.quantity}" readonly>
                                <button class="quantity-btn" onclick="updateItemQty(${item.product_id}, '${item.size}', 1)">+</button>
                            </div>
                            <button class="cart-item-remove" onclick="removeItem(${item.product_id}, '${item.size}')">Remove</button>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
        
        <!-- Cart Summary -->
        <div class="cart-summary">
            <h3>Order Summary</h3>
            
            <div class="summary-row">
                <span>Subtotal</span>
                <span>${Hypercore.formatCurrency(subtotal)}</span>
            </div>
            
            <div class="summary-row">
                <span>Delivery</span>
                <span>${Hypercore.formatCurrency(deliveryFee)}</span>
            </div>
            
            <div class="summary-row total">
                <span>Total</span>
                <span>${Hypercore.formatCurrency(total)}</span>
            </div>
            
            <a href="/checkout.html" class="btn btn-primary btn-lg checkout-btn">Proceed to Checkout</a>
            <a href="/shop.html" class="continue-shopping">← Continue Shopping</a>
        </div>
    `;
}

/**
 * Update item quantity
 */
function updateItemQty(productId, size, change) {
    const cart = Hypercore.getCart();
    const item = cart.find(i => i.product_id === productId && i.size === size);
    
    if (item) {
        const newQty = item.quantity + change;
        if (newQty > 0 && newQty <= 10) {
            Hypercore.updateCartQuantity(productId, size, newQty);
            renderCart();
        }
    }
}

/**
 * Remove item from cart
 */
function removeItem(productId, size) {
    Hypercore.removeFromCart(productId, size);
    renderCart();
    Hypercore.showToast('Item removed from cart', 'info');
}
