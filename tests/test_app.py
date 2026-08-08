import unittest
from unittest.mock import MagicMock, patch
import os
import json
import datetime

# Fake Mongo Cursor and Collection for unit testing without live MongoDB server
class FakeCursor:
    def __init__(self, docs=None):
        self.docs = docs or [
            {
                "_id": "prod-1",
                "name": "Apple iPhone 15 Pro Max",
                "brand": "Apple",
                "slug": "apple-iphone-15-pro-max",
                "sku": "APPL-IP15PM-256",
                "regular_price": 159900.0,
                "offer_price": 149900.0,
                "discount": 6.0,
                "stock_quantity": 25,
                "status": "active",
                "featured_product": True,
                "images": ["https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=800"],
                "thumbnail": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600",
                "rating": 4.8,
                "review_count": 120,
                "date_created": datetime.datetime.now()
            },
            {
                "_id": "prod-2",
                "name": "Samsung Galaxy S24 Ultra",
                "brand": "Samsung",
                "slug": "samsung-galaxy-s24-ultra",
                "sku": "SAMS-S24U-512",
                "regular_price": 139999.0,
                "offer_price": 129999.0,
                "discount": 7.0,
                "stock_quantity": 15,
                "status": "active",
                "featured_product": True,
                "images": ["https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=800"],
                "thumbnail": "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=600",
                "rating": 4.7,
                "review_count": 95,
                "date_created": datetime.datetime.now()
            }
        ]
    def sort(self, *args, **kwargs): return self
    def skip(self, *args, **kwargs): return self
    def limit(self, *args, **kwargs): return self
    def __iter__(self): return iter(self.docs)
    def __list__(self): return self.docs

class FakeCollection:
    def __init__(self, name):
        self.name = name
    def find_one(self, query=None, *args, **kwargs):
        if self.name == 'cart':
            return {"_id": "cart-1", "user_id": "user-1", "session_id": "sess-1", "items": [], "coupon_code": None}
        if self.name == 'wishlist':
            return {"_id": "wish-1", "user_id": "user-1", "session_id": "sess-1", "product_ids": ["prod-1"]}
        if self.name == 'categories':
            return {"_id": "cat-1", "name": "Mobiles & Tablets", "slug": "mobiles-tablets", "icon": "fa-mobile-alt", "status": "active", "parent_id": None}
        if self.name == 'brands':
            return {"_id": "brand-1", "name": "Apple", "slug": "apple", "logo": "", "status": "active"}
        if self.name == 'products':
            return FakeCursor().docs[0]
        if self.name == 'banners':
            return {"_id": "ban-1", "title": "Welcome Banner", "image_url": "http://example.com/ban.jpg", "status": "active", "banner_type": "homepage"}
        return {"_id": "doc-1", "name": "Sample Doc", "status": "active"}
    def find(self, *args, **kwargs):
        return FakeCursor()
    def count_documents(self, *args, **kwargs):
        return 2
    def insert_one(self, *args, **kwargs):
        res = MagicMock()
        res.inserted_id = "new-doc-id"
        return res
    def update_one(self, *args, **kwargs): return MagicMock()
    def delete_one(self, *args, **kwargs): return MagicMock()

def fake_get_collection(name):
    return FakeCollection(name)

# Patch mongo.get_collection globally before importing app routes that trigger DB during test requests
patcher = patch('app.db.mongo.get_collection', side_effect=fake_get_collection)
patcher.start()

from app import create_app

class FancyStoreAppTestCase(unittest.TestCase):
    """Automated integration and verification test suite for Fancy Store E-Commerce Platform."""

    @classmethod
    def setUpClass(cls):
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['MONGO_URI'] = 'mongodb://localhost:27017/fancy_store_test'
        cls.app = create_app('testing')
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        patcher.stop()

    def test_01_app_factory_initialization(self):
        """Verify application factory initializes correctly in testing mode."""
        self.assertIsNotNone(self.app)
        self.assertTrue(self.app.config['TESTING'])
        self.assertEqual(self.app.config['WTF_CSRF_ENABLED'], False)

    def test_02_homepage_route(self):
        """Verify main storefront homepage renders with 200 OK status."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Fancy Store', response.data)

    def test_03_catalog_route(self):
        """Verify faceted catalog search page renders correctly."""
        response = self.client.get('/catalog')
        self.assertEqual(response.status_code, 200)

    def test_04_auth_pages_render(self):
        """Verify authentication login and signup forms render."""
        resp_login = self.client.get('/auth/login')
        self.assertEqual(resp_login.status_code, 200)
        self.assertIn(b'Sign In', resp_login.data)

        resp_register = self.client.get('/auth/register')
        self.assertEqual(resp_register.status_code, 200)
        self.assertIn(b'Create Account', resp_register.data)

    def test_05_cart_and_wishlist_pages(self):
        """Verify shopping cart and wishlist routes return valid responses."""
        resp_cart = self.client.get('/cart/')
        self.assertEqual(resp_cart.status_code, 200)

        resp_wish = self.client.get('/cart/wishlist')
        self.assertEqual(resp_wish.status_code, 200)

    def test_06_api_search_endpoint(self):
        """Verify JSON API search suggestions endpoint returns correct format."""
        response = self.client.get('/api/search/suggestions?q=Apple')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('suggestions', data)
        self.assertIsInstance(data['suggestions'], list)

    def test_07_protected_routes_redirect(self):
        """Verify unauthenticated requests to protected customer & admin routes redirect to login."""
        resp_orders = self.client.get('/orders/', follow_redirects=False)
        self.assertEqual(resp_orders.status_code, 302)
        self.assertIn('/auth/login', resp_orders.headers['Location'])

        resp_admin = self.client.get('/admin/', follow_redirects=False)
        self.assertEqual(resp_admin.status_code, 302)
        self.assertIn('/auth/login', resp_admin.headers['Location'])


if __name__ == '__main__':
    unittest.main()
