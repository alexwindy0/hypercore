"""
Hypercore E-commerce Application
Main Flask Application Entry Point
"""

import os
from datetime import timedelta
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import extensions and configurations
from models.database import db, init_db
from utils.security import setup_security_headers

# Import route blueprints
from routes.auth import auth_bp
from routes.products import products_bp
from routes.cart import cart_bp
from routes.orders import orders_bp
from routes.users import users_bp
from routes.admin import admin_bp
from routes.webhooks import webhooks_bp

def create_app():
    """Application factory pattern"""
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/hypercore')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
    
    # Google OAuth Config
    app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
    
    # Paystack Config
    app.config['PAYSTACK_SECRET_KEY'] = os.getenv('PAYSTACK_SECRET_KEY')
    app.config['PAYSTACK_PUBLIC_KEY'] = os.getenv('PAYSTACK_PUBLIC_KEY')
    
    # Cloudinary Config
    app.config['CLOUDINARY_CLOUD_NAME'] = os.getenv('CLOUDINARY_CLOUD_NAME')
    app.config['CLOUDINARY_API_KEY'] = os.getenv('CLOUDINARY_API_KEY')
    app.config['CLOUDINARY_API_SECRET'] = os.getenv('CLOUDINARY_API_SECRET')
    
    # Resend Email Config
    app.config['RESEND_API_KEY'] = os.getenv('RESEND_API_KEY')
    app.config['FROM_EMAIL'] = os.getenv('FROM_EMAIL', 'noreply@hypercore.com.ng')
    
    # Admin Registration Key
    app.config['ADMIN_REGISTRATION_KEY'] = os.getenv('ADMIN_REGISTRATION_KEY', 'hypercore-admin-2024')
    
    # Initialize extensions
    db.init_app(app)
    
    # CORS Configuration - whitelist frontend domain
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5000')
    CORS(app, resources={
        r"/api/*": {
            "origins": [frontend_url, "http://localhost:*", "https://*.vercel.app", "https://*.render.com"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Rate Limiting - 100 requests per minute per IP
    Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["100 per minute"],
        storage_uri="memory://"
    )
    
    # Security Headers Middleware
    @app.after_request
    def after_request(response):
        return setup_security_headers(response)
    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(cart_bp, url_prefix='/api/cart')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(webhooks_bp, url_prefix='/webhooks')
    
    # Health Check Endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'hypercore-api',
            'version': '1.0.0'
        }), 200
    
    # Serve Frontend (for production)
    @app.route('/')
    def serve_frontend():
        return send_from_directory('../frontend', 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory('../frontend', path)
    
    # Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        return jsonify({'error': 'Rate limit exceeded', 'retry_after': error.description}), 429
    
    # Initialize database tables
    with app.app_context():
        init_db()
    
    return app

# Create application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
