"""
User Model - Customer and Admin accounts
"""
from datetime import datetime
from models.database import db
import json

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # Address stored as JSON for flexibility
    address = db.Column(db.Text, nullable=True)
    
    # Role: 'customer' or 'admin'
    role = db.Column(db.String(20), default='customer', nullable=False)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, email, name, google_id=None, phone=None, role='customer'):
        self.email = email
        self.name = name
        self.google_id = google_id
        self.phone = phone
        self.role = role
    
    def set_address(self, address_dict):
        """Store address as JSON string"""
        self.address = json.dumps(address_dict) if address_dict else None
    
    def get_address(self):
        """Retrieve address as dictionary"""
        return json.loads(self.address) if self.address else None
    
    def to_dict(self, include_orders=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'address': self.get_address(),
            'role': self.role,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_orders:
            data['orders'] = [order.to_dict() for order in self.orders]
        
        return data
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.email} - {self.role}>'
