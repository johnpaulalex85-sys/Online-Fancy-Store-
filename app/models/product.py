import uuid
import datetime
import logging
import math
from app.db import mongo
from app.utils.helpers import slugify_text, generate_sku

logger = logging.getLogger(__name__)

class Product:
    """Product model wrapping the MongoDB 'products' collection."""
    def __init__(self, doc):
        self._doc = doc
        self.id = str(doc.get('_id'))
        self.name = doc.get('name', '')
        self.slug = doc.get('slug', '')
        self.sku = doc.get('sku', '')
        self.barcode = doc.get('barcode', '')
        self.category = doc.get('category', '')
        self.category_id = doc.get('category_id', self.category)
        self.subcategory = doc.get('subcategory', '')
        self.brand = doc.get('brand', '')
        self.description = doc.get('description', '')
        self.short_description = doc.get('short_description', '')
        self.highlights = doc.get('highlights', [])
        self.specifications = doc.get('specifications', {})
        self.variants = doc.get('variants', [])
        self.regular_price = float(doc.get('regular_price', 0.0))
        self.offer_price = float(doc.get('offer_price', self.regular_price))
        self.discount = float(doc.get('discount', 0.0))
        self.gst = float(doc.get('gst', 18.0))
        self.stock_quantity = int(doc.get('stock_quantity', 0))
        self.images = doc.get('images', [])
        self.thumbnail = doc.get('thumbnail', self.images[0] if self.images else '')
        self.tags = doc.get('tags', [])
        self.rating = float(doc.get('rating', 0.0))
        self.review_count = int(doc.get('review_count', 0))
        self.status = doc.get('status', 'active')
        self.featured_product = doc.get('featured_product', False)
        self.trending_product = doc.get('trending_product', False)
        self.best_seller = doc.get('best_seller', False)
        self.new_arrival = doc.get('new_arrival', False)
        self.date_created = doc.get('date_created')
        self.last_updated = doc.get('last_updated')

    @property
    def price_after_discount(self):
        return min(self.offer_price, self.regular_price)

    @property
    def price(self):
        return self.offer_price if self.offer_price else self.regular_price

    @property
    def is_featured(self):
        return self.featured_product

    @property
    def rating_avg(self):
        return self.rating

    @property
    def rating_count(self):
        return self.review_count

    @property
    def in_stock(self):
        return self.stock_quantity > 0 and self.status == 'active'

    @classmethod
    def get_by_id(cls, prod_id):
        try:
            doc = mongo.get_collection('products').find_one({"_id": str(prod_id)})
            return cls(doc) if doc else None
        except Exception as e:
            logger.error(f"Error fetching product by id {prod_id}: {e}")
            return None

    @classmethod
    def get_by_slug(cls, slug):
        try:
            doc = mongo.get_collection('products').find_one({"slug": slug})
            return cls(doc) if doc else None
        except Exception as e:
            logger.error(f"Error fetching product by slug {slug}: {e}")
            return None

    @classmethod
    def get_by_sku(cls, sku):
        try:
            doc = mongo.get_collection('products').find_one({"sku": sku})
            return cls(doc) if doc else None
        except Exception as e:
            logger.error(f"Error fetching product by sku {sku}: {e}")
            return None

    @classmethod
    def get_all(cls, filter_dict=None, sort_by=None, page=1, per_page=12):
        if filter_dict is None:
            filter_dict = {}
        
        try:
            # Build sort criteria
            sort_criteria = [("date_created", -1)]
            if sort_by == 'price_asc':
                sort_criteria = [("offer_price", 1)]
            elif sort_by == 'price_desc':
                sort_criteria = [("offer_price", -1)]
            elif sort_by == 'rating_desc':
                sort_criteria = [("rating", -1)]
            elif sort_by == 'popularity':
                sort_criteria = [("review_count", -1), ("rating", -1)]
                
            col = mongo.get_collection('products')
            total_count = col.count_documents(filter_dict)
            total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
            page = max(1, min(page, total_pages))
            
            cursor = col.find(filter_dict).sort(sort_criteria).skip((page - 1) * per_page).limit(per_page)
            products = [cls(doc) for doc in cursor]
            
            return {
                "products": products,
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": page,
                "per_page": per_page
            }
        except Exception as e:
            logger.warning(f"Database error in Product.get_all: {e}")
            return {
                "products": [],
                "total_count": 0,
                "total_pages": 1,
                "current_page": 1,
                "per_page": per_page
            }

    @classmethod
    def search(cls, query='', category=None, category_id=None, brand=None, min_price=None, max_price=None, min_rating=None, sort_by=None, page=1, per_page=12, **kwargs):
        filter_dict = {"status": {"$in": ["active", "not_available", "coming_soon"]}}
        
        if query and query.strip():
            regex_pattern = {"$regex": query.strip(), "$options": "i"}
            filter_dict["$or"] = [
                {"name": regex_pattern},
                {"brand": regex_pattern},
                {"category": regex_pattern},
                {"subcategory": regex_pattern},
                {"tags": regex_pattern}
            ]
            
        cat_val = category or category_id
        if cat_val and cat_val != 'all':
            if "$or" in filter_dict:
                filter_dict["$and"] = [{"$or": filter_dict.pop("$or")}, {"$or": [{"category": str(cat_val)}, {"subcategory": str(cat_val)}, {"category_id": str(cat_val)}]}]
            else:
                filter_dict["$or"] = [{"category": str(cat_val)}, {"subcategory": str(cat_val)}, {"category_id": str(cat_val)}]
                
        if brand and brand != 'all':
            filter_dict["brand"] = brand
        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter["$gte"] = float(min_price)
            if max_price is not None:
                price_filter["$lte"] = float(max_price)
            filter_dict["offer_price"] = price_filter
        if min_rating and float(min_rating) > 0:
            filter_dict["rating"] = {"$gte": float(min_rating)}
            
        return cls.get_all(filter_dict, sort_by=sort_by, page=page, per_page=per_page)

    @classmethod
    def get_featured(cls, limit=8):
        col = mongo.get_collection('products')
        cursor = col.find({"status": {"$in": ["active", "not_available", "coming_soon"]}, "featured_product": True}).sort("rating", -1).limit(limit)
        return [cls(doc) for doc in cursor]

    @classmethod
    def get_trending(cls, limit=8):
        col = mongo.get_collection('products')
        cursor = col.find({"status": {"$in": ["active", "not_available", "coming_soon"]}, "trending_product": True}).sort("review_count", -1).limit(limit)
        return [cls(doc) for doc in cursor]

    @classmethod
    def get_best_sellers(cls, limit=8):
        col = mongo.get_collection('products')
        cursor = col.find({"status": {"$in": ["active", "not_available", "coming_soon"]}, "best_seller": True}).sort("rating", -1).limit(limit)
        return [cls(doc) for doc in cursor]

    @classmethod
    def get_new_arrivals(cls, limit=8):
        col = mongo.get_collection('products')
        cursor = col.find({"status": {"$in": ["active", "not_available", "coming_soon"]}, "new_arrival": True}).sort("date_created", -1).limit(limit)
        return [cls(doc) for doc in cursor]

    def update_stock(self, quantity_change):
        """Atomically change stock (negative for order placement, positive for return/restock)."""
        mongo.get_collection('products').update_one(
            {"_id": self.id},
            {"$inc": {"stock_quantity": quantity_change}, "$set": {"last_updated": datetime.datetime.now()}}
        )
        self.stock_quantity += quantity_change

    def update_rating_stats(self):
        """Re-calculate average rating and review count from approved reviews."""
        col = mongo.get_collection('reviews')
        pipeline = [
            {"$match": {"product_id": self.id, "status": "approved"}},
            {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}, "count": {"$sum": 1}}}
        ]
        results = list(col.aggregate(pipeline))
        if results:
            avg_rating = round(results[0]["avg_rating"], 1)
            count = results[0]["count"]
        else:
            avg_rating = 0.0
            count = 0
            
        mongo.get_collection('products').update_one(
            {"_id": self.id},
            {"$set": {"rating": avg_rating, "review_count": count, "last_updated": datetime.datetime.now()}}
        )
        self.rating = avg_rating
        self.review_count = count

    @classmethod
    def create(cls, data=None, **kwargs):
        if data is None:
            data = kwargs
        prod_id = str(uuid.uuid4())
        name = data.get('name', '').strip()
        slug = slugify_text(name)
        
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while mongo.get_collection('products').find_one({"slug": slug}):
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        sku = data.get('sku') or generate_sku(data.get('category'), data.get('brand'), name)
        regular_price = float(data.get('regular_price', 0.0))
        offer_price = float(data.get('offer_price', regular_price))
        discount = round(((regular_price - offer_price) / regular_price) * 100, 1) if regular_price > offer_price else 0.0
        
        images = data.get('images', [])
        thumbnail = data.get('thumbnail') or (images[0] if images else "https://placehold.co/600x600/333/fff?text=No+Image")
        
        doc = {
            "_id": prod_id,
            "name": name,
            "slug": slug,
            "sku": sku,
            "barcode": data.get('barcode', f"8901000{uuid.uuid4().int % 1000000:06d}"),
            "category": data.get('category', ''),
            "category_id": data.get('category_id', data.get('category', '')),
            "subcategory": data.get('subcategory', ''),
            "brand": data.get('brand', ''),
            "description": data.get('description', ''),
            "short_description": data.get('short_description', ''),
            "highlights": data.get('highlights', []),
            "specifications": data.get('specifications', {}),
            "variants": data.get('variants', []),
            "regular_price": regular_price,
            "offer_price": offer_price,
            "discount": discount,
            "gst": float(data.get('gst', 18.0)),
            "stock_quantity": int(data.get('stock_quantity', 0)),
            "images": images if images else [thumbnail],
            "thumbnail": thumbnail,
            "tags": data.get('tags', [data.get('brand', '').lower(), data.get('category', '').lower()]),
            "rating": 0.0,
            "review_count": 0,
            "status": data.get('status', 'active'),
            "featured_product": data.get('is_featured', data.get('featured_product', False)),
            "trending_product": data.get('trending_product', False),
            "best_seller": data.get('best_seller', False),
            "new_arrival": data.get('new_arrival', True),
            "date_created": datetime.datetime.now(),
            "last_updated": datetime.datetime.now()
        }
        mongo.get_collection('products').insert_one(doc)
        return cls(doc)

    def update(self, data):
        if 'name' in data and data['name'] != self.name:
            self.name = data['name'].strip()
            self.slug = slugify_text(self.name)
            
        if 'regular_price' in data or 'offer_price' in data:
            self.regular_price = float(data.get('regular_price', self.regular_price))
            self.offer_price = float(data.get('offer_price', self.offer_price))
            if self.regular_price > self.offer_price:
                self.discount = round(((self.regular_price - self.offer_price) / self.regular_price) * 100, 1)
            else:
                self.discount = 0.0
                
        if 'is_featured' in data:
            self.featured_product = bool(data['is_featured'])

        fields = ['sku', 'barcode', 'category', 'category_id', 'subcategory', 'brand', 'description', 
                  'short_description', 'highlights', 'specifications', 'variants', 'gst', 'stock_quantity', 'images', 
                  'thumbnail', 'tags', 'status', 'featured_product', 'trending_product', 
                  'best_seller', 'new_arrival']
        for field in fields:
            if field in data:
                setattr(self, field, data[field])
                
        self.last_updated = datetime.datetime.now()
        
        update_dict = {
            "name": self.name, "slug": self.slug, "sku": self.sku, "barcode": self.barcode,
            "category": self.category, "category_id": self.category_id, "subcategory": self.subcategory, "brand": self.brand,
            "description": self.description, "short_description": self.short_description, "highlights": self.highlights,
            "specifications": self.specifications, "variants": self.variants, "regular_price": self.regular_price,
            "offer_price": self.offer_price, "discount": self.discount, "gst": self.gst,
            "stock_quantity": self.stock_quantity, "images": self.images, "thumbnail": self.thumbnail,
            "tags": self.tags, "status": self.status, "featured_product": self.featured_product,
            "trending_product": self.trending_product, "best_seller": self.best_seller,
            "new_arrival": self.new_arrival, "last_updated": self.last_updated
        }
        mongo.get_collection('products').update_one({"_id": self.id}, {"$set": update_dict})

    def delete(self):
        mongo.get_collection('products').delete_one({"_id": self.id})

    def duplicate(self):
        new_data = dict(self._doc)
        new_data.pop('_id', None)
        new_data['name'] = f"{self.name} (Copy)"
        new_data['sku'] = generate_sku(self.category, self.brand, new_data['name'])
        new_data['status'] = 'disabled'
        return Product.create(new_data)

    def toggle_status(self):
        self.status = 'disabled' if self.status == 'active' else 'active'
        mongo.get_collection('products').update_one({"_id": self.id}, {"$set": {"status": self.status, "last_updated": datetime.datetime.now()}})


class Category:
    """Category model wrapping the MongoDB 'categories' collection."""
    def __init__(self, doc):
        self._doc = doc
        self.id = str(doc.get('_id'))
        self.name = doc.get('name', '')
        self.slug = doc.get('slug', '')
        self.parent_id = doc.get('parent_id')
        self.icon = doc.get('icon', '')
        self.image = doc.get('image', '')
        self.status = doc.get('status', 'active')
        self.display_order = int(doc.get('display_order', 1))
        self.created_at = doc.get('created_at')

    @classmethod
    def get_all_active(cls):
        try:
            cursor = mongo.get_collection('categories').find({"status": "active"}).sort("display_order", 1)
            return [cls(doc) for doc in cursor]
        except Exception as e:
            return []

    @classmethod
    def get_all(cls, parent_id=None, **kwargs):
        try:
            query = {}
            if parent_id is not None:
                query["parent_id"] = parent_id
            cursor = mongo.get_collection('categories').find(query).sort("display_order", 1)
            return [cls(doc) for doc in cursor]
        except Exception as e:
            return []

    @classmethod
    def get_by_id(cls, cat_id):
        try:
            doc = mongo.get_collection('categories').find_one({"_id": str(cat_id)})
            return cls(doc) if doc else None
        except Exception:
            return None

    @classmethod
    def get_by_slug(cls, slug):
        try:
            doc = mongo.get_collection('categories').find_one({"slug": slug})
            return cls(doc) if doc else None
        except Exception:
            return None

    @classmethod
    def get_hierarchy(cls):
        try:
            parents = list(mongo.get_collection('categories').find({"parent_id": None}).sort("display_order", 1))
            result = []
            for p in parents:
                p_obj = cls(p)
                subs = list(mongo.get_collection('categories').find({"parent_id": p['_id']}).sort("display_order", 1))
                p_obj.subcategories = [cls(s) for s in subs]
                result.append(p_obj)
            return result
        except Exception:
            return []

    @classmethod
    def create(cls, name, parent_id=None, icon=None, image=None, display_order=1, **kwargs):
        cat_id = str(uuid.uuid4())
        slug = kwargs.get('slug') or slugify_text(name)
        doc = {
            "_id": cat_id,
            "name": name.strip(),
            "slug": slug,
            "parent_id": parent_id if parent_id else None,
            "icon": icon or 'fa-tag',
            "image": image or f"https://placehold.co/400x300/333/fff?text={slug}",
            "description": kwargs.get('description', ''),
            "status": "active",
            "display_order": int(display_order),
            "created_at": datetime.datetime.now()
        }
        doc.update(kwargs)
        mongo.get_collection('categories').insert_one(doc)
        return cls(doc)

    def update(self, name, parent_id=None, icon=None, image=None, display_order=1, status='active'):
        self.name = name.strip()
        self.slug = slugify_text(self.name)
        self.parent_id = parent_id if parent_id else None
        self.icon = icon or self.icon
        self.image = image or self.image
        self.display_order = int(display_order)
        self.status = status
        mongo.get_collection('categories').update_one(
            {"_id": self.id},
            {"$set": {
                "name": self.name, "slug": self.slug, "parent_id": self.parent_id,
                "icon": self.icon, "image": self.image, "display_order": self.display_order,
                "status": self.status
            }}
        )

    def delete(self):
        # Also delete subcategories if this is a parent
        mongo.get_collection('categories').delete_many({"parent_id": self.id})
        mongo.get_collection('categories').delete_one({"_id": self.id})

    def toggle_status(self):
        self.status = 'disabled' if self.status == 'active' else 'active'
        mongo.get_collection('categories').update_one({"_id": self.id}, {"$set": {"status": self.status}})


class Brand:
    """Brand model wrapping the MongoDB 'brands' collection."""
    def __init__(self, doc):
        self._doc = doc
        self.id = str(doc.get('_id'))
        self.name = doc.get('name', '')
        self.slug = doc.get('slug', '')
        self.logo = doc.get('logo', '')
        self.description = doc.get('description', '')
        self.status = doc.get('status', 'active')
        self.created_at = doc.get('created_at')

    @classmethod
    def get_all_active(cls):
        cursor = mongo.get_collection('brands').find({"status": "active"}).sort("name", 1)
        return [cls(doc) for doc in cursor]

    @classmethod
    def get_all(cls):
        cursor = mongo.get_collection('brands').find().sort("name", 1)
        return [cls(doc) for doc in cursor]

    @classmethod
    def get_by_id(cls, brand_id):
        doc = mongo.get_collection('brands').find_one({"_id": str(brand_id)})
        return cls(doc) if doc else None

    @classmethod
    def get_by_slug(cls, slug):
        doc = mongo.get_collection('brands').find_one({"slug": slug})
        return cls(doc) if doc else None

    @classmethod
    def create(cls, name, logo=None, description="", **kwargs):
        brand_id = str(uuid.uuid4())
        slug = kwargs.get('slug') or slugify_text(name)
        doc = {
            "_id": brand_id,
            "name": name.strip(),
            "slug": slug,
            "logo": logo or f"https://placehold.co/200x80/222/fff?text={name}",
            "description": description.strip(),
            "status": "active",
            "created_at": datetime.datetime.now()
        }
        doc.update(kwargs)
        mongo.get_collection('brands').insert_one(doc)
        return cls(doc)

    def update(self, name, logo=None, description="", status="active"):
        self.name = name.strip()
        self.slug = slugify_text(self.name)
        self.logo = logo or self.logo
        self.description = description.strip()
        self.status = status
        mongo.get_collection('brands').update_one(
            {"_id": self.id},
            {"$set": {
                "name": self.name, "slug": self.slug, "logo": self.logo,
                "description": self.description, "status": self.status
            }}
        )

    def delete(self):
        mongo.get_collection('brands').delete_one({"_id": self.id})
