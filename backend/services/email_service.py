"""
Email Service - Handle transactional emails using Resend
"""
import os
import resend
from flask import current_app

class EmailService:
    """Service for sending transactional emails"""
    
    def __init__(self):
        self.api_key = os.getenv('RESEND_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'Hypercore <noreply@hypercore.com.ng>')
        self.from_name = 'Hypercore'
        
        # Initialize Resend
        if self.api_key:
            resend.api_key = self.api_key
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)
        
        Returns:
            dict: Send result
        """
        if not self.api_key:
            current_app.logger.warning("Resend API key not configured")
            return {'success': False, 'error': 'Email service not configured'}
        
        try:
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                params["text"] = text_content
            
            result = resend.Emails.send(params)
            
            return {
                'success': True,
                'id': result.get('id'),
                'message': 'Email sent successfully'
            }
        except Exception as e:
            current_app.logger.error(f"Email send error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def send_welcome_email(self, to_email, name, coupon_code=None):
        """
        Send welcome email to new user
        
        Args:
            to_email: User email
            name: User name
            coupon_code: Welcome discount code
        
        Returns:
            dict: Send result
        """
        subject = "Welcome to Hypercore - Your Fitness Journey Starts Here!"
        
        coupon_section = f"""
        <div style="background: #0066ff; color: white; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <h3 style="margin: 0 0 10px 0;">Your Welcome Gift</h3>
            <p style="margin: 0;">Use code <strong style="font-size: 24px; letter-spacing: 2px;">{coupon_code}</strong> for 10% off your first order!</p>
            <p style="margin: 10px 0 0 0; font-size: 12px;">Valid for 30 days</p>
        </div>
        """ if coupon_code else ""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Hypercore</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1a1a1a; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; padding: 20px 0; border-bottom: 3px solid #0066ff;">
                <h1 style="color: #1a1a1a; margin: 0; font-size: 28px; letter-spacing: 2px;">HYPERCORE</h1>
                <p style="color: #666; margin: 5px 0 0 0;">Premium Gym Sportswear</p>
            </div>
            
            <div style="padding: 30px 0;">
                <h2 style="color: #1a1a1a;">Welcome, {name}!</h2>
                <p>Thank you for joining Hypercore. We're excited to be part of your fitness journey.</p>
                
                <p>At Hypercore, we believe that the right gear can make all the difference. Our premium sportswear is designed to help you perform at your best, whether you're hitting the gym or pushing your limits outdoors.</p>
                
                {coupon_section}
                
                <div style="margin: 30px 0;">
                    <h3>What's Next?</h3>
                    <ul style="padding-left: 20px;">
                        <li>Browse our latest collections for Men and Women</li>
                        <li>Find your perfect fit with our size guide</li>
                        <li>Enjoy fast delivery across Lagos</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://hypercore.com.ng/shop" style="background: #0066ff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Start Shopping</a>
                </div>
            </div>
            
            <div style="border-top: 1px solid #eee; padding: 20px 0; text-align: center; color: #666; font-size: 12px;">
                <p>Hypercore | Lagos, Nigeria</p>
                <p>Follow us: @hypercore.ng</p>
                <p>If you have any questions, reply to this email or contact us at support@hypercore.com.ng</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_order_confirmation(self, to_email, name, order):
        """
        Send order confirmation email
        
        Args:
            to_email: Customer email
            name: Customer name
            order: Order object
        
        Returns:
            dict: Send result
        """
        subject = f"Order Confirmation - {order.order_number}"
        
        items_html = ""
        for item in order.get_items():
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{item.get('name', 'Product')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">{item.get('size', 'N/A')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">{item.get('quantity', 1)}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">₦{item.get('price', 0):,.2f}</td>
            </tr>
            """
        
        address = order.get_delivery_address()
        address_html = f"""
        <p>{address.get('street', '')}</p>
        <p>{address.get('city', '')}, {address.get('state', '')}</p>
        <p>{address.get('phone', '')}</p>
        """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Order Confirmation</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1a1a1a; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; padding: 20px 0; border-bottom: 3px solid #0066ff;">
                <h1 style="color: #1a1a1a; margin: 0; font-size: 28px; letter-spacing: 2px;">HYPERCORE</h1>
            </div>
            
            <div style="padding: 30px 0;">
                <h2 style="color: #0066ff;">Order Confirmed!</h2>
                <p>Hi {name},</p>
                <p>Thank you for your order. We've received it and are processing it now.</p>
                
                <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Order Number:</strong> {order.order_number}</p>
                    <p style="margin: 5px 0;"><strong>Order Date:</strong> {order.created_at.strftime('%B %d, %Y')}</p>
                    <p style="margin: 5px 0;"><strong>Payment Status:</strong> {order.payment_status.title()}</p>
                </div>
                
                <h3>Order Details</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f5f5f5;">
                            <th style="padding: 10px; text-align: left;">Product</th>
                            <th style="padding: 10px; text-align: center;">Size</th>
                            <th style="padding: 10px; text-align: center;">Qty</th>
                            <th style="padding: 10px; text-align: right;">Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="3" style="padding: 10px; text-align: right;"><strong>Subtotal:</strong></td>
                            <td style="padding: 10px; text-align: right;">₦{float(order.subtotal):,.2f}</td>
                        </tr>
                        <tr>
                            <td colspan="3" style="padding: 10px; text-align: right;"><strong>Delivery:</strong></td>
                            <td style="padding: 10px; text-align: right;">₦{float(order.delivery_fee):,.2f}</td>
                        </tr>
                        <tr style="font-size: 18px;">
                            <td colspan="3" style="padding: 10px; text-align: right;"><strong>Total:</strong></td>
                            <td style="padding: 10px; text-align: right; color: #0066ff;"><strong>₦{float(order.total):,.2f}</strong></td>
                        </tr>
                    </tfoot>
                </table>
                
                <div style="margin: 30px 0;">
                    <h3>Delivery Address</h3>
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px;">
                        {address_html}
                    </div>
                </div>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://hypercore.com.ng/orders" style="background: #0066ff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Track Your Order</a>
                </p>
            </div>
            
            <div style="border-top: 1px solid #eee; padding: 20px 0; text-align: center; color: #666; font-size: 12px;">
                <p>Hypercore | Lagos, Nigeria</p>
                <p>Questions? Contact support@hypercore.com.ng</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_order_shipped(self, to_email, name, order):
        """
        Send order shipped notification
        
        Args:
            to_email: Customer email
            name: Customer name
            order: Order object
        
        Returns:
            dict: Send result
        """
        subject = f"Your Order is on the Way! - {order.order_number}"
        
        tracking_info = f"""
        <div style="background: #0066ff; color: white; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <h3 style="margin: 0 0 10px 0;">Tracking Number</h3>
            <p style="margin: 0; font-size: 20px; font-weight: bold;">{order.tracking_number}</p>
        </div>
        """ if order.tracking_number else ""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Order Shipped</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1a1a1a; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; padding: 20px 0; border-bottom: 3px solid #0066ff;">
                <h1 style="color: #1a1a1a; margin: 0; font-size: 28px; letter-spacing: 2px;">HYPERCORE</h1>
            </div>
            
            <div style="padding: 30px 0; text-align: center;">
                <h2 style="color: #0066ff;">Your Order is on the Way!</h2>
                <p>Hi {name},</p>
                <p>Great news! Your order <strong>{order.order_number}</strong> has been shipped and is on its way to you.</p>
                
                {tracking_info}
                
                <p>Estimated delivery: <strong>{order.estimated_delivery_date.strftime('%B %d, %Y') if order.estimated_delivery_date else '3-5 business days'}</strong></p>
                
                <p style="margin: 30px 0;">
                    <a href="https://hypercore.com.ng/orders/{order.id}" style="background: #0066ff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Track Order</a>
                </p>
            </div>
            
            <div style="border-top: 1px solid #eee; padding: 20px 0; text-align: center; color: #666; font-size: 12px;">
                <p>Hypercore | Lagos, Nigeria</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_order_delivered(self, to_email, name, order):
        """
        Send order delivered notification
        
        Args:
            to_email: Customer email
            name: Customer name
            order: Order object
        
        Returns:
            dict: Send result
        """
        subject = f"Order Delivered - {order.order_number}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Order Delivered</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1a1a1a; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; padding: 20px 0; border-bottom: 3px solid #0066ff;">
                <h1 style="color: #1a1a1a; margin: 0; font-size: 28px; letter-spacing: 2px;">HYPERCORE</h1>
            </div>
            
            <div style="padding: 30px 0; text-align: center;">
                <h2 style="color: #28a745;">Order Delivered!</h2>
                <p>Hi {name},</p>
                <p>Your order <strong>{order.order_number}</strong> has been delivered.</p>
                <p>We hope you love your new Hypercore gear!</p>
                
                <div style="margin: 30px 0;">
                    <a href="https://hypercore.com.ng/shop" style="background: #0066ff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 5px;">Shop More</a>
                    <a href="https://hypercore.com.ng/review/{order.id}" style="background: #1a1a1a; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 5px;">Leave a Review</a>
                </div>
            </div>
            
            <div style="border-top: 1px solid #eee; padding: 20px 0; text-align: center; color: #666; font-size: 12px;">
                <p>Hypercore | Lagos, Nigeria</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_payment_received(self, to_email, name, order):
        """
        Send payment received confirmation
        
        Args:
            to_email: Customer email
            name: Customer name
            order: Order object
        
        Returns:
            dict: Send result
        """
        subject = f"Payment Received - {order.order_number}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Payment Received</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1a1a1a; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; padding: 20px 0; border-bottom: 3px solid #0066ff;">
                <h1 style="color: #1a1a1a; margin: 0; font-size: 28px; letter-spacing: 2px;">HYPERCORE</h1>
            </div>
            
            <div style="padding: 30px 0; text-align: center;">
                <h2 style="color: #28a745;">Payment Received!</h2>
                <p>Hi {name},</p>
                <p>We've received your payment of <strong>₦{float(order.total):,.2f}</strong> for order <strong>{order.order_number}</strong>.</p>
                <p>Your order is now being processed and will be shipped soon.</p>
                
                <p style="margin: 30px 0;">
                    <a href="https://hypercore.com.ng/orders/{order.id}" style="background: #0066ff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">View Order</a>
                </p>
            </div>
            
            <div style="border-top: 1px solid #eee; padding: 20px 0; text-align: center; color: #666; font-size: 12px;">
                <p>Hypercore | Lagos, Nigeria</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)

# Singleton instance
email_service = EmailService()
