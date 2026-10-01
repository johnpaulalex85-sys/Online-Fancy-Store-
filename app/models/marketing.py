import uuid
import datetime
import logging
import math
from app.db import mongo

logger = logging.getLogger(__name__)

class Coupon:
    """Coupon model wrapping the MongoDB 'coupons' collection."""
    def __init__(self, doc):
        self._doc = doc
        self.id = str(doc.get('_id'))
        self.code = doc.get('code', '').upper()
        self.description = doc.get('description', '')
        self.discount_type = doc.get('discount_type', 'percentage') # percentage or fixed
        self.discount_value = float(doc.get('discount_value', 0.0))
        self.min_purchase = float(doc.get('min_purchase', 0.0))
        self.max_discount = float(doc.get('max_discount', 0.0))
        self.usage_limit = int(doc.get('usage_limit', 100))
        self.used_count = int(doc.get('used_count', 0))
        self.expiry_date = doc.get('expiry_date')
        self.status = doc.get('status', 'active')
        self.created_at = doc.get('created_at')

    def is_valid(self):
        if self.status != 'active':
            return False
        if self.used_count >= self.usage_limit:
            return False
        if self.expiry_date and datetime.datetime.now() > self.expiry_date:
            return False
        return True

    def increment_usage(self):
        mongo.get_collection('coupons').update_one(
            {"_id": self.id},
            {"$inc": {"used_count": 1}}
        )
        self.used_count += 1

    @classmethod
    def get_by_code(cls, code):
        if not code:
            return None
        doc = mongo.get_collection('coupons').find_one({"code": code.strip().upper()})
        return cls(doc) if doc else None

    @classmethod
    def get_by_id(cls, coupon_id):
        doc = mongo.get_collection('coupons').find_one({"_id": str(coupon_id)})
        return cls(doc) if doc else None

    @classmethod
    def get_all(cls):
        cursor = mongo.get_collection('coupons').find().sort("created_at", -1)
        return [cls(doc) for doc in cursor]

    @classmethod
    def create(cls, code, discount_type, discount_value, min_purchase=0.0, max_discount=0.0, usage_limit=100, expiry_days=30, description="", **kwargs):
        coupon_id = str(uuid.uuid4())
        expiry = datetime.datetime.now() + datetime.timedelta(days=int(expiry_days))
        doc = {
            "_id": coupon_id,
            "code": code.strip().upper(),
            "description": description.strip(),
            "discount_type": discount_type,
            "discount_value": float(discount_value),
            "min_purchase": float(min_purchase),
            "max_discount": float(max_discount),
            "usage_limit": int(usage_limit),
            "used_count": 0,
            "expiry_date": expiry,
            "status": "active",
            "created_at": datetime.datetime.now()
        }
        mongo.get_collection('coupons').insert_one(doc)
        return cls(doc)

    def update(self, description, discount_type, discount_value, min_purchase, max_discount, usage_limit, status="active"):
        self.description = description.strip()
        self.discount_type = discount_type
        self.discount_value = float(discount_value)
        self.min_purchase = float(min_purchase)
        self.max_discount = float(max_discount)
        self.usage_limit = int(usage_limit)
        self.status = status
        mongo.get_collection('coupons').update_one(
            {"_id": self.id},
            {"$set": {
                "description": self.description, "discount_type": self.discount_type,
                "discount_value": self.discount_value, "min_purchase": self.min_purchase,
                "max_discount": self.max_discount, "usage_limit": self.usage_limit,
                "status": self.status
            }}
        )

    def delete(self):
        mongo.get_collection('coupons').delete_one({"_id": self.id})

    def toggle_status(self):
        self.status = 'disabled' if self.status == 'active' else 'active'
        mongo.get_collection('coupons').update_one({"_id": self.id}, {"$set": {"status": self.status}})


_BANNERS_CACHE = None
_BANNERS_CACHE_TIME = 0.0
BANNERS_TTL = 60.0  # seconds

class Banner:
    """Banner model wrapping the MongoDB 'banners' collection with in-memory caching."""
    def __init__(self, doc):
        self._doc = doc
        self.id = str(doc.get('_id'))
        self.title = doc.get('title', '')
        self.subtitle = doc.get('subtitle', '')
        self.image_url = doc.get('image_url', '')
        self.link_url = doc.get('link_url', '#')
        self.banner_type = doc.get('banner_type', 'homepage') # homepage, category, festival, offer, popup
        self.position = int(doc.get('position', 1))
        self.status = doc.get('status', 'active')
        self.created_at = doc.get('created_at')

    @classmethod
    def _fetch_all_cached(cls):
        global _BANNERS_CACHE, _BANNERS_CACHE_TIME
        now = datetime.datetime.now().timestamp()
        if _BANNERS_CACHE is not None and (now - _BANNERS_CACHE_TIME) < BANNERS_TTL:
            return _BANNERS_CACHE
        try:
            cursor = mongo.get_collection('banners').find().sort([("banner_type", 1), ("position", 1)])
            docs = list(cursor)
            _BANNERS_CACHE = docs
            _BANNERS_CACHE_TIME = now
            return docs
        except Exception:
            return _BANNERS_CACHE or []

    @classmethod
    def clear_cache(cls):
        global _BANNERS_CACHE, _BANNERS_CACHE_TIME
        _BANNERS_CACHE = None
        _BANNERS_CACHE_TIME = 0.0

    @classmethod
    def get_by_type(cls, banner_type="homepage"):
        docs = cls._fetch_all_cached()
        matching = [d for d in docs if d.get('status') == 'active' and d.get('banner_type') == banner_type]
        return [cls(doc) for doc in matching]

    @classmethod
    def get_all(cls):
        docs = cls._fetch_all_cached()
        return [cls(doc) for doc in docs]

    @classmethod
    def get_by_id(cls, banner_id):
        doc = mongo.get_collection('banners').find_one({"_id": str(banner_id)})
        return cls(doc) if doc else None

    @classmethod
    def create(cls, title, subtitle, image_url, link_url, banner_type="homepage", position=1, **kwargs):
        banner_id = str(uuid.uuid4())
        pos = kwargs.get('sort_order', position)
        doc = {
            "_id": banner_id,
            "title": title.strip(),
            "subtitle": subtitle.strip(),
            "image_url": image_url.strip(),
            "link_url": link_url.strip() if link_url else '#',
            "banner_type": banner_type,
            "position": int(pos),
            "status": "active",
            "created_at": datetime.datetime.now()
        }
        mongo.get_collection('banners').insert_one(doc)
        cls.clear_cache()
        return cls(doc)

    def update(self, title, subtitle, image_url, link_url, banner_type, position, status="active"):
        self.title = title.strip()
        self.subtitle = subtitle.strip()
        self.image_url = image_url.strip()
        self.link_url = link_url.strip() if link_url else '#'
        self.banner_type = banner_type
        self.position = int(position)
        self.status = status
        mongo.get_collection('banners').update_one(
            {"_id": self.id},
            {"$set": {
                "title": self.title, "subtitle": self.subtitle, "image_url": self.image_url,
                "link_url": self.link_url, "banner_type": self.banner_type,
                "position": self.position, "status": self.status
            }}
        )
        Banner.clear_cache()

    def delete(self):
        mongo.get_collection('banners').delete_one({"_id": self.id})
        Banner.clear_cache()

    def toggle_status(self):
        self.status = 'disabled' if self.status == 'active' else 'active'
        mongo.get_collection('banners').update_one({"_id": self.id}, {"$set": {"status": self.status}})
        Banner.clear_cache()


class Review:
    """Review model wrapping the MongoDB 'reviews' collection."""
    def __init__(self, doc):
        self._doc = doc
        self.id = str(doc.get('_id'))
        self.product_id = doc.get('product_id')
        self.user_id = doc.get('user_id')
        self.user_name = doc.get('user_name', 'Anonymous')
        self.rating = int(doc.get('rating', 5))
        self.title = doc.get('title', '')
        self.comment = doc.get('comment', '')
        self.images = doc.get('images', [])
        self.status = doc.get('status', 'approved') # approved, pending, rejected
        self.created_at = doc.get('created_at')

    @classmethod
    def get_by_product(cls, product_id):
        cursor = mongo.get_collection('reviews').find({"product_id": str(product_id), "status": "approved"}).sort("created_at", -1)
        return [cls(doc) for doc in cursor]

    @classmethod
    def get_all(cls, filter_dict=None, page=1, per_page=20):
        if filter_dict is None:
            filter_dict = {}
        col = mongo.get_collection('reviews')
        total_count = col.count_documents(filter_dict)
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
        page = max(1, min(page, total_pages))
        
        cursor = col.find(filter_dict).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page)
        return {
            "reviews": [cls(doc) for doc in cursor],
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page
        }

    @classmethod
    def create(cls, product_id, user_id, user_name, rating, title, comment, images=None):
        rev_id = str(uuid.uuid4())
        doc = {
            "_id": rev_id,
            "product_id": str(product_id),
            "user_id": str(user_id),
            "user_name": user_name.strip(),
            "rating": max(1, min(int(rating), 5)),
            "title": title.strip(),
            "comment": comment.strip(),
            "images": images or [],
            "status": "approved", # Default to approved for immediate feedback
            "created_at": datetime.datetime.now()
        }
        mongo.get_collection('reviews').insert_one(doc)
        
        # Re-calculate product stats
        from app.models.product import Product
        prod = Product.get_by_id(product_id)
        if prod:
            prod.update_rating_stats()
            
        return cls(doc)

    def update_status(self, new_status):
        self.status = new_status
        mongo.get_collection('reviews').update_one({"_id": self.id}, {"$set": {"status": new_status}})
        from app.models.product import Product
        prod = Product.get_by_id(self.product_id)
        if prod:
            prod.update_rating_stats()

    def delete(self):
        mongo.get_collection('reviews').delete_one({"_id": self.id})
        from app.models.product import Product
        prod = Product.get_by_id(self.product_id)
        if prod:
            prod.update_rating_stats()


_SETTINGS_CACHE = {}
_SETTINGS_CACHE_TIME = 0.0
SETTINGS_TTL = 60.0  # seconds

class Setting:
    """Setting model wrapping the MongoDB 'settings' collection with in-memory TTL caching."""
    @classmethod
    def get_all(cls):
        global _SETTINGS_CACHE, _SETTINGS_CACHE_TIME
        now = datetime.datetime.now().timestamp()
        if _SETTINGS_CACHE and (now - _SETTINGS_CACHE_TIME) < SETTINGS_TTL:
            return dict(_SETTINGS_CACHE)
        settings = {}
        try:
            for doc in mongo.get_collection('settings').find():
                settings[doc['key']] = doc['value']
            _SETTINGS_CACHE = settings
            _SETTINGS_CACHE_TIME = now
        except Exception as e:
            logger.error(f"Error fetching settings: {e}")
        return settings or dict(_SETTINGS_CACHE)

    @classmethod
    def get(cls, key, default=None):
        all_settings = cls.get_all()
        return all_settings.get(key, default)

    @classmethod
    def set(cls, key, value):
        global _SETTINGS_CACHE, _SETTINGS_CACHE_TIME
        try:
            mongo.get_collection('settings').update_one(
                {"key": key},
                {"$set": {"value": value, "updated_at": datetime.datetime.now()}},
                upsert=True
            )
            _SETTINGS_CACHE[key] = value
            _SETTINGS_CACHE_TIME = datetime.datetime.now().timestamp()
        except Exception as e:
            logger.error(f"Error setting configuration {key}: {e}")

    @classmethod
    def clear_cache(cls):
        global _SETTINGS_CACHE, _SETTINGS_CACHE_TIME
        _SETTINGS_CACHE = {}
        _SETTINGS_CACHE_TIME = 0.0
