import logging
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

class MongoDB:
    """MongoDB database connection manager and index initializer."""
    def __init__(self, app=None):
        self.client = None
        self.db = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        uri = app.config.get('MONGODB_URI', 'mongodb://localhost:27017/')
        db_name = app.config.get('MONGODB_DB_NAME', 'fancy_store_db')
        try:
            self.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                socketTimeoutMS=10000,
                maxPoolSize=50,
                minPoolSize=5
            )
            self.db = self.client[db_name]
            # Verify connection
            self.client.admin.command('ping')
            # Create indexes
            self.create_indexes()
            logger.info(f"Successfully connected to MongoDB database: {db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")

    def get_collection(self, name):
        """Retrieve a MongoDB collection by name."""
        if self.db is None:
            raise RuntimeError("Database not initialized. Call init_app first.")
        return self.db[name]

    def create_indexes(self):
        """Create necessary indexes for all 13 MongoDB collections."""
        if self.db is None:
            return
        
        try:
            # 1. users
            self.db.users.create_index("email", unique=True)
            self.db.users.create_index("created_at")

            # 2. admins
            self.db.admins.create_index("email", unique=True)

            # 3. products
            self.db.products.create_index("slug", unique=True)
            self.db.products.create_index("sku", unique=True)
            self.db.products.create_index("category")
            self.db.products.create_index("subcategory")
            self.db.products.create_index("brand")
            self.db.products.create_index("status")
            self.db.products.create_index("featured_product")
            self.db.products.create_index("trending_product")
            self.db.products.create_index("best_seller")
            self.db.products.create_index("new_arrival")
            self.db.products.create_index([("offer_price", ASCENDING)])
            self.db.products.create_index([("rating", DESCENDING)])
            self.db.products.create_index([("date_created", DESCENDING)])
            self.db.products.create_index(
                [("name", TEXT), ("description", TEXT), ("tags", TEXT), ("brand", TEXT), ("category", TEXT)],
                name="product_text_search"
            )

            # 4. categories
            self.db.categories.create_index("slug", unique=True)
            self.db.categories.create_index("parent_id")
            self.db.categories.create_index([("display_order", ASCENDING)])

            # 5. brands
            self.db.brands.create_index("slug", unique=True)
            self.db.brands.create_index("name")

            # 6. orders
            self.db.orders.create_index("order_number", unique=True)
            self.db.orders.create_index("user_id")
            self.db.orders.create_index("order_status")
            self.db.orders.create_index([("created_at", DESCENDING)])

            # 7. cart
            self.db.cart.create_index("user_id", unique=True)
            self.db.cart.create_index("session_id")

            # 8. wishlist
            self.db.wishlist.create_index("user_id", unique=True)

            # 9. reviews
            self.db.reviews.create_index([("product_id", ASCENDING), ("created_at", DESCENDING)])
            self.db.reviews.create_index("user_id")
            self.db.reviews.create_index("status")

            # 10. coupons
            self.db.coupons.create_index("code", unique=True)
            self.db.coupons.create_index("status")
            self.db.coupons.create_index("expiry_date")

            # 11. banners
            self.db.banners.create_index("banner_type")
            self.db.banners.create_index([("position", ASCENDING)])
            self.db.banners.create_index("status")

            # 12. notifications
            self.db.notifications.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
            self.db.notifications.create_index("is_read")

            # 13. settings
            self.db.settings.create_index("key", unique=True)

            # Ensure default super admin exists
            if self.db.admins.count_documents({"email": "admin@fancystore.com"}) == 0:
                from werkzeug.security import generate_password_hash
                import datetime, uuid
                self.db.admins.insert_one({
                    "_id": str(uuid.uuid4()),
                    "name": "Super Admin",
                    "email": "admin@fancystore.com",
                    "password": generate_password_hash("admin123"),
                    "role": "super_admin",
                    "status": "active",
                    "created_at": datetime.datetime.now()
                })

            # Ensure default ad banners exist if empty
            if self.db.banners.count_documents({}) == 0:
                import datetime, uuid
                default_banners = [
                    {
                        "_id": str(uuid.uuid4()),
                        "title": "Exclusive Tech & Mobile Deals",
                        "subtitle": "Up to 30% Off New Smartphone Arrivals",
                        "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=1200&q=80",
                        "link_url": "/catalog",
                        "banner_type": "homepage",
                        "position": 1,
                        "status": "active",
                        "created_at": datetime.datetime.now()
                    },
                    {
                        "_id": str(uuid.uuid4()),
                        "title": "Modern Home & Lifestyle Essentials",
                        "subtitle": "Transform your living space with luxury essentials",
                        "image_url": "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?auto=format&fit=crop&w=1200&q=80",
                        "link_url": "/catalog",
                        "banner_type": "homepage",
                        "position": 2,
                        "status": "active",
                        "created_at": datetime.datetime.now()
                    },
                    {
                        "_id": str(uuid.uuid4()),
                        "title": "Curated Fashion & Beauty Collections",
                        "subtitle": "Premium quality guaranteed & fast shipping",
                        "image_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=1200&q=80",
                        "link_url": "/catalog",
                        "banner_type": "homepage",
                        "position": 3,
                        "status": "active",
                        "created_at": datetime.datetime.now()
                    }
                ]
                self.db.banners.insert_many(default_banners)

            logger.info("MongoDB database indexes verified and initialized.")
        except Exception as e:
            logger.error(f"Error creating MongoDB indexes: {e}")

# Global MongoDB instance
mongo = MongoDB()
