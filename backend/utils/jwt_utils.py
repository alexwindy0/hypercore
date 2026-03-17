"""
JWT Token Utilities - Authentication and Authorization
"""
import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from models.database import db
from models.user import User

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 7


def generate_token(user_id, role='customer'):
    """
    Generate JWT token for user
    
    Args:
        user_id: User ID
        role: User role (customer/admin)
    
    Returns:
        JWT token string
    """
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token):
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        tuple: (is_valid, payload_or_error)
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, 'Token has expired'
    except jwt.InvalidTokenError:
        return False, 'Invalid token'


def get_token_from_request():
    """
    Extract token from request headers or cookies
    
    Returns:
        Token string or None
    """
    # Check Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
    
    # Check cookies (httpOnly)
    return request.cookies.get('access_token')


def get_current_user():
    """
    Get current authenticated user from request
    
    Returns:
        User object or None
    """
    token = get_token_from_request()
    if not token:
        return None
    
    is_valid, payload = verify_token(token)
    if not is_valid:
        return None
    
    user_id = payload.get('user_id')
    if not user_id:
        return None
    
    return User.query.get(user_id)


def require_auth(f):
    """
    Decorator to require authentication for a route
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        is_valid, payload = verify_token(token)
        if not is_valid:
            return jsonify({'error': payload}), 401
        
        # Get user from database
        user_id = payload.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # Add user to request context
        request.current_user = user
        request.user_role = payload.get('role', 'customer')
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """
    Decorator to require admin role for a route
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        is_valid, payload = verify_token(token)
        if not is_valid:
            return jsonify({'error': payload}), 401
        
        role = payload.get('role')
        if role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get user from database
        user_id = payload.get('user_id')
        user = User.query.get(user_id)
        
        if not user or not user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        
        request.current_user = user
        request.user_role = 'admin'
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """
    Decorator to optionally authenticate user (for public routes that can be personalized)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if token:
            is_valid, payload = verify_token(token)
            if is_valid:
                user_id = payload.get('user_id')
                user = User.query.get(user_id)
                if user and user.is_active:
                    request.current_user = user
                    request.user_role = payload.get('role', 'customer')
        
        return f(*args, **kwargs)
    
    return decorated_function


def set_auth_cookie(response, token):
    """
    Set JWT token in httpOnly cookie
    
    Args:
        response: Flask response object
        token: JWT token string
    """
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    response.set_cookie(
        'access_token',
        token,
        httponly=True,
        secure=is_production,  # HTTPS only in production
        samesite='Lax',
        max_age=60 * 60 * 24 * JWT_EXPIRATION_DAYS  # 7 days
    )
    
    return response


def clear_auth_cookie(response):
    """
    Clear authentication cookie
    
    Args:
        response: Flask response object
    """
    response.delete_cookie('access_token')
    return response
