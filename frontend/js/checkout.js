/**
 * Checkout Page JavaScript
 */

let cartItems = [];
let deliveryFee = 2000;

// Delivery fees
const DELIVERY_FEES = {
    island: 2500,
    mainland: 2000,
    outside: 5000
};

document.addEventListener('DOMContentLoaded', () => {
    loadCartItems();
    loadUserInfo();
});

/**
 * Load cart items
 */
function loadCartItems() {
    cartItems = Hypercore.getCart();
    
    if (cartItems.length === 0) {
        window.location.href = '/cart.html';
        return;
    }
    
    renderSummary();
}

/**
 * Load user info if logged in
 */
async function loadUserInfo() {
    if (!Hypercore.isLoggedIn()) return;
    
    try {
        const response = await Hypercore.apiRequest('/users/profile');
        
        if (response.success) {
            const user = response.profile;
            
            // Fill contact info
            document.getElementById('email').value = user.email || '';
            document.getElementById('phone').value = user.phone || '';
            
            // Fill address if available
            if (user.address) {
                document.getElementById('street').value = user.address.street || '';
                document.getElementById('city').value = user.address.city || '';
                document.getElementById('landmark').value = user.address.landmark || '';
            }
            
            // Hide contact section if we have email
            if (user.email) {
                document.getElementById('contactInfo').innerHTML = `
                    <p>${user.email}</p>
                    <a href="#" onclick="showContactForm()">Change</a>
                `;
            }
        }
    } catch (error) {
        console.error('Failed to load user info:', error);
    }
}

/**
 * Render order summary
 */
function renderSummary() {
    const container = document.getElementById('summaryItems');
    
    container.innerHTML = cartItems.map(item => `
        <div class="summary-item">
            <div class="summary-item-image">
                <img src="${item.image || 'assets/images/placeholder.jpg'}" alt="${item.name}">
            </div>
            <div class="summary-item-details">
                <p class="summary-item-name">${item.name}</p>
                <p class="summary-item-meta">Size: ${item.size} × ${item.quantity}</p>
            </div>
            <span class="summary-item-price">${Hypercore.formatCurrency(item.price * item.quantity)}</span>
        </div>
    `).join('');
    
    updateTotals();
}

/**
 * Update delivery fee
 */
function updateDeliveryFee() {
    const zone = document.querySelector('input[name="delivery_zone"]:checked').value;
    deliveryFee = DELIVERY_FEES[zone];
    document.getElementById('deliveryFee').textContent = Hypercore.formatCurrency(deliveryFee);
    updateTotals();
}

/**
 * Update totals
 */
function updateTotals() {
    const subtotal = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const total = subtotal + deliveryFee;
    
    document.getElementById('subtotal').textContent = Hypercore.formatCurrency(subtotal);
    document.getElementById('total').textContent = Hypercore.formatCurrency(total);
}

/**
 * Process checkout
 */
async function processCheckout() {
    const btn = document.getElementById('checkoutBtn');
    const originalText = btn.textContent;
    
    // Validate form
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const street = document.getElementById('street').value;
    const city = document.getElementById('city').value;
    const state = document.getElementById('state').value;
    const landmark = document.getElementById('landmark').value;
    const zone = document.querySelector('input[name="delivery_zone"]:checked').value;
    
    if (!email || !phone || !street || !city) {
        Hypercore.showToast('Please fill in all required fields', 'error');
        return;
    }
    
    if (!Hypercore.isValidEmail(email)) {
        Hypercore.showToast('Please enter a valid email', 'error');
        return;
    }
    
    // Show loading
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner spinner-sm"></div> Processing...';
    
    // If not logged in, need to handle guest checkout or redirect to login
    if (!Hypercore.isLoggedIn()) {
        // Store checkout data and redirect to login
        sessionStorage.setItem('checkout_data', JSON.stringify({
            email, phone, address: { street, city, state, landmark },
            zone, items: cartItems
        }));
        window.location.href = '/login.html?redirect=checkout';
        return;
    }
    
    try {
        // Create checkout
        const response = await Hypercore.apiRequest('/orders/checkout', {
            method: 'POST',
            body: JSON.stringify({
                delivery_address: {
                    street,
                    city,
                    state,
                    landmark,
                    phone
                },
                delivery_zone: zone,
                customer_notes: ''
            })
        });
        
        if (response.success) {
            // Initialize Paystack payment
            const paystackConfig = {
                key: response.payment.public_key,
                email: email,
                amount: Math.round(parseFloat(response.order.total) * 100), // Convert to kobo
                ref: response.payment.reference,
                callback: function(response) {
                    verifyPayment(response.reference);
                },
                onClose: function() {
                    btn.disabled = false;
                    btn.textContent = originalText;
                    Hypercore.showToast('Payment cancelled', 'warning');
                }
            };
            
            const handler = PaystackPop.setup(paystackConfig);
            handler.openIframe();
        } else {
            throw new Error(response.error || 'Checkout failed');
        }
    } catch (error) {
        console.error('Checkout error:', error);
        Hypercore.showToast(error.message || 'Checkout failed. Please try again.', 'error');
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

/**
 * Verify payment
 */
async function verifyPayment(reference) {
    try {
        const response = await Hypercore.apiRequest('/orders/verify-payment', {
            method: 'POST',
            body: JSON.stringify({ reference })
        });
        
        if (response.success) {
            // Clear cart
            Hypercore.clearCart();
            
            // Redirect to success page
            window.location.href = `/order-success.html?order=${response.order.order_number}`;
        } else {
            throw new Error(response.error || 'Payment verification failed');
        }
    } catch (error) {
        console.error('Payment verification error:', error);
        Hypercore.showToast(error.message || 'Payment verification failed', 'error');
    }
}

/**
 * Show contact form
 */
function showContactForm() {
    document.getElementById('contactInfo').innerHTML = `
        <div class="form-group">
            <label class="form-label">Email</label>
            <input type="email" class="form-input" id="email" placeholder="your@email.com">
        </div>
        <div class="form-group">
            <label class="form-label">Phone Number</label>
            <input type="tel" class="form-input" id="phone" placeholder="08012345678">
        </div>
    `;
}
