/**
 * Account Page JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadProfile();
    setupForms();
});

/**
 * Check if user is logged in
 */
function checkAuth() {
    if (!Hypercore.isLoggedIn()) {
        window.location.href = '/login.html?redirect=account';
        return;
    }
}

/**
 * Load user profile
 */
async function loadProfile() {
    try {
        const response = await Hypercore.apiRequest('/users/profile');
        
        if (response.success) {
            const user = response.profile;
            
            // Update sidebar
            document.getElementById('userName').textContent = user.name;
            document.getElementById('userEmail').textContent = user.email;
            document.getElementById('userAvatar').textContent = getInitials(user.name);
            
            // Update profile form
            document.getElementById('profileName').value = user.name || '';
            document.getElementById('profileEmail').value = user.email || '';
            document.getElementById('profilePhone').value = user.phone || '';
            
            // Update address form
            if (user.address) {
                document.getElementById('addressStreet').value = user.address.street || '';
                document.getElementById('addressCity').value = user.address.city || '';
                document.getElementById('addressLandmark').value = user.address.landmark || '';
            }
            
            // Load orders
            loadOrders();
        }
    } catch (error) {
        console.error('Failed to load profile:', error);
    }
}

/**
 * Get initials from name
 */
function getInitials(name) {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

/**
 * Load user orders
 */
async function loadOrders() {
    try {
        const response = await Hypercore.apiRequest('/orders/');
        
        if (response.success) {
            const container = document.getElementById('ordersList');
            
            if (response.orders.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📦</div>
                        <h3 class="empty-state-title">No orders yet</h3>
                        <p class="empty-state-text">Start shopping to see your orders here</p>
                        <a href="/shop.html" class="btn btn-primary">Shop Now</a>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = response.orders.map(order => `
                <div class="order-card">
                    <div class="order-header">
                        <div>
                            <p class="order-number">${order.order_number}</p>
                            <p class="order-date">${Hypercore.formatDate(order.created_at)}</p>
                        </div>
                        <span class="order-status ${order.status}">${order.status}</span>
                    </div>
                    <div class="order-items">
                        ${order.items.slice(0, 3).map(item => `
                            <div class="order-item">
                                <span class="order-item-name">${item.name}</span>
                                <span class="order-item-meta">${item.size} × ${item.quantity}</span>
                                <span class="order-item-price">${Hypercore.formatCurrency(item.price * item.quantity)}</span>
                            </div>
                        `).join('')}
                        ${order.items.length > 3 ? `<p>+${order.items.length - 3} more items</p>` : ''}
                    </div>
                    <div class="order-footer">
                        <p class="order-total">Total: <span>${Hypercore.formatCurrency(order.total)}</span></p>
                        <a href="/order.html?id=${order.id}" class="btn btn-sm btn-outline">View Details</a>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load orders:', error);
    }
}

/**
 * Setup form handlers
 */
function setupForms() {
    // Profile form
    document.getElementById('profileForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const name = document.getElementById('profileName').value;
        const phone = document.getElementById('profilePhone').value;
        
        try {
            const response = await Hypercore.apiRequest('/auth/profile', {
                method: 'PUT',
                body: JSON.stringify({ name, phone })
            });
            
            if (response.success) {
                Hypercore.setUser(response.user);
                document.getElementById('userName').textContent = response.user.name;
                Hypercore.showToast('Profile updated successfully', 'success');
            }
        } catch (error) {
            Hypercore.showToast('Failed to update profile', 'error');
        }
    });
    
    // Address form
    document.getElementById('addressForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const address = {
            street: document.getElementById('addressStreet').value,
            city: document.getElementById('addressCity').value,
            state: document.getElementById('addressState').value,
            landmark: document.getElementById('addressLandmark').value
        };
        
        try {
            const response = await Hypercore.apiRequest('/users/address', {
                method: 'PUT',
                body: JSON.stringify(address)
            });
            
            if (response.success) {
                Hypercore.showToast('Address saved successfully', 'success');
            }
        } catch (error) {
            Hypercore.showToast('Failed to save address', 'error');
        }
    });
}

/**
 * Show account section
 */
function showSection(section) {
    // Hide all sections
    document.querySelectorAll('.account-section').forEach(s => s.classList.add('hidden'));
    
    // Show selected section
    document.getElementById(section + 'Section').classList.remove('hidden');
    
    // Update nav
    document.querySelectorAll('.account-nav-link').forEach(l => l.classList.remove('active'));
    event.target.classList.add('active');
}
