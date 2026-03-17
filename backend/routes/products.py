"""
Product Routes - Product catalog and management
"""
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import desc, asc
from models.database import db
from models.product import Product
from utils.jwt_utils import optional_auth, require_admin
from utils.validation import validate_price, validate_gender, sanitize_string
from utils.helpers import paginate_results

products_bp = Blueprint('products', __name__)


@products_bp.route('/', methods=['GET'])
@optional_auth
def get_products():
    """
    Get products list with filtering and pagination
    
    Query Parameters:
        - gender: Filter by 'men' or 'women'
        - category: Filter by category
        - min_price: Minimum price
        - max_price: Maximum price
        - size: Filter by available size
        - search: Search by name
        - sort: Sort by 'newest', 'price_asc', 'price_desc', 'name'
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
        - featured: Filter featured products only
    
    Returns:
        - Paginated list of products
    """
    # Get query parameters
    gender = request.args.get('gender')
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    size = request.args.get('size')
    search = request.args.get('search')
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    featured = request.args.get('featured', type=lambda x: x.lower() == 'true')
    
    # Build query
    query = Product.query.filter_by(is_active=True)
    
    # Apply filters
    if gender:
        query = query.filter_by(gender=gender.lower())
    
    if category:
        query = query.filter_by(category=category.lower())
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    if featured is not None:
        query = query.filter_by(is_featured=featured)
    
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(Product.name.ilike(search_term))
    
    # Size filter (requires checking JSON stock field)
    if size:
        # This is a simplified check - in production, you might want a more sophisticated approach
        query = query.filter(Product.sizes.contains(size.upper()))
    
    # Apply sorting
    if sort == 'newest':
        query = query.order_by(desc(Product.created_at))
    elif sort == 'price_asc':
        query = query.order_by(asc(Product.price))
    elif sort == 'price_desc':
        query = query.order_by(desc(Product.price))
    elif sort == 'name':
        query = query.order_by(asc(Product.name))
    else:
        query = query.order_by(desc(Product.created_at))
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    products = [p.to_dict() for p in pagination.items]
    
    return jsonify({
        'success': True,
        'products': products,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'total_pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@products_bp.route('/<int:product_id>', methods=['GET'])
@optional_auth
def get_product(product_id):
    """
    Get single product details
    
    Args:
        product_id: Product ID
    
    Returns:
        - Product details
    """
    product = Product.query.get_or_404(product_id)
    
    # Get related products (same gender, different product)
    related = Product.query.filter(
        Product.gender == product.gender,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    
    return jsonify({
        'success': True,
        'product': product.to_dict(),
        'related_products': [p.to_dict(include_description=False) for p in related]
    }), 200


@products_bp.route('/featured', methods=['GET'])
def get_featured_products():
    """
    Get featured products
    
    Returns:
        - List of featured products
    """
    products = Product.query.filter_by(
        is_featured=True,
        is_active=True
    ).limit(8).all()
    
    return jsonify({
        'success': True,
        'products': [p.to_dict(include_description=False) for p in products]
    }), 200


@products_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    Get product categories
    
    Returns:
        - List of categories with counts
    """
    # Get distinct categories with counts
    from sqlalchemy import func
    
    categories = db.session.query(
        Product.category,
        func.count(Product.id).label('count')
    ).filter(
        Product.is_active == True
    ).group_by(Product.category).all()
    
    return jsonify({
        'success': True,
        'categories': [
            {'name': cat, 'count': count} for cat, count in categories if cat
        ]
    }), 200


# Admin Routes

@products_bp.route('/', methods=['POST'])
@require_admin
def create_product():
    """
    Create new product (Admin only)
    
    Request Body:
        - name: Product name
        - description: Product description
        - price: Product price
        - sizes: List of available sizes
        - stock: Stock count per size (dict)
        - gender: 'men' or 'women'
        - category: Product category
        - images: List of image URLs
        - is_featured: Boolean
    
    Returns:
        - Created product
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    required = ['name', 'price', 'gender']
    missing = [f for f in required if f not in data or not data[f]]
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400
    
    # Validate price
    is_valid, price = validate_price(data['price'])
    if not is_valid:
        return jsonify({'error': price}), 400
    
    # Validate gender
    is_valid, gender = validate_gender(data['gender'])
    if not is_valid:
        return jsonify({'error': gender}), 400
    
    try:
        product = Product(
            name=sanitize_string(data['name'], max_length=255),
            description=sanitize_string(data.get('description', ''), max_length=2000, allow_newlines=True),
            price=price,
            sizes=data.get('sizes', ["S", "M", "L", "XL", "XXL"]),
            stock=data.get('stock', {"S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}),
            gender=gender,
            category=sanitize_string(data.get('category'), max_length=50),
            images=data.get('images', []),
            is_featured=data.get('is_featured', False)
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Product creation error: {str(e)}")
        return jsonify({'error': 'Failed to create product'}), 500


@products_bp.route('/<int:product_id>', methods=['PUT'])
@require_admin
def update_product(product_id):
    """
    Update product (Admin only)
    
    Args:
        product_id: Product ID
    
    Request Body:
        - Same as create, all fields optional
    
    Returns:
        - Updated product
    """
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update fields
    if 'name' in data:
        product.name = sanitize_string(data['name'], max_length=255)
    
    if 'description' in data:
        product.description = sanitize_string(data['description'], max_length=2000, allow_newlines=True)
    
    if 'price' in data:
        is_valid, price = validate_price(data['price'])
        if not is_valid:
            return jsonify({'error': price}), 400
        product.price = price
    
    if 'sizes' in data:
        product.sizes = str(data['sizes'])
    
    if 'stock' in data:
        product.set_stock(data['stock'])
    
    if 'gender' in data:
        is_valid, gender = validate_gender(data['gender'])
        if not is_valid:
            return jsonify({'error': gender}), 400
        product.gender = gender
    
    if 'category' in data:
        product.category = sanitize_string(data['category'], max_length=50)
    
    if 'images' in data:
        product.set_images(data['images'])
    
    if 'is_featured' in data:
        product.is_featured = bool(data['is_featured'])
    
    if 'is_active' in data:
        product.is_active = bool(data['is_active'])
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'product': product.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Product update error: {str(e)}")
        return jsonify({'error': 'Failed to update product'}), 500


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@require_admin
def delete_product(product_id):
    """
    Delete product (Admin only) - Soft delete
    
    Args:
        product_id: Product ID
    
    Returns:
        - Success message
    """
    product = Product.query.get_or_404(product_id)
    
    try:
        # Soft delete
        product.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Product delete error: {str(e)}")
        return jsonify({'error': 'Failed to delete product'}), 500


@products_bp.route('/<int:product_id>/stock', methods=['PUT'])
@require_admin
def update_stock(product_id):
    """
    Update product stock (Admin only)
    
    Args:
        product_id: Product ID
    
    Request Body:
        - stock: Dict of size -> quantity
    
    Returns:
        - Updated product
    """
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if not data or 'stock' not in data:
        return jsonify({'error': 'Stock data required'}), 400
    
    try:
        product.set_stock(data['stock'])
        db.session.commit()
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Stock update error: {str(e)}")
        return jsonify({'error': 'Failed to update stock'}), 500
