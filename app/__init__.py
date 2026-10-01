import logging
from flask import Flask, render_template, session, request
from app.config import config_by_name
from app.extensions import login_manager, csrf
from app.db import mongo
from app.utils.helpers import format_currency

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    """Application factory for Fancy Store."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    mongo.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register security HTTP headers
    from app.middleware.security import register_security_middleware
    register_security_middleware(app)

    # Register custom template filters
    app.jinja_env.filters['currency'] = format_currency

    # Register Blueprints
    with app.app_context():
        # Import Blueprints within context to prevent circular imports
        try:
            from app.auth.routes import auth_bp
            app.register_blueprint(auth_bp, url_prefix='/auth')
        except ImportError as e:
            logger.warning(f"Could not register auth_bp: {e}")

        try:
            from app.main.routes import main_bp
            app.register_blueprint(main_bp)
        except ImportError as e:
            logger.warning(f"Could not register main_bp: {e}")

        try:
            from app.cart.routes import cart_bp
            app.register_blueprint(cart_bp, url_prefix='/cart')
        except ImportError as e:
            logger.warning(f"Could not register cart_bp: {e}")

        try:
            from app.orders.routes import orders_bp
            app.register_blueprint(orders_bp, url_prefix='/orders')
        except ImportError as e:
            logger.warning(f"Could not register orders_bp: {e}")

        try:
            from app.admin.routes import admin_bp
            app.register_blueprint(admin_bp, url_prefix='/admin')
        except ImportError as e:
            logger.warning(f"Could not register admin_bp: {e}")

    # Browser cache control for static assets
    @app.after_request
    def add_browser_cache_headers(response):
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        return response

    # Register Global Context Processor (High-performance in-memory cached)
    @app.context_processor
    def inject_global_data():
        from flask_login import current_user
        from app.models.marketing import Setting
        from app.models.product import Category
        
        settings = Setting.get_all()
        nav_categories = []
        cart_count = 0
        wishlist_count = 0
        
        try:
            if mongo.db is not None:
                cats = Category.get_all_active()
                nav_categories = [{
                    'id': c.id,
                    'name': c.name,
                    'slug': c.slug,
                    'icon': c.icon,
                    'image': c.image,
                    'description': c.description,
                    'parent_id': c.parent_id
                } for c in cats]
                
                # Fast projection lookup for Cart & Wishlist counts
                if current_user.is_authenticated and hasattr(current_user, 'id'):
                    cart_doc = mongo.db.cart.find_one({"user_id": current_user.id}, {"items": 1})
                    if cart_doc and 'items' in cart_doc:
                        cart_count = sum(item.get('quantity', 1) for item in cart_doc['items'])
                    wish_doc = mongo.db.wishlist.find_one({"user_id": current_user.id}, {"product_ids": 1})
                    if wish_doc and 'product_ids' in wish_doc:
                        wishlist_count = len(wish_doc['product_ids'])
                elif 'session_id' in session:
                    cart_doc = mongo.db.cart.find_one({"session_id": session['session_id']}, {"items": 1})
                    if cart_doc and 'items' in cart_doc:
                        cart_count = sum(item.get('quantity', 1) for item in cart_doc['items'])
        except Exception as e:
            logger.debug(f"Context processor query error: {e}")

        return dict(
            store_settings=settings,
            settings=settings,
            nav_categories=nav_categories,
            cart_count=cart_count,
            wishlist_count=wishlist_count
        )

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(error):
        try:
            return render_template('errors/404.html'), 404
        except Exception:
            return "404 Page Not Found", 404

    @app.errorhandler(500)
    def internal_server_error(error):
        try:
            return render_template('errors/500.html'), 500
        except Exception:
            return "500 Internal Server Error", 500

    @app.errorhandler(403)
    def forbidden_access(error):
        try:
            return render_template('errors/403.html'), 403
        except Exception:
            return "403 Forbidden Access", 403

    return app
