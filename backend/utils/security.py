"""
Security Utilities - Headers, Input Sanitization, File Validation
"""
import bleach
import imghdr
import io
from werkzeug.utils import secure_filename

# Allowed HTML tags for rich text (if needed)
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u']
ALLOWED_ATTRIBUTES = {}

def setup_security_headers(response):
    """
    Add security headers to all responses
    """
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # XSS Protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://js.paystack.co; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self' https://api.paystack.co; "
        "frame-src https://checkout.paystack.co;"
    )
    
    # Strict Transport Security (HTTPS only)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions Policy
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    return response


def sanitize_input(text, allow_html=False):
    """
    Sanitize user input to prevent XSS attacks
    
    Args:
        text: Input text to sanitize
        allow_html: Whether to allow safe HTML tags
    
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    if allow_html:
        # Allow safe HTML tags
        return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    else:
        # Strip all HTML
        return bleach.clean(text, tags=[], strip=True)


def sanitize_dict(data_dict, allow_html_fields=None):
    """
    Sanitize all string values in a dictionary
    
    Args:
        data_dict: Dictionary to sanitize
        allow_html_fields: List of field names that can contain HTML
    
    Returns:
        Sanitized dictionary
    """
    if not data_dict:
        return data_dict
    
    allow_html_fields = allow_html_fields or []
    sanitized = {}
    
    for key, value in data_dict.items():
        if isinstance(value, str):
            allow_html = key in allow_html_fields
            sanitized[key] = sanitize_input(value, allow_html=allow_html)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, allow_html_fields)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_input(item, allow_html=key in allow_html_fields) if isinstance(item, str) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized


def validate_image_file(file_storage, max_size_mb=2):
    """
    Validate uploaded image file
    
    Args:
        file_storage: Flask FileStorage object
        max_size_mb: Maximum file size in MB
    
    Returns:
        tuple: (is_valid, error_message or None)
    """
    if not file_storage:
        return False, "No file provided"
    
    # Check filename
    filename = secure_filename(file_storage.filename)
    if not filename:
        return False, "Invalid filename"
    
    # Check file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if file_ext not in allowed_extensions:
        return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
    
    # Check file size
    file_storage.seek(0, io.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)
    
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"File too large. Maximum size: {max_size_mb}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    # Verify file content matches extension (basic check)
    file_header = file_storage.read(512)
    file_storage.seek(0)
    
    image_type = imghdr.what(None, file_header)
    if image_type not in ['png', 'jpeg', 'gif', 'webp']:
        return False, "File content does not match image type"
    
    return True, None


def generate_secure_filename(original_filename):
    """
    Generate a secure filename with random suffix
    
    Args:
        original_filename: Original filename
    
    Returns:
        Secure filename
    """
    import uuid
    
    filename = secure_filename(original_filename)
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, 'jpg')
    unique_id = uuid.uuid4().hex[:8]
    
    return f"{name}_{unique_id}.{ext.lower()}"
