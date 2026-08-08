import os
import logging
from app import create_app
from app.db import mongo
from app.models.user import User
from app.models.product import Category, Brand, Product
from app.models.marketing import Coupon, Banner

# Initialize Flask application
app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.cli.command("seed")
def seed_db():
    """CLI command: Seed all 13 MongoDB collections with initial Flipkart-style demo catalog and admin account."""
    from app.utils.seed import seed_database
    with app.app_context():
        seed_database(app)
        print("[DONE] Enterprise database seeding completed successfully!")



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))
