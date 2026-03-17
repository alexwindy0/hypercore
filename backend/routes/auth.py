"""
Authentication Routes - Google OAuth and JWT
"""
import os
import requests
from flask import Blueprint, request, jsonify, current_app
from models.database import db
from models.user import User
from utils.jwt_utils import generate_token, set_auth_cookie, clear_auth_cookie, require_auth
from utils.validation import validate_email, validate_phone
from utils.helpers import generate_welcome_coupon
from services.email_service import email_service

auth_bp = Blueprint('auth', __name__)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'


@auth_bp.route('/google', methods=['POST'])
def google_auth():
    """
    Handle Google OAuth authentication
    
    Request Body:
        - access_token: Google OAuth access token
        - admin_key: (optional) Admin registration key
    
    Returns:
        - JWT token and user data
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    access_token = data.get('access_token')
    admin_key = data.get('admin_key')
    
    if not access_token:
        return jsonify({'error': 'Access token is required'}), 400
    
    # Verify token with Google
    try:
        # Get user info from Google
        headers = {'Authorization': f'Bearer {access_token}'}
        google_response = requests.get(GOOGLE_USERINFO_URL, headers=headers, timeout=10)
        
        if not google_response.ok:
            return jsonify({'error': 'Invalid Google token'}), 401
        
        google_user = google_response.json()
        
        email = google_user.get('email')
        name = google_user.get('name')
        google_id = google_user.get('id')
        picture = google_user.get('picture')
        email_verified = google_user.get('verified_email', False)
        
        if not email:
            return jsonify({'error': 'Email not provided by Google'}), 400
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        is_new_user = False
        
        if user:
            # Update existing user
            user.google_id = google_id
            user.name = name or user.name
            user.email_verified = email_verified
            user.last_login = db.func.now()
        else:
            # Create new user
            is_new_user = True
            
            # Check if admin registration
            role = 'customer'
            if admin_key:
                expected_key = current_app.config.get('ADMIN_REGISTRATION_KEY')
                if admin_key == expected_key:
                    role = 'admin'
                else:
                    return jsonify({'error': 'Invalid admin registration key'}), 403
            
            user = User(
                email=email,
                name=name or email.split('@')[0],
                google_id=google_id,
                role=role,
                email_verified=email_verified
            )
            db.session.add(user)
        
        db.session.commit()
        
        # Generate JWT token
        token = generate_token(user.id, user.role)
        
        # Send welcome email for new users
        if is_new_user and role == 'customer':
            coupon = generate_welcome_coupon()
            email_service.send_welcome_email(email, user.name, coupon)
        
        # Prepare response
        response_data = {
            'success': True,
            'is_new_user': is_new_user,
            'user': user.to_dict(),
            'token': token
        }
        
        response = jsonify(response_data)
        
        # Set httpOnly cookie
        set_auth_cookie(response, token)
        
        return response, 200
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Google auth error: {str(e)}")
        return jsonify({'error': 'Failed to verify with Google'}), 500
    except Exception as e:
        current_app.logger.error(f"Auth error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Authentication failed'}), 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    Logout user and clear session
    
    Returns:
        - Success message
    """
    response = jsonify({'success': True, 'message': 'Logged out successfully'})
    clear_auth_cookie(response)
    return response, 200


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user_info():
    """
    Get current authenticated user info
    
    Returns:
        - User data
    """
    user = request.current_user
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """
    Update user profile
    
    Request Body:
        - name: User name
        - phone: Phone number
        - address: Delivery address object
    
    Returns:
        - Updated user data
    """
    user = request.current_user
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update name
    if 'name' in data:
        user.name = data['name'].strip()
    
    # Update and validate phone
    if 'phone' in data:
        is_valid, result = validate_phone(data['phone'])
        if not is_valid:
            return jsonify({'error': result}), 400
        user.phone = result
    
    # Update address
    if 'address' in data:
        user.set_address(data['address'])
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@require_auth
def refresh_token():
    """
    Refresh JWT token
    
    Returns:
        - New JWT token
    """
    user = request.current_user
    new_token = generate_token(user.id, user.role)
    
    response = jsonify({
        'success': True,
        'token': new_token
    })
    
    set_auth_cookie(response, new_token)
    return response, 200


@auth_bp.route('/admin/register', methods=['POST'])
def admin_register():
    """
    Register a new admin user (requires admin key)
    
    Request Body:
        - access_token: Google OAuth access token
        - admin_key: Admin registration key
    
    Returns:
        - JWT token and user data
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    admin_key = data.get('admin_key')
    expected_key = current_app.config.get('ADMIN_REGISTRATION_KEY')
    
    if not admin_key or admin_key != expected_key:
        return jsonify({'error': 'Invalid admin registration key'}), 403
    
    # Proceed with normal Google auth but force admin role
    return google_auth()
