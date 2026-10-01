import os
import sys
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
    demo_mode = '--prod' not in sys.argv and '--production' not in sys.argv
    with app.app_context():
        seed_database(app, production_mode=not demo_mode)
        print("[DONE] Enterprise database seeding completed successfully!")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['seed', '--seed', 'seed_db']:
        demo_mode = '--prod' not in sys.argv and '--production' not in sys.argv
        from app.utils.seed import seed_database
        with app.app_context():
            seed_database(app, production_mode=not demo_mode)
            print("[DONE] Enterprise database seeding completed successfully!")
    else:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))

