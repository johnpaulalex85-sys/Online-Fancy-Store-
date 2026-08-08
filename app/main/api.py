from flask import request, jsonify, url_for
from app.main import main_bp
from app.models.product import Product
from app.middleware.decorators import ajax_required
from app.utils.helpers import format_currency

@main_bp.route('/api/search/suggestions', methods=['GET'])
def search_suggestions():
    """AJAX endpoint for live search autocomplete in navbar."""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({"status": "error", "message": "Query too short", "suggestions": []})

    results = Product.search(query=query, page=1, per_page=6)['products']
    
    suggestions = []
    for prod in results:
        suggestions.append({
            "id": prod.id,
            "name": prod.name,
            "brand": prod.brand,
            "slug": prod.slug,
            "thumbnail": prod.thumbnail,
            "price_formatted": format_currency(prod.price_after_discount),
            "url": url_for('main.product_detail', slug=prod.slug)
        })

    return jsonify({
        "status": "success",
        "count": len(suggestions),
        "suggestions": suggestions
    })


@main_bp.route('/api/product/<product_id>/quickview', methods=['GET'])
def product_quickview(product_id):
    """AJAX endpoint to fetch product data for Quick View modal."""
    prod = Product.get_by_id(product_id)
    if not prod:
        return jsonify({"status": "error", "message": "Product not found"}), 404

    return jsonify({
        "status": "success",
        "product": {
            "id": prod.id,
            "name": prod.name,
            "brand": prod.brand,
            "slug": prod.slug,
            "sku": prod.sku,
            "short_description": prod.short_description,
            "thumbnail": prod.thumbnail,
            "images": prod.images,
            "regular_price_formatted": format_currency(prod.regular_price),
            "price_formatted": format_currency(prod.price_after_discount),
            "discount": prod.discount,
            "in_stock": prod.in_stock,
            "stock_quantity": prod.stock_quantity,
            "rating_avg": prod.rating_avg,
            "rating_count": prod.rating_count,
            "variants": prod.variants,
            "url": url_for('main.product_detail', slug=prod.slug)
        }
    })


@main_bp.route('/api/wishlist/toggle', methods=['POST'])
@ajax_required
def root_wishlist_toggle():
    """Root AJAX endpoint for toggling wishlist items."""
    from app.cart.services import toggle_wishlist_item
    data = request.get_json()
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({"status": "error", "message": "Product ID required"}), 400
        
    in_wishlist, count, msg = toggle_wishlist_item(product_id)
    return jsonify({
        "status": "success",
        "in_wishlist": in_wishlist,
        "wishlist_count": count,
        "message": msg
    })

@main_bp.route('/api/categories/<category_slug>/brands', methods=['GET'])
def category_brands(category_slug):
    """Fetch all distinct brands for products in a specific category."""
    if not category_slug or category_slug == 'all':
        from app.models.product import Brand
        brands = Brand.get_all_active()
        return jsonify({
            "status": "success",
            "brands": [{"name": b.name, "slug": b.slug} for b in brands]
        })
        
    from app.models.product import Category
    cat = Category.get_by_slug(category_slug)
    cat_id = cat.id if cat else category_slug
    cat_name = cat.name if cat else category_slug

    from app.db import mongo
    filter_dict = {
        "status": {"$in": ["active", "coming_soon"]},
        "$or": [
            {"category": cat_name}, 
            {"subcategory": cat_name}, 
            {"category_id": cat_id},
            {"category": category_slug}, 
            {"subcategory": category_slug}, 
            {"category_id": category_slug}
        ]
    }
    distinct_brands = mongo.get_collection('products').distinct("brand", filter_dict)
    
    valid_brands = [b for b in distinct_brands if b]
    valid_brands.sort()
    
    return jsonify({
        "status": "success",
        "brands": [{"name": b, "slug": b} for b in valid_brands]
    })
