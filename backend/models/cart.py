"""
Cart Item Model - Shopping Cart for Logged-in Users
"""
from datetime import datetime
from models.database import db

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User reference
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Product reference
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Cart Item Details
    quantity = db.Column(db.Integer, nullable=False, default=1)
    size = db.Column(db.String(10), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Ensure unique product+size combination per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', 'size', name='unique_cart_item'),
    )
    
    def __init__(self, user_id, product_id, quantity, size):
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.size = size
    
    def get_subtotal(self):
        """Calculate subtotal for this cart item"""
        if self.product:
            return float(self.product.price) * self.quantity
        return 0
    
    def to_dict(self, include_product=True):
        """Convert cart item to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'size': self.size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_product and self.product:
            data['product'] = self.product.to_dict(include_description=False)
            data['subtotal'] = self.get_subtotal()
        
        return data
    
    def __repr__(self):
        return f'<CartItem User:{self.user_id} Product:{self.product_id} {self.size} x{self.quantity}>'
