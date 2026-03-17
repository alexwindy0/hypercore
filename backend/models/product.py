"""
Product Model - Gym Sportswear Items
"""
from datetime import datetime
from models.database import db
import json

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Sizes available (stored as JSON array)
    sizes = db.Column(db.Text, nullable=False, default='["S", "M", "L", "XL", "XXL"]')
    
    # Stock count per size (stored as JSON object)
    stock = db.Column(db.Text, nullable=False, default='{"S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}')
    
    # Gender category: 'men' or 'women'
    gender = db.Column(db.String(10), nullable=False, index=True)
    
    # Product category (e.g., 'tops', 'bottoms', 'accessories')
    category = db.Column(db.String(50), nullable=True)
    
    # Images (stored as JSON array of URLs)
    images = db.Column(db.Text, nullable=True)
    
    # Featured product flag
    is_featured = db.Column(db.Boolean, default=False)
    
    # Product status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    
    def __init__(self, name, price, gender, description=None, sizes=None, stock=None, category=None, images=None):
        self.name = name
        self.price = price
        self.gender = gender
        self.description = description
        self.sizes = json.dumps(sizes) if sizes else json.dumps(["S", "M", "L", "XL", "XXL"])
        self.stock = json.dumps(stock) if stock else json.dumps({"S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0})
        self.category = category
        self.images = json.dumps(images) if images else json.dumps([])
    
    def get_sizes(self):
        """Get sizes as list"""
        return json.loads(self.sizes) if self.sizes else []
    
    def get_stock(self):
        """Get stock as dictionary"""
        return json.loads(self.stock) if self.stock else {}
    
    def set_stock(self, stock_dict):
        """Set stock from dictionary"""
        self.stock = json.dumps(stock_dict)
    
    def get_images(self):
        """Get images as list"""
        return json.loads(self.images) if self.images else []
    
    def set_images(self, images_list):
        """Set images from list"""
        self.images = json.dumps(images_list)
    
    def get_total_stock(self):
        """Get total stock across all sizes"""
        stock_dict = self.get_stock()
        return sum(stock_dict.values())
    
    def is_in_stock(self, size=None):
        """Check if product is in stock"""
        stock_dict = self.get_stock()
        if size:
            return stock_dict.get(size, 0) > 0
        return any(qty > 0 for qty in stock_dict.values())
    
    def decrease_stock(self, size, quantity=1):
        """Decrease stock for a specific size"""
        stock_dict = self.get_stock()
        if size in stock_dict and stock_dict[size] >= quantity:
            stock_dict[size] -= quantity
            self.set_stock(stock_dict)
            return True
        return False
    
    def increase_stock(self, size, quantity=1):
        """Increase stock for a specific size"""
        stock_dict = self.get_stock()
        if size in stock_dict:
            stock_dict[size] += quantity
        else:
            stock_dict[size] = quantity
        self.set_stock(stock_dict)
    
    def to_dict(self, include_description=True):
        """Convert product to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'price': float(self.price),
            'sizes': self.get_sizes(),
            'stock': self.get_stock(),
            'total_stock': self.get_total_stock(),
            'gender': self.gender,
            'category': self.category,
            'images': self.get_images(),
            'is_featured': self.is_featured,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_description:
            data['description'] = self.description
        
        return data
    
    def __repr__(self):
        return f'<Product {self.name} - {self.gender} - ₦{self.price}>'
