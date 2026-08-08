import datetime
import uuid
import logging
from werkzeug.security import generate_password_hash
from app.db import mongo
from app.utils.helpers import slugify_text, generate_sku

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_database(app=None, production_mode=True):
    """Seed MongoDB collections with production-ready or demo data."""
    if app is not None:
        mongo.init_app(app)
        
    mode_str = "PRODUCTION" if production_mode else "DEMO/TEST"
    logger.info(f"Starting {mode_str} database initialization for Fancy Store...")
    
    # 1. Clear existing collections and drop unwanted legacy tables from other projects
    valid_collections = [
        'admins', 'users', 'products', 'categories', 'brands', 'orders',
        'cart', 'wishlist', 'reviews', 'coupons', 'banners', 'notifications', 'settings'
    ]
    for col in mongo.db.list_collection_names():
        if col not in valid_collections:
            logger.info(f"Dropping unwanted legacy collection: {col}")
            mongo.db.drop_collection(col)

    for col in valid_collections:
        mongo.get_collection(col).delete_many({})
    logger.info("Cleared existing store collections and removed unwanted database tables.")
    
    # 2. Seed Settings
    settings_data = [
        {"key": "store_name", "value": "Fancy Store", "updated_at": datetime.datetime.now()},
        {"key": "contact_email", "value": "support@fancystore.com", "updated_at": datetime.datetime.now()},
        {"key": "contact_phone", "value": "+91 98765 43210", "updated_at": datetime.datetime.now()},
        {"key": "currency", "value": "₹", "updated_at": datetime.datetime.now()},
        {"key": "gst_rate", "value": 18.0, "updated_at": datetime.datetime.now()},
        {"key": "free_shipping_threshold", "value": 999.0, "updated_at": datetime.datetime.now()},
        {"key": "standard_shipping_charge", "value": 49.0, "updated_at": datetime.datetime.now()},
        {"key": "maintenance_mode", "value": False, "updated_at": datetime.datetime.now()},
        {"key": "store_address", "value": "Connaught Place, New Delhi, DL, India", "updated_at": datetime.datetime.now()},
        {"key": "store_latitude", "value": 28.6139, "updated_at": datetime.datetime.now()},
        {"key": "store_longitude", "value": 77.2090, "updated_at": datetime.datetime.now()},
        {"key": "max_booking_distance_km", "value": 50.0, "updated_at": datetime.datetime.now()}
    ]
    mongo.get_collection('settings').insert_many(settings_data)
    
    # 3. Seed Admins
    admin_docs = [
        {
            "_id": str(uuid.uuid4()),
            "name": "Super Admin",
            "email": "admin@fancystore.com",
            "password": generate_password_hash("admin123"),
            "role": "super_admin",
            "status": "active",
            "created_at": datetime.datetime.now(),
            "last_login": None
        },
        {
            "_id": str(uuid.uuid4()),
            "name": "Fancy Administrator",
            "email": "admin@fancystore.in",
            "password": generate_password_hash("admin123"),
            "role": "super_admin",
            "status": "active",
            "created_at": datetime.datetime.now(),
            "last_login": None
        }
    ]
    mongo.get_collection('admins').insert_many(admin_docs)
    
    # 4. Seed Users (Only in demo/test mode)
    user_id = None
    user_doc = None
    if not production_mode:
        user_docs = [
            {
                "_id": str(uuid.uuid4()),
                "name": "John Doe",
                "email": "john.doe@example.com",
                "password": generate_password_hash("password123"),
                "phone": "+91 98111 22333",
                "status": "active",
                "email_verified": True,
                "addresses": [
                    {
                        "address_id": str(uuid.uuid4()),
                        "full_name": "John Doe",
                        "phone": "+91 98111 22333",
                        "pincode": "560001",
                        "address_line1": "123, Tech Park Residency, M.G. Road",
                        "address_line2": "Near Metro Station",
                        "city": "Bangalore",
                        "state": "Karnataka",
                        "address_type": "Home",
                        "is_default": True
                    }
                ],
                "created_at": datetime.datetime.now()
            },
            {
                "_id": str(uuid.uuid4()),
                "name": "John Doe",
                "email": "john@example.com",
                "password": generate_password_hash("password123"),
                "phone": "+91 98111 22333",
                "status": "active",
                "email_verified": True,
                "addresses": [],
                "created_at": datetime.datetime.now()
            }
        ]
        mongo.get_collection('users').insert_many(user_docs)
        user_id = user_docs[0]["_id"]
        user_doc = user_docs[0]
        logger.info("Seeded demo user accounts.")
    else:
        logger.info("Production mode: Skipped dummy customer account creation.")
    
    # 5. Seed Brands
    brands_raw = [
        {"name": "Apple", "description": "Innovative technology and consumer electronics."},
        {"name": "Samsung", "description": "Global leader in digital appliances and smartphones."},
        {"name": "Nike", "description": "Inspiring athletes with sportswear and footwear."},
        {"name": "Sony", "description": "Cutting-edge audio and visual entertainment equipment."},
        {"name": "Dyson", "description": "Advanced vacuum cleaners and home appliances."},
        {"name": "Adidas", "description": "High-performance sports shoes and apparel."},
        {"name": "Levi's", "description": "Iconic denim and casual fashion wear."},
        {"name": "Asus", "description": "High-performance gaming laptops and motherboards."}
    ]
    brand_docs = []
    brand_map = {}
    for b in brands_raw:
        slug = slugify_text(b["name"])
        doc = {
            "_id": str(uuid.uuid4()),
            "name": b["name"],
            "slug": slug,
            "logo": f"https://placehold.co/200x80/222/fff?text={b['name']}",
            "description": b["description"],
            "status": "active",
            "created_at": datetime.datetime.now()
        }
        brand_docs.append(doc)
        brand_map[b["name"]] = doc["_id"]
    mongo.get_collection('brands').insert_many(brand_docs)
    
    # 6. Seed Categories & Subcategories
    categories_raw = [
        {
            "name": "Electronics",
            "icon": "fa-laptop",
            "subs": ["Smartphones", "Laptops", "Audio & Headphones", "Tablets"]
        },
        {
            "name": "Fashion",
            "icon": "fa-tshirt",
            "subs": ["Men's Clothing", "Women's Clothing", "Accessories"]
        },
        {
            "name": "Footwear",
            "icon": "fa-shoe-prints",
            "subs": ["Sports Shoes", "Casual Shoes", "Formal Shoes"]
        },
        {
            "name": "Home & Kitchen",
            "icon": "fa-blender",
            "subs": ["Cookware", "Home Decor", "Lighting"]
        },
        {
            "name": "Appliances",
            "icon": "fa-tv",
            "subs": ["Televisions", "Vacuum Cleaners", "Air Purifiers"]
        },
        {
            "name": "Beauty",
            "icon": "fa-sparkles",
            "subs": ["Skincare", "Fragrances", "Haircare"]
        }
    ]
    
    cat_docs = []
    cat_map = {}
    order_idx = 1
    for cat in categories_raw:
        cat_id = str(uuid.uuid4())
        cat_slug = slugify_text(cat["name"])
        cat_doc = {
            "_id": cat_id,
            "name": cat["name"],
            "slug": cat_slug,
            "parent_id": None,
            "icon": cat["icon"],
            "image": f"https://placehold.co/400x300/333/fff?text={cat['name']}",
            "status": "active",
            "display_order": order_idx,
            "created_at": datetime.datetime.now()
        }
        cat_docs.append(cat_doc)
        cat_map[cat["name"]] = cat_id
        order_idx += 1
        
        # Subcategories
        sub_order = 1
        for sub in cat["subs"]:
            sub_id = str(uuid.uuid4())
            sub_slug = slugify_text(sub)
            sub_doc = {
                "_id": sub_id,
                "name": sub,
                "slug": sub_slug,
                "parent_id": cat_id,
                "icon": None,
                "image": f"https://placehold.co/300x200/444/fff?text={sub}",
                "status": "active",
                "display_order": sub_order,
                "created_at": datetime.datetime.now()
            }
            cat_docs.append(sub_doc)
            cat_map[sub] = sub_id
            sub_order += 1
            
    mongo.get_collection('categories').insert_many(cat_docs)
    
    # 7. Seed Products
    products_raw = [
        {
            "name": "Apple iPhone 15 Pro Max (256GB) - Natural Titanium",
            "brand": "Apple",
            "category": "Electronics",
            "subcategory": "Smartphones",
            "regular_price": 159900.0,
            "offer_price": 148900.0,
            "stock": 45,
            "rating": 4.8,
            "review_count": 342,
            "featured": True, "trending": True, "bestseller": True, "new": True,
            "highlights": ["A17 Pro chip with 6-core GPU", "48MP Main camera system", "Titanium design with Ceramic Shield", "Up to 29 hours video playback"],
            "specs": {"Display": "6.7-inch Super Retina XDR", "Processor": "A17 Pro", "Storage": "256GB", "Battery": "4422 mAh", "OS": "iOS 17"},
            "description": "The iPhone 15 Pro Max is forged in titanium and features the groundbreaking A17 Pro chip, a customizable Action button, and a versatile 5x Telephoto camera system."
        },
        {
            "name": "MacBook Pro M3 Max 16-inch (36GB RAM, 1TB SSD)",
            "brand": "Apple",
            "category": "Electronics",
            "subcategory": "Laptops",
            "regular_price": 319900.0,
            "offer_price": 299900.0,
            "stock": 15,
            "rating": 4.9,
            "review_count": 128,
            "featured": True, "trending": True, "bestseller": True, "new": False,
            "highlights": ["M3 Max chip with 14-core CPU and 30-core GPU", "16.2-inch Liquid Retina XDR display", "Up to 22 hours battery life", "MagSafe 3 charging port"],
            "specs": {"Display": "16.2-inch Liquid Retina XDR", "Processor": "Apple M3 Max", "RAM": "36GB Unified", "Storage": "1TB SSD", "Weight": "2.14 kg"},
            "description": "Mind-blowing performance and battery life with the Apple M3 Max chip. Designed for extreme workflows, 3D rendering, and AI development."
        },
        {
            "name": "Samsung Galaxy S24 Ultra 5G (12GB RAM, 512GB Storage)",
            "brand": "Samsung",
            "category": "Electronics",
            "subcategory": "Smartphones",
            "regular_price": 139999.0,
            "offer_price": 129999.0,
            "stock": 60,
            "rating": 4.7,
            "review_count": 289,
            "featured": True, "trending": True, "bestseller": False, "new": True,
            "highlights": ["Galaxy AI built-in with Live Translate", "200MP Quad Tele System", "Snapdragon 8 Gen 3 for Galaxy", "Integrated S Pen"],
            "specs": {"Display": "6.8-inch Dynamic AMOLED 2X", "Processor": "Snapdragon 8 Gen 3", "Camera": "200MP + 50MP + 12MP + 10MP", "Battery": "5000 mAh"},
            "description": "Welcome to the era of mobile AI. With Galaxy S24 Ultra in your hands, you can unleash whole new levels of creativity, productivity and possibility."
        },
        {
            "name": "Sony WH-1000XM5 Wireless Noise Canceling Headphones",
            "brand": "Sony",
            "category": "Electronics",
            "subcategory": "Audio & Headphones",
            "regular_price": 34990.0,
            "offer_price": 28990.0,
            "stock": 85,
            "rating": 4.8,
            "review_count": 512,
            "featured": True, "trending": False, "bestseller": True, "new": False,
            "highlights": ["Industry-leading Noise Cancellation with two processors", "Up to 30-hour battery life with quick charging", "Ultra-comfortable lightweight leather fit", "Crystal clear hands-free calling"],
            "specs": {"Type": "Over-Ear Wireless", "Battery Life": "30 Hours", "Noise Canceling": "Yes, Active V1 processor", "Weight": "250g", "Connectivity": "Bluetooth 5.2"},
            "description": "The WH-1000XM5 headphones rewrite the rules for distraction-free listening and call clarity, powered by two processors and 8 microphones."
        },
        {
            "name": "Nike Air Jordan 1 Retro High OG - Lost & Found",
            "brand": "Nike",
            "category": "Footwear",
            "subcategory": "Sports Shoes",
            "regular_price": 16995.0,
            "offer_price": 14995.0,
            "stock": 30,
            "rating": 4.9,
            "review_count": 420,
            "featured": True, "trending": True, "bestseller": True, "new": False,
            "highlights": ["Classic Chicago colorway with vintage aesthetic", "Premium leather upper with cracked leather accents", "Air-Sole unit in the heel for cushioning", "Rubber outsole for durable traction"],
            "specs": {"Upper Material": "Full-grain Leather", "Sole Material": "Rubber", "Closure": "Lace-up", "Style": "High-Top Basketball"},
            "description": "Bringing back the look of the original 1985 release, this Air Jordan 1 features vintage-inspired details like a weathered box and pre-yellowed midsole."
        },
        {
            "name": "Adidas Ultraboost Light Running Shoes",
            "brand": "Adidas",
            "category": "Footwear",
            "subcategory": "Sports Shoes",
            "regular_price": 18999.0,
            "offer_price": 13999.0,
            "stock": 50,
            "rating": 4.6,
            "review_count": 180,
            "featured": False, "trending": True, "bestseller": False, "new": True,
            "highlights": ["Lightest Ultraboost ever made with Light BOOST foam", "adidas PRIMEKNIT+ forged upper", "Continental Rubber outsole for epic grip", "Made in part with Parley Ocean Plastic"],
            "specs": {"Midsole": "Light BOOST", "Drop": "10 mm", "Weight": "293g", "Surface": "Road / Track"},
            "description": "Experience epic energy with the new Ultraboost Light, our lightest Ultraboost ever. The magic lies in the Light BOOST midsole, an all-new adidas BOOST generation."
        },
        {
            "name": "Dyson V15 Detect Cord-Free Vacuum Cleaner",
            "brand": "Dyson",
            "category": "Appliances",
            "subcategory": "Vacuum Cleaners",
            "regular_price": 65900.0,
            "offer_price": 58900.0,
            "stock": 25,
            "rating": 4.8,
            "review_count": 156,
            "featured": True, "trending": False, "bestseller": True, "new": False,
            "highlights": ["Laser reveals microscopic dust on hard floors", "Piezo sensor automatically adapts suction power", "LCD screen shows proof of deep clean in real time", "Up to 60 minutes of fade-free suction"],
            "specs": {"Suction Power": "240 AW", "Bin Volume": "0.77 L", "Run Time": "60 Mins", "Filtration": "Whole-machine HEPA"},
            "description": "Dyson's most powerful, intelligent cordless vacuum. Engineered for whole-home deep cleans with advanced illumination technology."
        },
        {
            "name": "Levi's 501 Original Fit Men's Jeans - Vintage Blue",
            "brand": "Levi's",
            "category": "Fashion",
            "subcategory": "Men's Clothing",
            "regular_price": 4999.0,
            "offer_price": 3499.0,
            "stock": 120,
            "rating": 4.5,
            "review_count": 640,
            "featured": False, "trending": False, "bestseller": True, "new": False,
            "highlights": ["The original button-fly blue jeans since 1873", "100% premium non-stretch cotton denim", "Regular fit through the thigh with a straight leg", "Classic 5-pocket styling"],
            "specs": {"Material": "100% Cotton", "Fit": "Regular Straight", "Closure": "Button Fly", "Wash": "Medium Vintage Blue"},
            "description": "Close your eyes. Think jeans. Now open. You were thinking of the 501s, right? They're literally the blueprint for every pair of jeans in existence."
        },
        {
            "name": "Asus ROG Zephyrus G16 Gaming Laptop (RTX 4080)",
            "brand": "Asus",
            "category": "Electronics",
            "subcategory": "Laptops",
            "regular_price": 249990.0,
            "offer_price": 229990.0,
            "stock": 18,
            "rating": 4.8,
            "review_count": 94,
            "featured": True, "trending": True, "bestseller": False, "new": True,
            "highlights": ["Intel Core Ultra 9 processor with AI NPU", "NVIDIA GeForce RTX 4080 12GB GPU", "16-inch 2.5K 240Hz ROG Nebula OLED display", "Ultra-slim 1.49cm aluminum chassis"],
            "specs": {"Display": "16-inch OLED 240Hz", "Processor": "Intel Core Ultra 9 185H", "GPU": "RTX 4080 12GB", "RAM": "32GB LPDDR5X", "Storage": "2TB PCIe 4.0 SSD"},
            "description": "Precision craftsmanship meets flagship gaming performance. The ROG Zephyrus G16 features a jaw-dropping OLED panel in an ultra-sleek CNC-milled aluminum chassis."
        },
        {
            "name": "Apple iPad Air M2 11-inch (128GB, Wi-Fi) - Space Grey",
            "brand": "Apple",
            "category": "Electronics",
            "subcategory": "Tablets",
            "regular_price": 59900.0,
            "offer_price": 56900.0,
            "stock": 70,
            "rating": 4.7,
            "review_count": 210,
            "featured": False, "trending": True, "bestseller": True, "new": True,
            "highlights": ["Supercharged by Apple M2 chip", "11-inch Liquid Retina display with True Tone", "Landscape 12MP Ultra Wide front camera with Center Stage", "Supports Apple Pencil Pro and Magic Keyboard"],
            "specs": {"Display": "11-inch Liquid Retina", "Chip": "Apple M2", "Storage": "128GB", "Camera": "12MP Back + 12MP Front", "Connectivity": "Wi-Fi 6E"},
            "description": "Now with the blazing-fast M2 chip, the redesigned iPad Air is more versatile than ever. Featuring a stunning display and all-day battery life."
        },
        {
            "name": "Samsung 65-inch 4K Ultra HD Neo QLED Smart TV",
            "brand": "Samsung",
            "category": "Appliances",
            "subcategory": "Televisions",
            "regular_price": 189900.0,
            "offer_price": 154900.0,
            "stock": 12,
            "rating": 4.8,
            "review_count": 88,
            "featured": True, "trending": False, "bestseller": False, "new": False,
            "highlights": ["Quantum Matrix Technology with Mini LEDs", "Neural Quantum Processor 4K with AI Upscaling", "Dolby Atmos with top-channel speakers", "120Hz refresh rate for seamless gaming"],
            "specs": {"Screen Size": "65 Inches", "Resolution": "4K Ultra HD (3840 x 2160)", "Refresh Rate": "120Hz", "Sound Output": "60W 4.2.2Ch", "OS": "Tizen"},
            "description": "Experience our finest 4K picture yet with Neo QLED. Quantum Mini LEDs deliver hyper-focused luminance and extreme contrast in every scene."
        },
        {
            "name": "Nike Air Zoom Pegasus 40 Running Shoes - Triple Black",
            "brand": "Nike",
            "category": "Footwear",
            "subcategory": "Sports Shoes",
            "regular_price": 11895.0,
            "offer_price": 9995.0,
            "stock": 90,
            "rating": 4.6,
            "review_count": 530,
            "featured": False, "trending": False, "bestseller": True, "new": False,
            "highlights": ["Dual Zoom Air units for responsive bounce", "Nike React foam for lightweight, durable cushioning", "Highly breathable engineered mesh upper", "Optimized midfoot strap for secure lockdown"],
            "specs": {"Weight": "288g", "Drop": "10mm", "Cushioning": "Medium-High", "Surface": "Road"},
            "description": "A springy ride for every run, the Peg's familiar, just-for-you feel returns to help you accomplish your goals with upgraded arch comfort."
        }
    ]
    
    product_docs = []
    product_ids = []
    for p in products_raw:
        prod_id = str(uuid.uuid4())
        product_ids.append((prod_id, p["name"]))
        slug = slugify_text(p["name"])
        sku = generate_sku(p["category"], p["brand"], p["name"])
        discount = round(((p["regular_price"] - p["offer_price"]) / p["regular_price"]) * 100, 1) if p["regular_price"] > p["offer_price"] else 0.0
        
        # Build images array with rich placehold URLs
        bg_color = "111" if p["brand"] == "Apple" else ("004488" if p["brand"] == "Samsung" else "222222")
        images = [
            f"https://placehold.co/800x800/{bg_color}/ffffff?text={slugify_text(p['brand'])}+1",
            f"https://placehold.co/800x800/{bg_color}/ffffff?text={slugify_text(p['brand'])}+2",
            f"https://placehold.co/800x800/{bg_color}/ffffff?text={slugify_text(p['brand'])}+3"
        ]
        
        doc = {
            "_id": prod_id,
            "name": p["name"],
            "slug": slug,
            "sku": sku,
            "barcode": f"8901000{uuid.uuid4().int % 1000000:06d}",
            "category": p["category"],
            "subcategory": p["subcategory"],
            "brand": p["brand"],
            "description": p["description"],
            "highlights": p["highlights"],
            "specifications": p["specs"],
            "regular_price": float(p["regular_price"]),
            "offer_price": float(p["offer_price"]),
            "discount": discount,
            "gst": 18.0,
            "stock_quantity": int(p["stock"]),
            "images": images,
            "thumbnail": images[0],
            "tags": [p["brand"].lower(), p["category"].lower(), p["subcategory"].lower(), "premium", "modern"],
            "rating": float(p["rating"]),
            "review_count": int(p["review_count"]),
            "status": "active",
            "featured_product": p.get("featured", False),
            "trending_product": p.get("trending", False),
            "best_seller": p.get("bestseller", False),
            "new_arrival": p.get("new", False),
            "date_created": datetime.datetime.now() - datetime.timedelta(days=int(uuid.uuid4().int % 30)),
            "last_updated": datetime.datetime.now()
        }
        product_docs.append(doc)
    mongo.get_collection('products').insert_many(product_docs)
    logger.info(f"Seeded {len(product_docs)} demo products.")
    
    # 8. Seed Banners
    banner_docs = [
        {
            "_id": str(uuid.uuid4()),
            "title": "Titanium iPhone 15 Pro Max",
            "subtitle": "So strong. So light. So Pro.",
            "image_url": "https://placehold.co/1400x500/0b0f19/61dafb?text=Apple+iPhone+15+Pro+Max+-+Titanium+Series",
            "link_url": "/product/apple-iphone-15-pro-max-256gb-natural-titanium",
            "banner_type": "homepage",
            "position": 1,
            "status": "active",
            "created_at": datetime.datetime.now()
        },
        {
            "_id": str(uuid.uuid4()),
            "title": "MacBook Pro M3 Series",
            "subtitle": "Mind-blowing. Head-turning.",
            "image_url": "https://placehold.co/1400x500/121212/ffffff?text=MacBook+Pro+M3+Max+-+Extreme+Performance",
            "link_url": "/category/electronics",
            "banner_type": "homepage",
            "position": 2,
            "status": "active",
            "created_at": datetime.datetime.now()
        },
        {
            "_id": str(uuid.uuid4()),
            "title": "Nike Air Jordan 1 Retro",
            "subtitle": "Step into greatness with timeless footwear.",
            "image_url": "https://placehold.co/1400x500/8b0000/ffffff?text=Nike+Air+Jordan+1+-+Lost+%26+Found",
            "link_url": "/category/footwear",
            "banner_type": "homepage",
            "position": 3,
            "status": "active",
            "created_at": datetime.datetime.now()
        },
        {
            "_id": str(uuid.uuid4()),
            "title": "Dyson V15 Detect Festival Offer",
            "subtitle": "Flat ₹7,000 OFF on cordless vacuums.",
            "image_url": "https://placehold.co/1200x300/3e2723/ffecb3?text=Festival+Sale+-+Flat+₹7000+OFF+on+Dyson+Appliances",
            "link_url": "/brand/dyson",
            "banner_type": "festival",
            "position": 1,
            "status": "active",
            "created_at": datetime.datetime.now()
        }
    ]
    mongo.get_collection('banners').insert_many(banner_docs)
    
    # 9. Seed Coupons
    coupon_docs = [
        {
            "_id": str(uuid.uuid4()),
            "code": "WELCOME10",
            "description": "Get 10% OFF on your first purchase above ₹1,000",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "min_purchase": 1000.0,
            "max_discount": 2000.0,
            "usage_limit": 500,
            "used_count": 42,
            "expiry_date": datetime.datetime.now() + datetime.timedelta(days=90),
            "status": "active",
            "created_at": datetime.datetime.now()
        },
        {
            "_id": str(uuid.uuid4()),
            "code": "FANCY20",
            "description": "Flat 20% OFF on fashion and footwear above ₹2,500",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "min_purchase": 2500.0,
            "max_discount": 5000.0,
            "usage_limit": 200,
            "used_count": 88,
            "expiry_date": datetime.datetime.now() + datetime.timedelta(days=30),
            "status": "active",
            "created_at": datetime.datetime.now()
        },
        {
            "_id": str(uuid.uuid4()),
            "code": "FLAT500",
            "description": "Flat ₹500 OFF on any order above ₹5,000",
            "discount_type": "fixed",
            "discount_value": 500.0,
            "min_purchase": 5000.0,
            "max_discount": 500.0,
            "usage_limit": 1000,
            "used_count": 150,
            "expiry_date": datetime.datetime.now() + datetime.timedelta(days=60),
            "status": "active",
            "created_at": datetime.datetime.now()
        }
    ]
    mongo.get_collection('coupons').insert_many(coupon_docs)
    
    # 10. Seed Reviews, Orders, Cart, Wishlist, Notifications (Only in demo/test mode)
    if not production_mode and user_id:
        review_docs = []
        for pid, pname in product_ids[:6]:
            review_docs.append({
                "_id": str(uuid.uuid4()),
                "product_id": pid,
                "user_id": user_id,
                "user_name": "John Doe",
                "rating": 5,
                "title": "Absolutely stunning product!",
                "comment": f"I purchased the {pname} last week and it exceeded all my expectations. The build quality and premium finish are unmatched. Highly recommended from Fancy Store!",
                "images": [],
                "status": "approved",
                "created_at": datetime.datetime.now() - datetime.timedelta(days=5)
            })
            review_docs.append({
                "_id": str(uuid.uuid4()),
                "product_id": pid,
                "user_id": str(uuid.uuid4()),
                "user_name": "Priya Sharma",
                "rating": 5,
                "title": "Best value for money!",
                "comment": "Super fast delivery by Fancy Store. Genuine product with sealed packaging. Will definitely buy again.",
                "images": [],
                "status": "approved",
                "created_at": datetime.datetime.now() - datetime.timedelta(days=12)
            })
        mongo.get_collection('reviews').insert_many(review_docs)
        
        # 11. Seed Orders
        sample_order = {
            "_id": str(uuid.uuid4()),
            "order_number": "ORD-20260715-9982",
            "user_id": user_id,
            "user_name": "John Doe",
            "user_email": "john@example.com",
            "items": [
                {
                    "product_id": product_ids[0][0],
                    "name": product_ids[0][1],
                    "price": 148900.0,
                    "quantity": 1,
                    "thumbnail": product_docs[0]["thumbnail"]
                }
            ],
            "shipping_address": user_doc["addresses"][0],
            "billing_summary": {
                "subtotal": 148900.0,
                "shipping_charge": 0.0,
                "discount_amount": 0.0,
                "tax_amount": round(148900.0 * 0.18, 2),
                "grand_total": 148900.0
            },
            "subtotal": 148900.0,
            "shipping_charge": 0.0,
            "discount_amount": 0.0,
            "tax_amount": round(148900.0 * 0.18, 2),
            "grand_total": 148900.0,
            "payment_method": "UPI",
            "payment_status": "Paid",
            "order_status": "Delivered",
            "tracking_history": [
                {"status": "Placed", "timestamp": datetime.datetime.now() - datetime.timedelta(days=10), "note": "Order placed successfully."},
                {"status": "Processing", "timestamp": datetime.datetime.now() - datetime.timedelta(days=9), "note": "Seller packed your item."},
                {"status": "Shipped", "timestamp": datetime.datetime.now() - datetime.timedelta(days=8), "note": "Shipped via BlueDart Courier."},
                {"status": "Delivered", "timestamp": datetime.datetime.now() - datetime.timedelta(days=6), "note": "Delivered to John Doe."}
            ],
            "created_at": datetime.datetime.now() - datetime.timedelta(days=10)
        }
        mongo.get_collection('orders').insert_one(sample_order)
        
        # 12. Seed Cart & Wishlist
        mongo.get_collection('cart').insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": None,
            "items": [
                {
                    "product_id": product_ids[3][0], # Sony headphones
                    "quantity": 1,
                    "added_at": datetime.datetime.now()
                }
            ],
            "coupon_code": None,
            "updated_at": datetime.datetime.now()
        })
        
        mongo.get_collection('wishlist').insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "product_ids": [product_ids[1][0], product_ids[4][0]], # MacBook and Air Jordan
            "updated_at": datetime.datetime.now()
        })
        
        # 13. Seed Notifications
        mongo.get_collection('notifications').insert_many([
            {
                "_id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": "Welcome to Fancy Store!",
                "message": "Use coupon code WELCOME10 on your first checkout to get 10% OFF.",
                "type": "promotion",
                "is_read": False,
                "created_at": datetime.datetime.now()
            },
            {
                "_id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": "Order Delivered!",
                "message": "Your order ORD-20260715-9982 has been delivered. Tap to leave a review.",
                "type": "order",
                "is_read": True,
                "created_at": datetime.datetime.now() - datetime.timedelta(days=6)
            }
        ])
        logger.info("Seeded demo reviews, orders, carts, and notifications.")
    else:
        logger.info("Production mode: Skipped seeding dummy customer reviews, orders, carts, wishlists, and notifications.")
        
    logger.info("Database initialization completed successfully! Store is ready.")

if __name__ == '__main__':
    import sys
    from app import create_app
    app = create_app('development')
    is_prod = '--demo' not in sys.argv
    with app.app_context():
        seed_database(app, production_mode=is_prod)
