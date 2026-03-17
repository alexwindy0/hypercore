"""
Helper Utilities - Order numbers, currency formatting, delivery calculations
"""
import random
import string
from datetime import datetime, timedelta

# Delivery Fees (in Naira)
DELIVERY_FEES = {
    'island': 2500,
    'mainland': 2000,
    'outside': 5000
}

# Delivery Time Estimates (in business days)
DELIVERY_ESTIMATES = {
    'island': (1, 2),
    'mainland': (1, 3),
    'outside': (3, 7)
}


def generate_order_number():
    """
    Generate unique order number
    Format: HC-YYYYMMDD-XXXX (e.g., HC-20240317-A3F7)
    
    Returns:
        Order number string
    """
    date_part = datetime.utcnow().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"HC-{date_part}-{random_part}"


def format_currency(amount, currency='₦'):
    """
    Format amount as currency string
    
    Args:
        amount: Amount value
        currency: Currency symbol
    
    Returns:
        Formatted currency string
    """
    try:
        amount_float = float(amount)
        # Format with thousand separators and 2 decimal places
        return f"{currency}{amount_float:,.2f}"
    except (ValueError, TypeError):
        return f"{currency}0.00"


def format_currency_without_decimals(amount, currency='₦'):
    """
    Format amount as currency string without decimals (for display)
    
    Args:
        amount: Amount value
        currency: Currency symbol
    
    Returns:
        Formatted currency string
    """
    try:
        amount_float = float(amount)
        return f"{currency}{amount_float:,.0f}"
    except (ValueError, TypeError):
        return f"{currency}0"


def calculate_delivery_fee(zone):
    """
    Get delivery fee for zone
    
    Args:
        zone: Delivery zone (island, mainland, outside)
    
    Returns:
        Delivery fee amount
    """
    zone_lower = zone.lower() if zone else 'mainland'
    return DELIVERY_FEES.get(zone_lower, DELIVERY_FEES['mainland'])


def calculate_delivery_estimate(zone, from_date=None):
    """
    Calculate estimated delivery date range
    
    Args:
        zone: Delivery zone
        from_date: Starting date (default: today)
    
    Returns:
        Dictionary with min_date and max_date
    """
    from_date = from_date or datetime.utcnow()
    zone_lower = zone.lower() if zone else 'mainland'
    
    min_days, max_days = DELIVERY_ESTIMATES.get(zone_lower, (1, 3))
    
    min_date = from_date + timedelta(days=min_days)
    max_date = from_date + timedelta(days=max_days)
    
    return {
        'min_date': min_date.strftime('%Y-%m-%d'),
        'max_date': max_date.strftime('%Y-%m-%d'),
        'min_days': min_days,
        'max_days': max_days,
        'formatted': f"{min_date.strftime('%b %d')} - {max_date.strftime('%b %d, %Y')}"
    }


def calculate_order_totals(cart_items, delivery_zone='mainland'):
    """
    Calculate order totals from cart items
    
    Args:
        cart_items: List of cart items (with product and quantity)
        delivery_zone: Delivery zone
    
    Returns:
        Dictionary with subtotal, delivery_fee, and total
    """
    subtotal = 0
    
    for item in cart_items:
        if hasattr(item, 'product') and item.product:
            subtotal += float(item.product.price) * item.quantity
        elif isinstance(item, dict):
            # Handle dictionary format (from localStorage)
            price = item.get('price', 0)
            qty = item.get('quantity', 1)
            subtotal += float(price) * qty
    
    delivery_fee = calculate_delivery_fee(delivery_zone)
    total = subtotal + delivery_fee
    
    return {
        'subtotal': round(subtotal, 2),
        'delivery_fee': delivery_fee,
        'total': round(total, 2)
    }


def truncate_text(text, max_length=100, suffix='...'):
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if not text:
        return text
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)].rstrip() + suffix


def slugify(text):
    """
    Convert text to URL-friendly slug
    
    Args:
        text: Text to convert
    
    Returns:
        Slug string
    """
    if not text:
        return ''
    
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    
    # Remove special characters
    import re
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    
    return slug[:100]  # Limit length


def get_initials(name):
    """
    Get initials from name
    
    Args:
        name: Full name
    
    Returns:
        Initials string
    """
    if not name:
        return ''
    
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0][:2].upper()
    
    return (parts[0][0] + parts[-1][0]).upper()


def generate_welcome_coupon():
    """
    Generate welcome discount coupon code
    
    Returns:
        Coupon code string
    """
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"WELCOME{random_part}"


def paginate_results(items, page=1, per_page=20):
    """
    Paginate list of items
    
    Args:
        items: List of items
        page: Current page number
        per_page: Items per page
    
    Returns:
        Dictionary with paginated results
    """
    try:
        page = int(page)
        per_page = int(per_page)
    except (ValueError, TypeError):
        page = 1
        per_page = 20
    
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20
    if per_page > 100:
        per_page = 100
    
    total = len(items)
    total_pages = (total + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_items = items[start:end]
    
    return {
        'items': paginated_items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
