"""
Order Model - Customer Orders and Order Items
"""
from datetime import datetime
from models.database import db
import json

class Order(db.Model):
    __tablename__ = 'orders'
    
    # Order Status Constants
    STATUS_PROCESSING = 'processing'
    STATUS_PAID = 'paid'
    STATUS_SHIPPED = 'shipped'
    STATUS_OUT_FOR_DELIVERY = 'out_for_delivery'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_REFUNDED = 'refunded'
    
    VALID_STATUSES = [
        STATUS_PROCESSING, STATUS_PAID, STATUS_SHIPPED, 
        STATUS_OUT_FOR_DELIVERY, STATUS_DELIVERED, 
        STATUS_CANCELLED, STATUS_REFUNDED
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Order Number (human-readable)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # User who placed the order
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Order Items (stored as JSON for quick access, detailed in OrderItem table)
    items = db.Column(db.Text, nullable=False)
    
    # Financial Details
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Delivery Details
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_zone = db.Column(db.String(50), nullable=False)
    estimated_delivery_date = db.Column(db.Date, nullable=True)
    
    # Payment Details
    payment_status = db.Column(db.String(20), default='pending')
    paystack_ref = db.Column(db.String(100), nullable=True)
    paystack_transaction_id = db.Column(db.String(100), nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    
    # Order Status
    status = db.Column(db.String(30), default=STATUS_PROCESSING, nullable=False)
    
    # Tracking
    tracking_number = db.Column(db.String(100), nullable=True)
    shipped_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Notes
    customer_notes = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, user_id, items, subtotal, delivery_fee, total, delivery_address, delivery_zone, order_number):
        self.user_id = user_id
        self.items = json.dumps(items)
        self.subtotal = subtotal
        self.delivery_fee = delivery_fee
        self.total = total
        self.delivery_address = json.dumps(delivery_address)
        self.delivery_zone = delivery_zone
        self.order_number = order_number
        self.status = self.STATUS_PROCESSING
    
    def get_items(self):
        """Get items as list"""
        return json.loads(self.items) if self.items else []
    
    def get_delivery_address(self):
        """Get delivery address as dictionary"""
        return json.loads(self.delivery_address) if self.delivery_address else {}
    
    def set_delivery_address(self, address_dict):
        """Set delivery address from dictionary"""
        self.delivery_address = json.dumps(address_dict)
    
    def update_status(self, new_status, tracking_number=None):
        """Update order status with validation"""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")
        
        self.status = new_status
        
        if new_status == self.STATUS_SHIPPED and tracking_number:
            self.tracking_number = tracking_number
            self.shipped_at = datetime.utcnow()
        
        if new_status == self.STATUS_DELIVERED:
            self.delivered_at = datetime.utcnow()
        
        self.updated_at = datetime.utcnow()
    
    def mark_as_paid(self, paystack_ref, paystack_transaction_id):
        """Mark order as paid"""
        self.payment_status = 'paid'
        self.paystack_ref = paystack_ref
        self.paystack_transaction_id = paystack_transaction_id
        self.paid_at = datetime.utcnow()
        self.status = self.STATUS_PAID
        self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_items=True):
        """Convert order to dictionary"""
        data = {
            'id': self.id,
            'order_number': self.order_number,
            'user_id': self.user_id,
            'subtotal': float(self.subtotal),
            'delivery_fee': float(self.delivery_fee),
            'total': float(self.total),
            'delivery_address': self.get_delivery_address(),
            'delivery_zone': self.delivery_zone,
            'estimated_delivery_date': self.estimated_delivery_date.isoformat() if self.estimated_delivery_date else None,
            'payment_status': self.payment_status,
            'paystack_ref': self.paystack_ref,
            'status': self.status,
            'tracking_number': self.tracking_number,
            'customer_notes': self.customer_notes,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'shipped_at': self.shipped_at.isoformat() if self.shipped_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None
        }
        
        if include_items:
            data['items'] = self.get_items()
            data['order_items'] = [item.to_dict() for item in self.order_items]
        
        return data
    
    def __repr__(self):
        return f'<Order {self.order_number} - {self.status} - ₦{self.total}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Order reference
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    # Product reference
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Item Details
    quantity = db.Column(db.Integer, nullable=False, default=1)
    size = db.Column(db.String(10), nullable=False)
    price_at_time = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Product snapshot (in case product changes later)
    product_name = db.Column(db.String(255), nullable=False)
    product_image = db.Column(db.String(500), nullable=True)
    
    def __init__(self, order_id, product_id, quantity, size, price_at_time, product_name, product_image=None):
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity
        self.size = size
        self.price_at_time = price_at_time
        self.product_name = product_name
        self.product_image = product_image
    
    def get_subtotal(self):
        """Calculate subtotal for this item"""
        return float(self.price_at_time) * self.quantity
    
    def to_dict(self):
        """Convert order item to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_image': self.product_image,
            'quantity': self.quantity,
            'size': self.size,
            'price_at_time': float(self.price_at_time),
            'subtotal': self.get_subtotal()
        }
    
    def __repr__(self):
        return f'<OrderItem {self.product_name} - {self.size} x{self.quantity}>'
