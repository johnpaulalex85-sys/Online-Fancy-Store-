import os
from app import create_app
from app.db import mongo

app = create_app(os.getenv('FLASK_ENV', 'development'))

with app.app_context():
    valid_collections = [
        'admins', 'users', 'products', 'categories', 'brands', 'orders',
        'cart', 'wishlist', 'reviews', 'coupons', 'banners', 'notifications', 'settings'
    ]
    print("Clearing collections...")
    for col in valid_collections:
        mongo.get_collection(col).delete_many({})
    print("Database cleared successfully!")
