"""
Orders Routes - Order management and checkout
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from models.database import db
from models.order import Order, OrderItem
from models.cart import CartItem
from models.product import Product
from utils.jwt_utils import require_auth, require_admin
from utils.validation import validate_delivery_address, validate_delivery_zone
from utils.helpers import generate_order_number, calculate_delivery_fee, calculate_delivery_estimate
from services.paystack_service import PaystackService, amount_to_kobo
from services.email_service import email_service

orders_bp = Blueprint('orders', __name__)
paystack_service = PaystackService()


@orders_bp.route('/', methods=['GET'])
@require_auth
def get_orders():
    """
    Get user's orders
    
    Query Parameters:
        - status: Filter by status
        - page: Page number
        - per_page: Items per page
    
    Returns:
        - List of orders
    """
    user = request.current_user
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Order.query.filter_by(user_id=user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(Order.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'orders': [order.to_dict() for order in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'total_pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@orders_bp.route('/<int:order_id>', methods=['GET'])
@require_auth
def get_order(order_id):
    """
    Get single order details
    
    Args:
        order_id: Order ID
    
    Returns:
        - Order details
    """
    user = request.current_user
    order = Order.query.filter_by(id=order_id, user_id=user.id).first()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify({
        'success': True,
        'order': order.to_dict()
    }), 200


@orders_bp.route('/checkout', methods=['POST'])
@require_auth
def create_checkout():
    """
    Create checkout session and initialize payment
    
    Request Body:
        - delivery_address: Delivery address object
        - delivery_zone: 'island', 'mainland', or 'outside'
        - customer_notes: Optional notes
    
    Returns:
        - Order details and Paystack payment info
    """
    user = request.current_user
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate delivery address
    address = data.get('delivery_address')
    is_valid, error = validate_delivery_address(address)
    if not is_valid:
        return jsonify({'error': error}), 400
    
    # Validate delivery zone
    zone = data.get('delivery_zone')
    is_valid, zone = validate_delivery_zone(zone)
    if not is_valid:
        return jsonify({'error': zone}), 400
    
    # Get cart items
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Validate cart items (check stock)
    for item in cart_items:
        product = item.product
        if not product or not product.is_active:
            return jsonify({'error': f'Product "{product.name if product else "Unknown"}" is no longer available'}), 400
        
        stock = product.get_stock()
        if stock.get(item.size, 0) < item.quantity:
            return jsonify({'error': f'Not enough stock for {product.name} (size {item.size}). Available: {stock.get(item.size, 0)}'}), 400
    
    # Calculate totals
    subtotal = sum(float(item.product.price) * item.quantity for item in cart_items)
    delivery_fee = calculate_delivery_fee(zone)
    total = subtotal + delivery_fee
    
    # Prepare order items
    order_items_data = []
    for item in cart_items:
        order_items_data.append({
            'product_id': item.product_id,
            'name': item.product.name,
            'price': float(item.product.price),
            'quantity': item.quantity,
            'size': item.size,
            'image': item.product.get_images()[0] if item.product.get_images() else None
        })
    
    # Generate order number
    order_number = generate_order_number()
    
    try:
        # Create order
        order = Order(
            user_id=user.id,
            items=order_items_data,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=total,
            delivery_address=address,
            delivery_zone=zone,
            order_number=order_number,
            customer_notes=data.get('customer_notes', '')
        )
        
        # Calculate estimated delivery date
        delivery_estimate = calculate_delivery_estimate(zone)
        order.estimated_delivery_date = datetime.strptime(delivery_estimate['max_date'], '%Y-%m-%d').date()
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                size=item.size,
                price_at_time=item.product.price,
                product_name=item.product.name,
                product_image=item.product.get_images()[0] if item.product.get_images() else None
            )
            db.session.add(order_item)
            
            # Decrease stock
            item.product.decrease_stock(item.size, item.quantity)
        
        db.session.commit()
        
        # Initialize Paystack transaction
        callback_url = f"{request.host_url.rstrip('/')}/payment/callback"
        metadata = {
            'order_id': order.id,
            'order_number': order.order_number,
            'user_id': user.id
        }
        
        paystack_response = paystack_service.initialize_transaction(
            email=user.email,
            amount=amount_to_kobo(total),
            reference=order_number,
            callback_url=callback_url,
            metadata=metadata
        )
        
        if not paystack_response.get('status'):
            # Rollback order creation if payment initialization fails
            db.session.delete(order)
            db.session.commit()
            return jsonify({
                'error': 'Failed to initialize payment',
                'details': paystack_response.get('message')
            }), 500
        
        # Clear cart after successful order creation
        CartItem.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order': order.to_dict(),
            'payment': {
                'authorization_url': paystack_response['data']['authorization_url'],
                'reference': paystack_response['data']['reference'],
                'public_key': current_app.config.get('PAYSTACK_PUBLIC_KEY')
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Checkout error: {str(e)}")
        return jsonify({'error': 'Failed to create order'}), 500


@orders_bp.route('/verify-payment', methods=['POST'])
@require_auth
def verify_payment():
    """
    Verify payment after Paystack callback
    
    Request Body:
        - reference: Paystack transaction reference
    
    Returns:
        - Payment verification result
    """
    data = request.get_json()
    
    if not data or 'reference' not in data:
        return jsonify({'error': 'Reference is required'}), 400
    
    reference = data['reference']
    
    # Verify with Paystack
    verification = paystack_service.verify_transaction(reference)
    
    if not verification.get('status'):
        return jsonify({
            'error': 'Payment verification failed',
            'details': verification.get('message')
        }), 400
    
    transaction_data = verification.get('data', {})
    
    if transaction_data.get('status') != 'success':
        return jsonify({
            'error': 'Payment was not successful',
            'status': transaction_data.get('status')
        }), 400
    
    # Find order
    order = Order.query.filter_by(order_number=reference).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    try:
        # Mark order as paid
        order.mark_as_paid(
            paystack_ref=transaction_data.get('reference'),
            paystack_transaction_id=str(transaction_data.get('id'))
        )
        db.session.commit()
        
        # Send payment confirmation email
        user = order.user
        email_service.send_payment_received(user.email, user.name, order)
        email_service.send_order_confirmation(user.email, user.name, order)
        
        return jsonify({
            'success': True,
            'message': 'Payment verified successfully',
            'order': order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Payment verification error: {str(e)}")
        return jsonify({'error': 'Failed to verify payment'}), 500


@orders_bp.route('/track/<order_number>', methods=['GET'])
def track_order(order_number):
    """
    Track order by order number (public endpoint)
    
    Args:
        order_number: Order number
    
    Returns:
        - Order tracking info
    """
    order = Order.query.filter_by(order_number=order_number).first()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify({
        'success': True,
        'order_number': order.order_number,
        'status': order.status,
        'tracking_number': order.tracking_number,
        'estimated_delivery': order.estimated_delivery_date.isoformat() if order.estimated_delivery_date else None,
        'shipped_at': order.shipped_at.isoformat() if order.shipped_at else None,
        'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None
    }), 200


# Admin Routes

@orders_bp.route('/admin/all', methods=['GET'])
@require_admin
def get_all_orders():
    """
    Get all orders (Admin only)
    
    Query Parameters:
        - status: Filter by status
        - page: Page number
        - per_page: Items per page
    
    Returns:
        - List of all orders
    """
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(Order.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'orders': [order.to_dict() for order in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'total_pages': pagination.pages
        }
    }), 200


@orders_bp.route('/admin/<int:order_id>/status', methods=['PUT'])
@require_admin
def update_order_status(order_id):
    """
    Update order status (Admin only)
    
    Args:
        order_id: Order ID
    
    Request Body:
        - status: New status
        - tracking_number: (optional) Tracking number for shipped orders
    
    Returns:
        - Updated order
    """
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
    
    new_status = data['status']
    tracking_number = data.get('tracking_number')
    
    try:
        order.update_status(new_status, tracking_number)
        db.session.commit()
        
        # Send appropriate email notification
        user = order.user
        if new_status == Order.STATUS_SHIPPED:
            email_service.send_order_shipped(user.email, user.name, order)
        elif new_status == Order.STATUS_DELIVERED:
            email_service.send_order_delivered(user.email, user.name, order)
        
        return jsonify({
            'success': True,
            'order': order.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Order status update error: {str(e)}")
        return jsonify({'error': 'Failed to update order status'}), 500


@orders_bp.route('/admin/<int:order_id>', methods=['GET'])
@require_admin
def get_admin_order(order_id):
    """
    Get order details for admin (Admin only)
    
    Args:
        order_id: Order ID
    
    Returns:
        - Full order details with user info
    """
    order = Order.query.get_or_404(order_id)
    
    order_data = order.to_dict()
    order_data['user'] = order.user.to_dict() if order.user else None
    
    return jsonify({
        'success': True,
        'order': order_data
    }), 200
