import re
from html import escape

def sanitize_input(text):
    """Sanitize user string input to prevent XSS attacks."""
    if not isinstance(text, str):
        return text
    # Strip dangerous tags
    clean = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    clean = re.sub(r'<.*?on\w+=.*?>', '', clean, flags=re.IGNORECASE)
    return escape(clean.strip())

def register_security_middleware(app):
    """Attach security HTTP headers to all Flask responses."""
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
