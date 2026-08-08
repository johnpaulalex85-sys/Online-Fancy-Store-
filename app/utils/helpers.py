import os
import re
import uuid
import datetime
from werkzeug.utils import secure_filename

def slugify_text(text):
    """Convert arbitrary text into a URL-friendly slug."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text

def format_currency(value, symbol='₹'):
    """Format a numerical value into standard Indian/International currency representation."""
    try:
        val = float(value)
        return f"{symbol}{val:,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"

def generate_sku(category_name, brand_name, product_name):
    """Generate a unique alphanumeric SKU code."""
    cat_part = (category_name[:3] if category_name else "GEN").upper()
    brand_part = (brand_name[:3] if brand_name else "BRD").upper()
    prod_part = (product_name[:3] if product_name else "PRD").upper()
    unique_suffix = uuid.uuid4().hex[:4].upper()
    return f"{cat_part}-{brand_part}-{prod_part}-{unique_suffix}"

def generate_order_number():
    """Generate a chronological order tracking number."""
    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d")
    random_str = uuid.uuid4().hex[:6].upper()
    return f"ORD-{date_str}-{random_str}"

def allowed_file(filename, allowed_extensions=None):
    """Check if the filename has an allowed file extension."""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file_storage, upload_folder, subfolder='products'):
    """Save an uploaded Werkzeug FileStorage securely and return the relative web path."""
    if not file_storage or not file_storage.filename:
        return None
    
    filename = secure_filename(file_storage.filename)
    # Prefix filename with timestamp/uuid to avoid collisions
    unique_filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}_{filename}"
    
    target_dir = os.path.join(upload_folder, subfolder)
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = os.path.join(target_dir, unique_filename)
    file_storage.save(file_path)
    
    # Return path relative to static folder for web rendering
    return f"uploads/{subfolder}/{unique_filename}"


def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the geodesic distance in kilometers between two points (lat/lon) on Earth using Haversine formula."""
    import math
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    except (ValueError, TypeError):
        return float('inf')
        
    R = 6371.0 # Earth radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c
