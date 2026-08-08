import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-secret-key-default'
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/'
    MONGODB_DB_NAME = os.environ.get('MONGODB_DB_NAME') or 'fancy_store_db'
    
    # Store settings
    STORE_NAME = os.environ.get('STORE_NAME', 'Fancy Store')
    STORE_EMAIL = os.environ.get('STORE_EMAIL', 'support@fancystore.com')
    STORE_PHONE = os.environ.get('STORE_PHONE', '+91 98765 43210')
    CURRENCY_SYMBOL = os.environ.get('CURRENCY_SYMBOL', '₹')
    GST_RATE = float(os.environ.get('GST_RATE', 18.0))
    FREE_SHIPPING_THRESHOLD = float(os.environ.get('FREE_SHIPPING_THRESHOLD', 999.0))
    STANDARD_SHIPPING_CHARGE = float(os.environ.get('STANDARD_SHIPPING_CHARGE', 49.0))
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    
    # Session & Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600 * 24 * 30  # 30 days
    CSRF_ENABLED = True

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    EXPLAIN_TEMPLATE_LOADING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    MONGODB_DB_NAME = 'fancy_store_test_db'

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
