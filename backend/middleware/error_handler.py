"""
Error Handler Middleware - Centralized error handling
"""
import traceback
from functools import wraps
from flask import jsonify, current_app

class APIError(Exception):
    """Custom API Error class"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv


def handle_errors(f):
    """
    Decorator to handle errors in route functions
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            response = jsonify(e.to_dict())
            response.status_code = e.status_code
            return response
        except Exception as e:
            # Log the error
            current_app.logger.error(f"Unhandled error: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            
            # Return generic error in production
            is_dev = current_app.config.get('FLASK_ENV') == 'development'
            error_msg = str(e) if is_dev else 'Internal server error'
            
            response = jsonify({'error': error_msg})
            response.status_code = 500
            return response
    
    return decorated_function


def register_error_handlers(app):
    """
    Register global error handlers with Flask app
    """
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': 'Method not allowed'}), 405
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({'error': 'Unprocessable entity'}), 422
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({'error': 'Rate limit exceeded', 'retry_after': error.description}), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({'error': 'Internal server error'}), 500
