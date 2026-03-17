"""
Validation Utilities - Input validation and sanitization
"""
import re
from email_validator import validate_email as email_validator, EmailNotValidError


def validate_email(email):
    """
    Validate email address format
    
    Args:
        email: Email address string
    
    Returns:
        tuple: (is_valid, normalized_email_or_error)
    """
    if not email:
        return False, "Email is required"
    
    try:
        validation = email_validator(email.strip(), check_deliverability=False)
        return True, validation.email
    except EmailNotValidError as e:
        return False, str(e)


def validate_phone(phone):
    """
    Validate Nigerian phone number
    
    Args:
        phone: Phone number string
    
    Returns:
        tuple: (is_valid, normalized_phone_or_error)
    """
    if not phone:
        return True, None  # Phone is optional
    
    # Remove all non-numeric characters
    cleaned = re.sub(r'\D', '', phone)
    
    # Nigerian phone numbers: 11 digits starting with 0, or 13 digits starting with 234
    if len(cleaned) == 11 and cleaned.startswith('0'):
        # Convert to international format
        return True, '+234' + cleaned[1:]
    elif len(cleaned) == 13 and cleaned.startswith('234'):
        return True, '+' + cleaned
    elif len(cleaned) == 10:
        # Assume missing country code
        return True, '+234' + cleaned
    else:
        return False, "Invalid Nigerian phone number format"


def validate_required_fields(data, required_fields):
    """
    Validate that required fields are present and not empty
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
    
    Returns:
        tuple: (is_valid, missing_fields)
    """
    missing = []
    
    for field in required_fields:
        if field not in data or data[field] is None or str(data[field]).strip() == '':
            missing.append(field)
    
    return len(missing) == 0, missing


def validate_price(price):
    """
    Validate price value
    
    Args:
        price: Price value (string or number)
    
    Returns:
        tuple: (is_valid, price_float_or_error)
    """
    if price is None or price == '':
        return False, "Price is required"
    
    try:
        price_float = float(price)
        if price_float < 0:
            return False, "Price cannot be negative"
        if price_float > 9999999.99:
            return False, "Price exceeds maximum allowed"
        return True, price_float
    except (ValueError, TypeError):
        return False, "Invalid price format"


def validate_quantity(quantity, max_quantity=10):
    """
    Validate quantity value
    
    Args:
        quantity: Quantity value
        max_quantity: Maximum allowed quantity
    
    Returns:
        tuple: (is_valid, quantity_int_or_error)
    """
    if quantity is None or quantity == '':
        return False, "Quantity is required"
    
    try:
        qty_int = int(quantity)
        if qty_int < 1:
            return False, "Quantity must be at least 1"
        if qty_int > max_quantity:
            return False, f"Maximum quantity allowed is {max_quantity}"
        return True, qty_int
    except (ValueError, TypeError):
        return False, "Invalid quantity format"


def validate_size(size, valid_sizes=None):
    """
    Validate size value
    
    Args:
        size: Size string
        valid_sizes: List of valid sizes
    
    Returns:
        tuple: (is_valid, size_upper_or_error)
    """
    valid_sizes = valid_sizes or ['S', 'M', 'L', 'XL', 'XXL']
    
    if not size:
        return False, "Size is required"
    
    size_upper = size.strip().upper()
    if size_upper not in valid_sizes:
        return False, f"Invalid size. Allowed: {', '.join(valid_sizes)}"
    
    return True, size_upper


def validate_gender(gender):
    """
    Validate gender value
    
    Args:
        gender: Gender string
    
    Returns:
        tuple: (is_valid, normalized_gender_or_error)
    """
    valid_genders = ['men', 'women', 'unisex']
    
    if not gender:
        return False, "Gender is required"
    
    gender_lower = gender.strip().lower()
    if gender_lower not in valid_genders:
        return False, f"Invalid gender. Allowed: {', '.join(valid_genders)}"
    
    return True, gender_lower


def validate_delivery_address(address):
    """
    Validate delivery address
    
    Args:
        address: Address dictionary
    
    Returns:
        tuple: (is_valid, error_message_or_none)
    """
    if not address or not isinstance(address, dict):
        return False, "Address must be a valid object"
    
    required_fields = ['street', 'city', 'state']
    is_valid, missing = validate_required_fields(address, required_fields)
    
    if not is_valid:
        return False, f"Missing address fields: {', '.join(missing)}"
    
    # Validate Lagos state
    state = address.get('state', '').lower()
    if state != 'lagos':
        return False, "We currently only deliver to Lagos State"
    
    return True, None


def validate_delivery_zone(zone):
    """
    Validate delivery zone
    
    Args:
        zone: Zone string
    
    Returns:
        tuple: (is_valid, normalized_zone_or_error)
    """
    valid_zones = {
        'island': 'Lagos Island',
        'mainland': 'Lagos Mainland',
        'outside': 'Outside Lagos'
    }
    
    if not zone:
        return False, "Delivery zone is required"
    
    zone_lower = zone.strip().lower()
    if zone_lower not in valid_zones:
        return False, f"Invalid zone. Allowed: {', '.join(valid_zones.keys())}"
    
    return True, zone_lower


def sanitize_string(value, max_length=None, allow_newlines=False):
    """
    Sanitize string input
    
    Args:
        value: String value
        max_length: Maximum length
        allow_newlines: Whether to allow newlines
    
    Returns:
        Sanitized string
    """
    if not value:
        return value
    
    # Convert to string
    value = str(value).strip()
    
    # Remove newlines if not allowed
    if not allow_newlines:
        value = value.replace('\n', ' ').replace('\r', '')
    
    # Truncate if too long
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value
