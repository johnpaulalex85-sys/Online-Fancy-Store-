import datetime
from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from app.main import main_bp
from app.models.product import Product, Category, Brand
from app.models.marketing import Banner, Review
from app.middleware.security import sanitize_input

@main_bp.route('/')
def index():
    """Storefront homepage showcasing banners, flash sales, and featured collections."""
    banners = Banner.get_by_type('homepage')
    categories = Category.get_all(parent_id=None)
    brands = Brand.get_all()
    
    # Fetch Flash Deals (Highest discounted active items)
    flash_deals = Product.get_all(
        filter_dict={"status": "active", "discount": {"$gte": 15.0}},
        sort_by="discount_desc",
        page=1,
        per_page=8
    )['products']
    
    # Fetch Featured Products
    featured_products = Product.get_all(
        filter_dict={"status": "active", "is_featured": True},
        sort_by="popularity",
        page=1,
        per_page=8
    )['products']
    
    # Fetch New Arrivals
    new_arrivals = Product.get_all(
        filter_dict={"status": "active"},
        sort_by="newest",
        page=1,
        per_page=8
    )['products']
    
    return render_template('main/index.html',
                           banners=banners,
                           categories=categories,
                           brands=brands,
                           flash_deals=flash_deals,
                           featured_products=featured_products,
                           new_arrivals=new_arrivals)


@main_bp.route('/catalog')
def catalog():
    """Product catalog with faceted sidebar filtering, searching, and pagination."""
    query = request.args.get('q', '').strip()
    cat_slug = request.args.get('category', '').strip()
    brand_name = request.args.get('brand', '').strip()
    sort_by = request.args.get('sort_by', 'popularity').strip()
    page = request.args.get('page', 1, type=int)
    
    # Price and rating bounds
    try:
        min_price = float(request.args.get('min_price')) if request.args.get('min_price') else None
    except ValueError:
        min_price = None
    try:
        max_price = float(request.args.get('max_price')) if request.args.get('max_price') else None
    except ValueError:
        max_price = None
    try:
        min_rating = int(request.args.get('rating')) if request.args.get('rating') else None
    except ValueError:
        min_rating = None

    # Resolve category if slug provided
    selected_category = None
    cat_id = None
    if cat_slug:
        selected_category = Category.get_by_slug(cat_slug)
        if selected_category:
            cat_id = selected_category.id

    # Execute search or filtered query
    results = Product.search(
        query=query,
        category_id=cat_id,
        brand=brand_name if brand_name else None,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort_by=sort_by,
        page=page,
        per_page=12
    )
    
    all_categories = Category.get_all(parent_id=None)
    all_brands = Brand.get_all()
    
    return render_template('main/catalog.html',
                           products=results['products'],
                           total_count=results['total_count'],
                           total_pages=results['total_pages'],
                           current_page=results['current_page'],
                           query=query,
                           selected_category=selected_category,
                           selected_brand=brand_name,
                           min_price=min_price,
                           max_price=max_price,
                           min_rating=min_rating,
                           sort_by=sort_by,
                           all_categories=all_categories,
                           all_brands=all_brands)


@main_bp.route('/product/<slug>', methods=['GET', 'POST'])
def product_detail(slug):
    """Detailed view of a single product with image gallery, specs, and reviews."""
    product = Product.get_by_slug(slug)
    if not product or product.status != 'active':
        abort(404)

    # Handle customer review submission
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash("Please log in to submit a review.", "warning")
            return redirect(url_for('auth.login', next=request.url))
            
        if getattr(current_user, 'is_admin', False):
            flash("Admins cannot submit customer reviews.", "warning")
            return redirect(url_for('main.product_detail', slug=slug))
            
        rating = request.form.get('rating', 5, type=int)
        title = sanitize_input(request.form.get('title', '').strip())
        comment = sanitize_input(request.form.get('comment', '').strip())
        
        if not title or not comment:
            flash("Review title and comments are required.", "danger")
        else:
            Review.create(
                product_id=product.id,
                user_id=current_user.id,
                user_name=current_user.name,
                rating=rating,
                title=title,
                comment=comment
            )
            flash("Thank you! Your product review has been submitted and published.", "success")
            return redirect(url_for('main.product_detail', slug=slug))

    # Fetch product reviews
    reviews = Review.get_by_product(product.id)
    
    # Fetch related products in same category
    related_results = Product.search(
        category_id=product.category_id,
        sort_by="popularity",
        page=1,
        per_page=5
    )['products']
    related_products = [p for p in related_results if p.id != product.id][:4]
    
    return render_template('main/detail.html',
                           product=product,
                           reviews=reviews,
                           related_products=related_products)
