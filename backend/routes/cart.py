"""
Cart Routes - Shopping cart management
"""
from flask import Blueprint, request, jsonify, current_app
from models.database import db
from models.cart import CartItem
from models.product import Product
from utils.jwt_utils import require_auth, optional_auth
from utils.validation import validate_quantity, validate_size

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/', methods=['GET'])
@optional_auth
def get_cart():
    """
    Get user's cart items
    
    Returns:
        - Cart items and totals
    """
    if hasattr(request, 'current_user') and request.current_user:
        # Get cart from database for logged-in user
        cart_items = CartItem.query.filter_by(user_id=request.current_user.id).all()
        items = [item.to_dict() for item in cart_items]
        
        # Calculate totals
        subtotal = sum(item.get_subtotal() for item in cart_items)
    else:
        # Return empty cart for guests (they use localStorage)
        items = []
        subtotal = 0
    
    return jsonify({
        'success': True,
        'items': items,
        'summary': {
            'item_count': len(items),
            'subtotal': round(subtotal, 2)
        }
    }), 200


@cart_bp.route('/add', methods=['POST'])
@require_auth
def add_to_cart():
    """
    Add item to cart
    
    Request Body:
        - product_id: Product ID
        - quantity: Quantity (default: 1)
        - size: Size (required)
    
    Returns:
        - Updated cart
    """
    user = request.current_user
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    product_id = data.get('product_id')
    size = data.get('size')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return jsonify({'error': 'Product ID is required'}), 400
    
    if not size:
        return jsonify({'error': 'Size is required'}), 400
    
    # Validate size
    is_valid, size = validate_size(size)
    if not is_valid:
        return jsonify({'error': size}), 400
    
    # Validate quantity
    is_valid, quantity = validate_quantity(quantity, max_quantity=10)
    if not is_valid:
        return jsonify({'error': quantity}), 400
    
    # Get product
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if not product.is_active:
        return jsonify({'error': 'Product is not available'}), 400
    
    # Check if size is available
    available_sizes = product.get_sizes()
    if size not in available_sizes:
        return jsonify({'error': f'Size {size} not available for this product'}), 400
    
    # Check stock
    stock = product.get_stock()
    if stock.get(size, 0) < quantity:
        return jsonify({'error': f'Not enough stock for size {size}. Available: {stock.get(size, 0)}'}), 400
    
    try:
        # Check if item already in cart
        cart_item = CartItem.query.filter_by(
            user_id=user.id,
            product_id=product_id,
            size=size
        ).first()
        
        if cart_item:
            # Update quantity
            new_quantity = cart_item.quantity + quantity
            if new_quantity > 10:
                return jsonify({'error': 'Maximum quantity per item is 10'}), 400
            
            # Check stock again
            if stock.get(size, 0) < new_quantity:
                return jsonify({'error': f'Not enough stock. Available: {stock.get(size, 0)}'}), 400
            
            cart_item.quantity = new_quantity
        else:
            # Create new cart item
            cart_item = CartItem(
                user_id=user.id,
                product_id=product_id,
                quantity=quantity,
                size=size
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item added to cart',
            'cart_item': cart_item.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Add to cart error: {str(e)}")
        return jsonify({'error': 'Failed to add item to cart'}), 500


@cart_bp.route('/update/<int:item_id>', methods=['PUT'])
@require_auth
def update_cart_item(item_id):
    """
    Update cart item quantity
    
    Args:
        item_id: Cart item ID
    
    Request Body:
        - quantity: New quantity
    
    Returns:
        - Updated cart item
    """
    user = request.current_user
    cart_item = CartItem.query.filter_by(id=item_id, user_id=user.id).first()
    
    if not cart_item:
        return jsonify({'error': 'Cart item not found'}), 404
    
    data = request.get_json()
    if not data or 'quantity' not in data:
        return jsonify({'error': 'Quantity is required'}), 400
    
    # Validate quantity
    is_valid, quantity = validate_quantity(data['quantity'], max_quantity=10)
    if not is_valid:
        return jsonify({'error': quantity}), 400
    
    # Check stock
    product = cart_item.product
    stock = product.get_stock()
    if stock.get(cart_item.size, 0) < quantity:
        return jsonify({'error': f'Not enough stock. Available: {stock.get(cart_item.size, 0)}'}), 400
    
    try:
        if quantity <= 0:
            # Remove item if quantity is 0
            db.session.delete(cart_item)
        else:
            cart_item.quantity = quantity
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cart updated' if quantity > 0 else 'Item removed',
            'cart_item': cart_item.to_dict() if quantity > 0 else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update cart error: {str(e)}")
        return jsonify({'error': 'Failed to update cart'}), 500


@cart_bp.route('/remove/<int:item_id>', methods=['DELETE'])
@require_auth
def remove_from_cart(item_id):
    """
    Remove item from cart
    
    Args:
        item_id: Cart item ID
    
    Returns:
        - Success message
    """
    user = request.current_user
    cart_item = CartItem.query.filter_by(id=item_id, user_id=user.id).first()
    
    if not cart_item:
        return jsonify({'error': 'Cart item not found'}), 404
    
    try:
        db.session.delete(cart_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item removed from cart'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Remove from cart error: {str(e)}")
        return jsonify({'error': 'Failed to remove item'}), 500


@cart_bp.route('/clear', methods=['DELETE'])
@require_auth
def clear_cart():
    """
    Clear all items from cart
    
    Returns:
        - Success message
    """
    user = request.current_user
    
    try:
        CartItem.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cart cleared'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Clear cart error: {str(e)}")
        return jsonify({'error': 'Failed to clear cart'}), 500


@cart_bp.route('/sync', methods=['POST'])
@require_auth
def sync_cart():
    """
    Sync localStorage cart with database (for when user logs in)
    
    Request Body:
        - items: List of cart items from localStorage
            [{product_id, quantity, size}]
    
    Returns:
        - Synced cart
    """
    user = request.current_user
    data = request.get_json()
    
    if not data or 'items' not in data:
        return jsonify({'error': 'Cart items required'}), 400
    
    items = data['items']
    if not isinstance(items, list):
        return jsonify({'error': 'Items must be a list'}), 400
    
    try:
        # Clear existing cart
        CartItem.query.filter_by(user_id=user.id).delete()
        
        # Add new items
        added_items = []
        errors = []
        
        for item in items:
            product_id = item.get('product_id')
            size = item.get('size')
            quantity = item.get('quantity', 1)
            
            if not product_id or not size:
                errors.append(f"Missing product_id or size for item")
                continue
            
            # Validate
            is_valid, qty = validate_quantity(quantity, max_quantity=10)
            if not is_valid:
                errors.append(f"Invalid quantity for product {product_id}")
                continue
            
            is_valid, size = validate_size(size)
            if not is_valid:
                errors.append(f"Invalid size for product {product_id}")
                continue
            
            # Check product
            product = Product.query.get(product_id)
            if not product or not product.is_active:
                errors.append(f"Product {product_id} not found or inactive")
                continue
            
            # Check stock
            stock = product.get_stock()
            if stock.get(size, 0) < qty:
                errors.append(f"Not enough stock for product {product_id} size {size}")
                continue
            
            cart_item = CartItem(
                user_id=user.id,
                product_id=product_id,
                quantity=qty,
                size=size
            )
            db.session.add(cart_item)
            added_items.append(cart_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cart synced successfully',
            'items': [item.to_dict() for item in added_items],
            'errors': errors if errors else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Cart sync error: {str(e)}")
        return jsonify({'error': 'Failed to sync cart'}), 500


@cart_bp.route('/validate', methods=['POST'])
@require_auth
def validate_cart():
    """
    Validate cart items (check stock availability)
    
    Returns:
        - Validation results with any issues
    """
    user = request.current_user
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    
    issues = []
    valid_items = []
    
    for item in cart_items:
        product = item.product
        
        if not product or not product.is_active:
            issues.append({
                'item_id': item.id,
                'product_id': item.product_id,
                'issue': 'Product no longer available',
                'action': 'remove'
            })
            continue
        
        stock = product.get_stock()
        available = stock.get(item.size, 0)
        
        if available < item.quantity:
            if available == 0:
                issues.append({
                    'item_id': item.id,
                    'product_id': item.product_id,
                    'product_name': product.name,
                    'size': item.size,
                    'issue': 'Out of stock',
                    'action': 'remove'
                })
            else:
                issues.append({
                    'item_id': item.id,
                    'product_id': item.product_id,
                    'product_name': product.name,
                    'size': item.size,
                    'issue': f'Only {available} available (you have {item.quantity})',
                    'action': 'update',
                    'suggested_quantity': available
                })
        else:
            valid_items.append(item.to_dict())
    
    return jsonify({
        'success': len(issues) == 0,
        'valid': len(issues) == 0,
        'valid_items': valid_items,
        'issues': issues
    }), 200
