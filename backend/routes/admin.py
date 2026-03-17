"""
Admin Routes - Dashboard, analytics, and bulk operations
"""
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from models.database import db
from models.user import User
from models.product import Product
from models.order import Order
from utils.jwt_utils import require_admin

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard', methods=['GET'])
@require_admin
def get_dashboard():
    """
    Get admin dashboard data
    
    Returns:
        - Dashboard metrics and stats
    """
    # Date ranges
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Sales metrics
    today_sales = db.session.query(func.sum(Order.total)).filter(
        func.date(Order.created_at) == today,
        Order.payment_status == 'paid'
    ).scalar() or 0
    
    week_sales = db.session.query(func.sum(Order.total)).filter(
        func.date(Order.created_at) >= week_ago,
        Order.payment_status == 'paid'
    ).scalar() or 0
    
    month_sales = db.session.query(func.sum(Order.total)).filter(
        func.date(Order.created_at) >= month_ago,
        Order.payment_status == 'paid'
    ).scalar() or 0
    
    total_sales = db.session.query(func.sum(Order.total)).filter(
        Order.payment_status == 'paid'
    ).scalar() or 0
    
    # Order counts
    today_orders = Order.query.filter(func.date(Order.created_at) == today).count()
    pending_orders = Order.query.filter_by(status='processing').count()
    total_orders = Order.query.count()
    
    # Customer metrics
    total_customers = User.query.filter_by(role='customer').count()
    new_customers_this_month = User.query.filter(
        func.date(User.created_at) >= month_ago
    ).count()
    
    # Average order value
    avg_order_value = db.session.query(func.avg(Order.total)).filter(
        Order.payment_status == 'paid'
    ).scalar() or 0
    
    # Low stock products
    low_stock_products = []
    products = Product.query.filter_by(is_active=True).all()
    for product in products:
        stock = product.get_stock()
        total_stock = sum(stock.values())
        if total_stock < 10:
            low_stock_products.append({
                'id': product.id,
                'name': product.name,
                'stock': stock,
                'total_stock': total_stock
            })
    
    # Recent orders
    recent_orders = Order.query.order_by(desc(Order.created_at)).limit(5).all()
    
    return jsonify({
        'success': True,
        'metrics': {
            'sales': {
                'today': float(today_sales),
                'this_week': float(week_sales),
                'this_month': float(month_sales),
                'total': float(total_sales)
            },
            'orders': {
                'today': today_orders,
                'pending': pending_orders,
                'total': total_orders,
                'average_value': float(avg_order_value)
            },
            'customers': {
                'total': total_customers,
                'new_this_month': new_customers_this_month
            }
        },
        'low_stock': low_stock_products[:10],
        'recent_orders': [order.to_dict(include_items=False) for order in recent_orders]
    }), 200


@admin_bp.route('/analytics/sales', methods=['GET'])
@require_admin
def get_sales_analytics():
    """
    Get sales analytics data
    
    Query Parameters:
        - period: 'daily', 'weekly', 'monthly'
        - days: Number of days to analyze (default: 30)
    
    Returns:
        - Sales analytics data
    """
    period = request.args.get('period', 'daily')
    days = request.args.get('days', 30, type=int)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get paid orders within date range
    orders = Order.query.filter(
        Order.created_at >= start_date,
        Order.payment_status == 'paid'
    ).all()
    
    # Group by date
    from collections import defaultdict
    sales_by_date = defaultdict(lambda: {'count': 0, 'revenue': 0})
    
    for order in orders:
        date_key = order.created_at.strftime('%Y-%m-%d')
        sales_by_date[date_key]['count'] += 1
        sales_by_date[date_key]['revenue'] += float(order.total)
    
    # Fill in missing dates
    data = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
        data.append({
            'date': date,
            'orders': sales_by_date[date]['count'],
            'revenue': sales_by_date[date]['revenue']
        })
    
    data.reverse()
    
    return jsonify({
        'success': True,
        'period': period,
        'data': data
    }), 200


@admin_bp.route('/analytics/products', methods=['GET'])
@require_admin
def get_product_analytics():
    """
    Get top selling products
    
    Query Parameters:
        - limit: Number of products to return (default: 10)
    
    Returns:
        - Top selling products
    """
    from models.order import OrderItem
    
    limit = request.args.get('limit', 10, type=int)
    
    # Get top selling products
    top_products = db.session.query(
        Product.id,
        Product.name,
        func.sum(OrderItem.quantity).label('total_sold'),
        func.sum(OrderItem.quantity * OrderItem.price_at_time).label('total_revenue')
    ).join(
        OrderItem, Product.id == OrderItem.product_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.payment_status == 'paid'
    ).group_by(
        Product.id, Product.name
    ).order_by(
        desc('total_sold')
    ).limit(limit).all()
    
    return jsonify({
        'success': True,
        'top_products': [
            {
                'id': p.id,
                'name': p.name,
                'total_sold': int(p.total_sold),
                'total_revenue': float(p.total_revenue)
            }
            for p in top_products
        ]
    }), 200


@admin_bp.route('/inventory/bulk-update', methods=['POST'])
@require_admin
def bulk_update_inventory():
    """
    Bulk update product inventory
    
    Request Body:
        - updates: List of {product_id, stock} objects
    
    Returns:
        - Update results
    """
    data = request.get_json()
    
    if not data or 'updates' not in data:
        return jsonify({'error': 'Updates required'}), 400
    
    updates = data['updates']
    if not isinstance(updates, list):
        return jsonify({'error': 'Updates must be a list'}), 400
    
    success_count = 0
    errors = []
    
    try:
        for update in updates:
            product_id = update.get('product_id')
            stock = update.get('stock')
            
            if not product_id or not stock:
                errors.append({'product_id': product_id, 'error': 'Missing product_id or stock'})
                continue
            
            product = Product.query.get(product_id)
            if not product:
                errors.append({'product_id': product_id, 'error': 'Product not found'})
                continue
            
            try:
                product.set_stock(stock)
                success_count += 1
            except Exception as e:
                errors.append({'product_id': product_id, 'error': str(e)})
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated': success_count,
            'errors': errors if errors else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Bulk update error: {str(e)}")
        return jsonify({'error': 'Failed to update inventory'}), 500


@admin_bp.route('/inventory/import', methods=['POST'])
@require_admin
def import_inventory_csv():
    """
    Import inventory from CSV file
    
    Request:
        - CSV file with columns: product_id, size_S, size_M, size_L, size_XL, size_XXL
    
    Returns:
        - Import results
    """
    import csv
    import io
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV format'}), 400
    
    try:
        stream = io.StringIO(file.stream.read().decode('UTF-8'))
        csv_reader = csv.DictReader(stream)
        
        success_count = 0
        errors = []
        
        for row in csv_reader:
            product_id = row.get('product_id')
            if not product_id:
                continue
            
            product = Product.query.get(int(product_id))
            if not product:
                errors.append({'product_id': product_id, 'error': 'Product not found'})
                continue
            
            # Build stock dict from CSV columns
            stock = {}
            for size in ['S', 'M', 'L', 'XL', 'XXL']:
                key = f'size_{size}'
                if key in row:
                    try:
                        stock[size] = int(row[key])
                    except ValueError:
                        stock[size] = 0
            
            try:
                product.set_stock(stock)
                success_count += 1
            except Exception as e:
                errors.append({'product_id': product_id, 'error': str(e)})
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'imported': success_count,
            'errors': errors if errors else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"CSV import error: {str(e)}")
        return jsonify({'error': 'Failed to import CSV'}), 500


@admin_bp.route('/orders/packing-slip/<int:order_id>', methods=['GET'])
@require_admin
def get_packing_slip(order_id):
    """
    Get packing slip for order (Admin only)
    
    Args:
        order_id: Order ID
    
    Returns:
        - Packing slip data
    """
    order = Order.query.get_or_404(order_id)
    
    slip = {
        'order_number': order.order_number,
        'date': order.created_at.strftime('%Y-%m-%d'),
        'customer': {
            'name': order.user.name if order.user else 'Guest',
            'email': order.user.email if order.user else '',
            'phone': order.user.phone if order.user else ''
        },
        'delivery_address': order.get_delivery_address(),
        'items': order.get_items(),
        'totals': {
            'subtotal': float(order.subtotal),
            'delivery_fee': float(order.delivery_fee),
            'total': float(order.total)
        },
        'notes': order.customer_notes
    }
    
    return jsonify({
        'success': True,
        'packing_slip': slip
    }), 200


@admin_bp.route('/customers/email', methods=['POST'])
@require_admin
def send_customer_email():
    """
    Send email to customers (Admin only)
    
    Request Body:
        - recipient_type: 'all', 'recent', or 'specific'
        - user_ids: List of user IDs (for 'specific')
        - subject: Email subject
        - message: Email message (HTML)
    
    Returns:
        - Send results
    """
    from services.email_service import email_service
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    recipient_type = data.get('recipient_type')
    subject = data.get('subject')
    message = data.get('message')
    
    if not recipient_type or not subject or not message:
        return jsonify({'error': 'recipient_type, subject, and message are required'}), 400
    
    # Get recipients
    if recipient_type == 'all':
        users = User.query.filter_by(role='customer', is_active=True).all()
    elif recipient_type == 'recent':
        # Customers who ordered in last 30 days
        month_ago = datetime.utcnow() - timedelta(days=30)
        users = User.query.join(Order).filter(
            Order.created_at >= month_ago
        ).distinct().all()
    elif recipient_type == 'specific':
        user_ids = data.get('user_ids', [])
        users = User.query.filter(User.id.in_(user_ids)).all()
    else:
        return jsonify({'error': 'Invalid recipient_type'}), 400
    
    # Send emails
    sent_count = 0
    errors = []
    
    for user in users:
        try:
            result = email_service.send_email(user.email, subject, message)
            if result['success']:
                sent_count += 1
            else:
                errors.append({'email': user.email, 'error': result.get('error')})
        except Exception as e:
            errors.append({'email': user.email, 'error': str(e)})
    
    return jsonify({
        'success': True,
        'sent': sent_count,
        'total_recipients': len(users),
        'errors': errors if errors else None
    }), 200
