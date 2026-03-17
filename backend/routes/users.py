"""
Users Routes - User management and profile
"""
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import desc
from models.database import db
from models.user import User
from models.order import Order
from utils.jwt_utils import require_auth, require_admin
from utils.validation import validate_phone, sanitize_string

users_bp = Blueprint('users', __name__)


@users_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """
    Get current user profile with stats
    
    Returns:
        - User profile and order stats
    """
    user = request.current_user
    
    # Get order stats
    total_orders = Order.query.filter_by(user_id=user.id).count()
    total_spent = db.session.query(db.func.sum(Order.total)).filter(
        Order.user_id == user.id,
        Order.payment_status == 'paid'
    ).scalar() or 0
    
    profile = user.to_dict()
    profile['stats'] = {
        'total_orders': total_orders,
        'total_spent': float(total_spent)
    }
    
    return jsonify({
        'success': True,
        'profile': profile
    }), 200


@users_bp.route('/address', methods=['PUT'])
@require_auth
def update_address():
    """
    Update delivery address
    
    Request Body:
        - street: Street address
        - city: City
        - state: State
        - phone: Contact phone
        - landmark: (optional) Landmark
    
    Returns:
        - Updated address
    """
    user = request.current_user
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Build address object
    address = {}
    
    if 'street' in data:
        address['street'] = sanitize_string(data['street'], max_length=500)
    if 'city' in data:
        address['city'] = sanitize_string(data['city'], max_length=100)
    if 'state' in data:
        address['state'] = sanitize_string(data['state'], max_length=100)
    if 'landmark' in data:
        address['landmark'] = sanitize_string(data['landmark'], max_length=200)
    if 'phone' in data:
        is_valid, phone = validate_phone(data['phone'])
        if not is_valid:
            return jsonify({'error': phone}), 400
        address['phone'] = phone
    
    # Validate required fields
    required = ['street', 'city', 'state']
    missing = [f for f in required if f not in address or not address[f]]
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400
    
    # Currently only Lagos deliveries
    if address.get('state', '').lower() != 'lagos':
        return jsonify({'error': 'We currently only deliver to Lagos State'}), 400
    
    try:
        user.set_address(address)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'address': user.get_address()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Address update error: {str(e)}")
        return jsonify({'error': 'Failed to update address'}), 500


@users_bp.route('/phone', methods=['PUT'])
@require_auth
def update_phone():
    """
    Update phone number
    
    Request Body:
        - phone: Phone number
    
    Returns:
        - Updated phone
    """
    user = request.current_user
    data = request.get_json()
    
    if not data or 'phone' not in data:
        return jsonify({'error': 'Phone number is required'}), 400
    
    is_valid, phone = validate_phone(data['phone'])
    if not is_valid:
        return jsonify({'error': phone}), 400
    
    try:
        user.phone = phone
        db.session.commit()
        
        return jsonify({
            'success': True,
            'phone': phone
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Phone update error: {str(e)}")
        return jsonify({'error': 'Failed to update phone'}), 500


# Admin Routes

@users_bp.route('/admin/all', methods=['GET'])
@require_admin
def get_all_users():
    """
    Get all users (Admin only)
    
    Query Parameters:
        - role: Filter by role
        - search: Search by name or email
        - page: Page number
        - per_page: Items per page
    
    Returns:
        - List of users
    """
    role = request.args.get('role')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = User.query
    
    if role:
        query = query.filter_by(role=role)
    
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            db.or_(
                User.name.ilike(search_term),
                User.email.ilike(search_term)
            )
        )
    
    query = query.order_by(desc(User.created_at))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'users': [user.to_dict() for user in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'total_pages': pagination.pages
        }
    }), 200


@users_bp.route('/admin/<int:user_id>', methods=['GET'])
@require_admin
def get_user_details(user_id):
    """
    Get user details with orders (Admin only)
    
    Args:
        user_id: User ID
    
    Returns:
        - User details with order history
    """
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'success': True,
        'user': user.to_dict(include_orders=True)
    }), 200


@users_bp.route('/admin/<int:user_id>/role', methods=['PUT'])
@require_admin
def update_user_role(user_id):
    """
    Update user role (Admin only)
    
    Args:
        user_id: User ID
    
    Request Body:
        - role: 'customer' or 'admin'
    
    Returns:
        - Updated user
    """
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if not data or 'role' not in data:
        return jsonify({'error': 'Role is required'}), 400
    
    role = data['role']
    if role not in ['customer', 'admin']:
        return jsonify({'error': 'Invalid role. Must be customer or admin'}), 400
    
    try:
        user.role = role
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Role update error: {str(e)}")
        return jsonify({'error': 'Failed to update role'}), 500


@users_bp.route('/admin/<int:user_id>/status', methods=['PUT'])
@require_admin
def update_user_status(user_id):
    """
    Activate/deactivate user (Admin only)
    
    Args:
        user_id: User ID
    
    Request Body:
        - is_active: Boolean
    
    Returns:
        - Updated user
    """
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if not data or 'is_active' not in data:
        return jsonify({'error': 'is_active is required'}), 400
    
    try:
        user.is_active = bool(data['is_active'])
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Status update error: {str(e)}")
        return jsonify({'error': 'Failed to update status'}), 500


@users_bp.route('/admin/export', methods=['GET'])
@require_admin
def export_users():
    """
    Export users to CSV (Admin only)
    
    Query Parameters:
        - role: Filter by role
    
    Returns:
        - CSV file download
    """
    import csv
    import io
    from flask import Response
    
    role = request.args.get('role')
    
    query = User.query
    if role:
        query = query.filter_by(role=role)
    
    users = query.all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Role', 'Created At', 'Last Login'])
    
    # Data
    for user in users:
        writer.writerow([
            user.id,
            user.name,
            user.email,
            user.phone or '',
            user.role,
            user.created_at.isoformat() if user.created_at else '',
            user.last_login.isoformat() if user.last_login else ''
        ])
    
    output.seek(0)
    
    return Response(
        output,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=users.csv'
        }
    ), 200
