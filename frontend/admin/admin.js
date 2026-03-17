/**
 * Admin Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    checkAdminAuth();
    loadDashboard();
});

/**
 * Check admin authentication
 */
function checkAdminAuth() {
    if (!Hypercore.isLoggedIn()) {
        window.location.href = '/login.html?redirect=admin';
        return;
    }
    
    if (!Hypercore.isAdmin()) {
        window.location.href = '/';
        return;
    }
    
    // Update admin name
    const user = Hypercore.getUser();
    document.getElementById('adminName').textContent = user.name;
}

/**
 * Load dashboard data
 */
async function loadDashboard() {
    try {
        const response = await Hypercore.apiRequest('/admin/dashboard');
        
        if (response.success) {
            // Update stats
            document.getElementById('todaySales').textContent = Hypercore.formatCurrencyShort(response.metrics.sales.today);
            document.getElementById('todayOrders').textContent = response.metrics.orders.today;
            document.getElementById('monthSales').textContent = Hypercore.formatCurrencyShort(response.metrics.sales.this_month);
            document.getElementById('totalCustomers').textContent = response.metrics.customers.total;
            
            // Render recent orders
            renderRecentOrders(response.recent_orders);
            
            // Render low stock
            renderLowStock(response.low_stock);
        }
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

/**
 * Render recent orders
 */
function renderRecentOrders(orders) {
    const tbody = document.getElementById('recentOrders');
    
    if (!orders || orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">No orders yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = orders.map(order => `
        <tr>
            <td>${order.order_number}</td>
            <td>${order.user?.name || 'Guest'}</td>
            <td>${Hypercore.formatCurrency(order.total)}</td>
            <td><span class="status-badge ${order.status}">${order.status}</span></td>
        </tr>
    `).join('');
}

/**
 * Render low stock items
 */
function renderLowStock(items) {
    const container = document.getElementById('lowStock');
    
    if (!items || items.length === 0) {
        container.innerHTML = '<p class="text-gray">All products well stocked</p>';
        return;
    }
    
    container.innerHTML = items.map(item => `
        <div class="flex justify-between items-center py-2 border-bottom">
            <span>${item.name}</span>
            <span class="badge badge-error">${item.total_stock} left</span>
        </div>
    `).join('');
}

/**
 * Show section
 */
function showSection(section) {
    // Update nav
    document.querySelectorAll('.admin-nav-link').forEach(l => l.classList.remove('active'));
    event.target.classList.add('active');
    
    // Hide all sections
    document.querySelectorAll('.admin-section').forEach(s => s.classList.add('hidden'));
    
    // Show selected section
    document.getElementById(section + 'Section').classList.remove('hidden');
    
    // Update title
    const titles = {
        dashboard: 'Dashboard',
        products: 'Products',
        orders: 'Orders',
        customers: 'Customers'
    };
    document.getElementById('pageTitle').textContent = titles[section];
    
    // Load section data
    if (section === 'products') loadProducts();
    if (section === 'orders') loadOrders();
    if (section === 'customers') loadCustomers();
}

/**
 * Load products
 */
async function loadProducts() {
    try {
        const response = await Hypercore.apiRequest('/products/?per_page=100');
        
        if (response.success) {
            const tbody = document.getElementById('productsTable');
            tbody.innerHTML = response.products.map(product => `
                <tr>
                    <td><img src="${product.images?.[0] || '../assets/images/placeholder.jpg'}" alt="" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;"></td>
                    <td>${product.name}</td>
                    <td>${Hypercore.formatCurrency(product.price)}</td>
                    <td>${product.total_stock}</td>
                    <td>
                        <button class="btn btn-sm btn-outline" onclick="editProduct(${product.id})">Edit</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load products:', error);
    }
}

/**
 * Load orders
 */
async function loadOrders(status = '') {
    try {
        const url = status ? `/admin/all?status=${status}` : '/admin/all';
        const response = await Hypercore.apiRequest(url);
        
        if (response.success) {
            const tbody = document.getElementById('ordersTable');
            tbody.innerHTML = response.orders.map(order => `
                <tr>
                    <td>${order.order_number}</td>
                    <td>${order.user?.name || 'Guest'}</td>
                    <td>${Hypercore.formatDate(order.created_at)}</td>
                    <td>${Hypercore.formatCurrency(order.total)}</td>
                    <td><span class="status-badge ${order.status}">${order.status}</span></td>
                    <td>
                        <select class="form-select form-select-sm" onchange="updateOrderStatus(${order.id}, this.value)">
                            <option value="">Update Status</option>
                            <option value="processing">Processing</option>
                            <option value="paid">Paid</option>
                            <option value="shipped">Shipped</option>
                            <option value="delivered">Delivered</option>
                        </select>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load orders:', error);
    }
}

/**
 * Load customers
 */
async function loadCustomers() {
    try {
        const response = await Hypercore.apiRequest('/users/admin/all');
        
        if (response.success) {
            const tbody = document.getElementById('customersTable');
            tbody.innerHTML = response.users.map(user => `
                <tr>
                    <td>${user.name}</td>
                    <td>${user.email}</td>
                    <td>${user.phone || '-'}</td>
                    <td>-</td>
                    <td>${Hypercore.formatDate(user.created_at)}</td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load customers:', error);
    }
}

/**
 * Filter orders
 */
function filterOrders() {
    const status = document.getElementById('orderFilter').value;
    loadOrders(status);
}

/**
 * Update order status
 */
async function updateOrderStatus(orderId, status) {
    if (!status) return;
    
    try {
        const response = await Hypercore.apiRequest(`/orders/admin/${orderId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
        
        if (response.success) {
            Hypercore.showToast('Order status updated', 'success');
            loadOrders();
        }
    } catch (error) {
        Hypercore.showToast('Failed to update status', 'error');
    }
}

/**
 * Export customers
 */
function exportCustomers() {
    window.open(`${Hypercore.API_BASE_URL}/users/admin/export`, '_blank');
}

/**
 * Show add product modal
 */
function showAddProductModal() {
    // Implementation for adding product
    Hypercore.showToast('Add product feature coming soon', 'info');
}

/**
 * Edit product
 */
function editProduct(productId) {
    // Implementation for editing product
    Hypercore.showToast('Edit product feature coming soon', 'info');
}
