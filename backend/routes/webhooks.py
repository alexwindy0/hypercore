"""
Webhooks Routes - Handle external service webhooks
"""
import os
import hmac
import hashlib
import json
from flask import Blueprint, request, jsonify, current_app
from models.database import db
from models.order import Order
from services.paystack_service import PaystackService
from services.email_service import email_service

webhooks_bp = Blueprint('webhooks', __name__)
paystack_service = PaystackService()


@webhooks_bp.route('/paystack', methods=['POST'])
def paystack_webhook():
    """
    Handle Paystack webhook events
    
    Events handled:
        - charge.success: Payment successful
        - transfer.success: Transfer successful
    """
    # Verify webhook signature
    signature = request.headers.get('x-paystack-signature')
    
    if not signature:
        return jsonify({'error': 'Missing signature'}), 400
    
    # Get raw request body
    request_body = request.get_data()
    
    # Verify signature
    secret_key = os.getenv('PAYSTACK_SECRET_KEY', '')
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        request_body,
        hashlib.sha512
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        current_app.logger.warning("Invalid Paystack webhook signature")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Parse event
    try:
        event = json.loads(request_body)
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    event_type = event.get('event')
    data = event.get('data', {})
    
    current_app.logger.info(f"Paystack webhook received: {event_type}")
    
    # Handle charge success
    if event_type == 'charge.success':
        return handle_charge_success(data)
    
    # Handle transfer success
    elif event_type == 'transfer.success':
        return handle_transfer_success(data)
    
    # Acknowledge other events
    return jsonify({'status': 'acknowledged'}), 200


def handle_charge_success(data):
    """
    Handle successful charge event
    
    Args:
        data: Event data from Paystack
    """
    reference = data.get('reference')
    
    if not reference:
        return jsonify({'error': 'Missing reference'}), 400
    
    # Find order
    order = Order.query.filter_by(order_number=reference).first()
    
    if not order:
        current_app.logger.warning(f"Order not found for reference: {reference}")
        return jsonify({'error': 'Order not found'}), 404
    
    # Check if already processed
    if order.payment_status == 'paid':
        return jsonify({'status': 'already_processed'}), 200
    
    try:
        # Mark order as paid
        order.mark_as_paid(
            paystack_ref=reference,
            paystack_transaction_id=str(data.get('id'))
        )
        db.session.commit()
        
        # Send confirmation emails
        user = order.user
        if user:
            email_service.send_payment_received(user.email, user.name, order)
            email_service.send_order_confirmation(user.email, user.name, order)
        
        current_app.logger.info(f"Order {order.order_number} marked as paid")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing charge.success: {str(e)}")
        return jsonify({'error': 'Processing failed'}), 500


def handle_transfer_success(data):
    """
    Handle successful transfer event
    
    Args:
        data: Event data from Paystack
    """
    # Implement refund/transfer logic if needed
    current_app.logger.info(f"Transfer success: {data.get('reference')}")
    return jsonify({'status': 'acknowledged'}), 200


@webhooks_bp.route('/test', methods=['POST'])
def test_webhook():
    """
    Test webhook endpoint (for development)
    """
    data = request.get_json()
    
    current_app.logger.info(f"Test webhook received: {data}")
    
    return jsonify({
        'status': 'received',
        'data': data
    }), 200
