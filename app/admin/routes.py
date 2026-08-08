import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, abort, jsonify, current_app
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.admin.analytics import get_dashboard_kpis
from app.admin.forms import ProductForm, CategoryForm, BrandForm, CouponForm, BannerForm, OrderStatusForm, StoreSettingsForm, AdminPasswordResetForm
from app.models.product import Product, Category, Brand
from app.models.order import Order
from app.models.marketing import Coupon, Banner, Review, Setting
from app.models.user import User, Admin
from app.middleware.security import sanitize_input
from app.db import mongo
from app.utils.email import send_order_cancellation

@admin_bp.before_request
def require_admin_privileges():
    """Security check: verify current authenticated user has Admin RBAC permissions."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.admin_login', next=request.url))
    if not getattr(current_user, 'is_admin', False):
        abort(403)
        
    # Restrict delivery personnel from accessing non-order routes
    if getattr(current_user, 'role', '') == 'delivery':
        allowed = ['admin.orders_list', 'admin.order_update_status', 'auth.logout', 'admin.dashboard']
        if request.endpoint not in allowed and not request.endpoint.startswith('static'):
            flash('Access Denied. You only have permission to view and update orders.', 'danger')
            return redirect(url_for('admin.orders_list'))


@admin_bp.route('/')
@admin_bp.route('/dashboard')
def dashboard():
    """Redirect to orders list since dashboard is removed."""
    return redirect(url_for('admin.orders_list'))


# ================= Product Management =================
@admin_bp.route('/products')
def products_list():
    """Catalog inventory management list with filtering and status controls."""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    results = Product.search(query=query, page=page, per_page=15)
    return render_template('admin/products_list.html',
                           products=results['products'],
                           total_count=results['total_count'],
                           total_pages=results['total_pages'],
                           current_page=results['current_page'],
                           query=query)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
def product_add():
    """Create new product item in catalog."""
    form = ProductForm()
    # Populate categories
    categories = Category.get_all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        # Handle file uploads
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'products')
        os.makedirs(upload_dir, exist_ok=True)
        
        thumbnail_val = form.thumbnail.data.strip() if form.thumbnail.data else ""
        if form.thumbnail_upload.data:
            file = form.thumbnail_upload.data
            filename = secure_filename(file.filename)
            if filename:
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file.save(os.path.join(upload_dir, unique_filename))
                thumbnail_val = f"/static/uploads/products/{unique_filename}"
                
        # Parse comma separated strings
        images_list = [img.strip() for img in form.images.data.replace(',', '\n').split('\n') if img.strip()]
        if form.gallery_upload.data:
            for file in form.gallery_upload.data:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    if filename:
                        unique_filename = f"{uuid.uuid4().hex}_{filename}"
                        file.save(os.path.join(upload_dir, unique_filename))
                        images_list.append(f"/static/uploads/products/{unique_filename}")
                        
        variants_list = [v.strip() for v in form.variants.data.split(',') if v.strip()]
        
        prod_id = Product.create(
            name=sanitize_input(form.name.data),
            brand=sanitize_input(form.brand.data),
            category_id=form.category_id.data,
            sku=sanitize_input((form.sku.data or "").upper()),
            regular_price=form.regular_price.data,
            discount=form.discount.data,
            stock_quantity=form.stock_quantity.data,
            short_description=sanitize_input(form.short_description.data),
            description=sanitize_input(form.description.data),
            thumbnail=thumbnail_val,
            images=images_list,
            variants=variants_list,
            is_featured=form.is_featured.data,
            status=form.status.data
        )
        flash(f"Product '{form.name.data}' added to catalog successfully!", "success")
        return redirect(url_for('admin.products_list'))
        
    return render_template('admin/product_form.html', form=form, title="Add New Product")


@admin_bp.route('/products/edit/<product_id>', methods=['GET', 'POST'])
def product_edit(product_id):
    """Modify existing catalog product."""
    prod = Product.get_by_id(product_id)
    if not prod:
        abort(404)
        
    form = ProductForm(obj=prod)
    categories = Category.get_all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if request.method == 'GET':
        form.images.data = '\n'.join(prod.images) if prod.images else ''
        form.variants.data = ', '.join(prod.variants) if prod.variants else ''
        
    if form.validate_on_submit():
        # Handle file uploads
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'products')
        os.makedirs(upload_dir, exist_ok=True)
        
        thumbnail_val = form.thumbnail.data.strip() if form.thumbnail.data else prod.thumbnail
        if form.thumbnail_upload.data:
            file = form.thumbnail_upload.data
            filename = secure_filename(file.filename)
            if filename:
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file.save(os.path.join(upload_dir, unique_filename))
                thumbnail_val = f"/static/uploads/products/{unique_filename}"
                
        images_list = [img.strip() for img in form.images.data.replace(',', '\n').split('\n') if img.strip()]
        if form.gallery_upload.data:
            for file in form.gallery_upload.data:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    if filename:
                        unique_filename = f"{uuid.uuid4().hex}_{filename}"
                        file.save(os.path.join(upload_dir, unique_filename))
                        images_list.append(f"/static/uploads/products/{unique_filename}")
                        
        variants_list = [v.strip() for v in form.variants.data.split(',') if v.strip()]
        
        update_data = {
            "name": sanitize_input(form.name.data),
            "brand": sanitize_input(form.brand.data),
            "category_id": form.category_id.data,
            "sku": sanitize_input((form.sku.data or "").upper()),
            "regular_price": form.regular_price.data,
            "discount": form.discount.data,
            "stock_quantity": form.stock_quantity.data,
            "short_description": sanitize_input(form.short_description.data),
            "description": sanitize_input(form.description.data),
            "thumbnail": thumbnail_val,
            "images": images_list,
            "variants": variants_list,
            "is_featured": form.is_featured.data,
            "status": form.status.data
        }
        
        prod.update(update_data)
        flash(f"Product '{prod.name}' updated successfully!", "success")
        return redirect(url_for('admin.products_list'))
        
    return render_template('admin/product_form.html', form=form, title=f"Edit Product: {prod.name}", product=prod)


@admin_bp.route('/products/delete/<product_id>', methods=['POST'])
def product_delete(product_id):
    """Archive / delete product from active catalog."""
    prod = Product.get_by_id(product_id)
    if prod:
        prod.delete()
        flash(f"Product '{prod.name}' deleted.", "info")
    return redirect(url_for('admin.products_list'))


@admin_bp.route('/products/status/<product_id>', methods=['POST'])
def product_update_status(product_id):
    """Quickly update product status from admin catalog list."""
    prod = Product.get_by_id(product_id)
    if prod:
        new_status = request.form.get('status', 'active').strip()
        prod.update({"status": new_status})
        flash(f"Status for '{prod.name}' changed to '{new_status}'.", "success")
    return redirect(request.referrer or url_for('admin.products_list'))



# ================= Order Management =================
@admin_bp.route('/orders')
def orders_list():
    """All customer orders management with shipment filters."""
    status_filter = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    
    filter_dict = {}
    if status_filter:
        filter_dict["order_status"] = status_filter
        
    if current_user.role == 'delivery':
        filter_dict["delivery_boy_id"] = current_user.id
        
    results = Order.get_all(filter_dict=filter_dict, page=page, per_page=15)
    
    delivery_boys = Admin.get_by_role('delivery')
    
    return render_template('admin/orders_list.html',
                           orders=results['orders'],
                           total_count=results['total_count'],
                           total_pages=results['total_pages'],
                           current_page=results['current_page'],
                           status_filter=status_filter,
                           delivery_boys=delivery_boys)


@admin_bp.route('/orders/<order_number>/status', methods=['POST'])
def order_update_status(order_number):
    """Admin endpoint to update order shipment status and tracking ID."""
    order = Order.get_by_order_number(order_number)
    if not order:
        abort(404)
        
    if request.method == 'POST':
        status = request.form.get('order_status')
        delivery_boy_id = request.form.get('delivery_boy_id')
        note = f"Status updated by Admin to {status}"
        
        if status:
            order.update_status(status, note=note)
            
            # If status is updated to Cancelled, notify customer
            if status == "Cancelled":
                user = User.get_by_id(order.user_id)
                if user and user.email:
                    send_order_cancellation(order, user.email)
            
        if delivery_boy_id:
            db_admin = Admin.get_by_id(delivery_boy_id)
            if db_admin:
                order.assign_delivery_boy(delivery_boy_id, db_admin.name)
        elif 'delivery_boy_id' in request.form and not delivery_boy_id:
            # If the admin selected "No Delivery Assigned", remove assignment
            order.assign_delivery_boy(None, None)
            
        flash(f"Order #{order_number} successfully updated.", "success")
        
    return redirect(request.referrer or url_for('admin.orders_list'))

@admin_bp.route('/orders/export/pdf')
def export_orders_pdf():
    """Export the currently filtered list of orders as a PDF document."""
    from app.orders.pdf_service import generate_orders_list_pdf
    
    status_filter = request.args.get('status', '').strip()
    filter_dict = {}
    if status_filter:
        filter_dict["order_status"] = status_filter
        
    if current_user.role == 'delivery':
        filter_dict["delivery_boy_id"] = current_user.id
        
    # Get all matching orders (large limit to export all)
    results = Order.get_all(filter_dict=filter_dict, page=1, per_page=10000)
    
    return generate_orders_list_pdf(results['orders'])


@admin_bp.route('/orders/delete/<order_id>', methods=['POST'])
def order_delete(order_id):
    """Admin endpoint to delete / remove customer order."""
    order = Order.get_by_id(order_id)
    if order:
        order.delete()
        flash(f"Order #{order.order_number} has been deleted.", "info")
    return redirect(request.referrer or url_for('admin.orders_list'))



# ================= Categories & Brands =================
@admin_bp.route('/categories', methods=['GET', 'POST'])
def categories_list():
    """Manage catalog categories hierarchy."""
    form = CategoryForm()
    categories = Category.get_all()
    form.parent_id.choices = [('', 'None (Top Level Category)')] + [(c.id, c.name) for c in categories if not c.parent_id]
    
    if form.validate_on_submit():
        Category.create(
            name=sanitize_input(form.name.data),
            parent_id=form.parent_id.data if form.parent_id.data else None
        )
        flash("Category added successfully!", "success")
        return redirect(url_for('admin.categories_list'))
        
    return render_template('admin/categories_list.html', categories=categories, form=form)


@admin_bp.route('/categories/delete/<category_id>', methods=['POST'])
def category_delete(category_id):
    """Delete category from catalog."""
    cat = Category.get_by_id(category_id)
    if cat:
        cat.delete()
        flash(f"Category '{cat.name}' deleted.", "info")
    return redirect(url_for('admin.categories_list'))


@admin_bp.route('/brands', methods=['GET', 'POST'])
def brands_list():
    """Manage partner brand logos."""
    form = BrandForm()
    brands = Brand.get_all()
    
    if form.validate_on_submit():
        Brand.create(
            name=sanitize_input(form.name.data),
            logo=form.logo.data.strip(),
            description=sanitize_input(form.description.data)
        )
        flash("Brand partner added!", "success")
        return redirect(url_for('admin.brands_list'))
        
    return render_template('admin/brands_list.html', brands=brands, form=form)


# ================= Marketing: Coupons, Banners, Reviews =================
@admin_bp.route('/coupons', methods=['GET', 'POST'])
def coupons_list():
    """Manage discount coupon codes."""
    form = CouponForm()
    coupons = Coupon.get_all()
    
    if form.validate_on_submit():
        Coupon.create(
            code=form.code.data.strip().upper(),
            description=sanitize_input(form.description.data),
            discount_type=form.discount_type.data,
            discount_value=form.discount_value.data,
            min_order_value=form.min_order_value.data,
            max_uses=form.max_uses.data,
            status=form.status.data
        )
        flash(f"Coupon '{form.code.data}' created successfully!", "success")
        return redirect(url_for('admin.coupons_list'))
        
    return render_template('admin/coupons_list.html', coupons=coupons, form=form)


@admin_bp.route('/banners', methods=['GET', 'POST'])
def banners_list():
    """Manage promotional homepage slider banners."""
    form = BannerForm()
    banners = Banner.get_all()
    
    if form.validate_on_submit():
        Banner.create(
            title=sanitize_input(form.title.data),
            subtitle=sanitize_input(form.subtitle.data),
            image_url=form.image_url.data.strip(),
            link_url=form.link_url.data.strip(),
            banner_type=form.banner_type.data,
            sort_order=form.sort_order.data,
            status=form.status.data
        )
        flash("Promotional banner added!", "success")
        return redirect(url_for('admin.banners_list'))
        
    return render_template('admin/banners_list.html', banners=banners, form=form)


@admin_bp.route('/reviews', methods=['GET', 'POST'])
def reviews_list():
    """Moderate customer product reviews."""
    col = mongo.get_collection('reviews')
    reviews_docs = list(col.find().sort("created_at", -1))
    
    if request.method == 'POST':
        rev_id = request.form.get('review_id')
        action = request.form.get('action') # approve, reject, delete
        if rev_id and action:
            from bson import ObjectId
            if action == 'delete':
                col.delete_one({"_id": ObjectId(rev_id) if ObjectId.is_valid(rev_id) else rev_id})
                flash("Review deleted.", "info")
            elif action in ['approved', 'rejected']:
                col.update_one({"_id": ObjectId(rev_id) if ObjectId.is_valid(rev_id) else rev_id}, {"$set": {"status": action}})
                flash(f"Review status changed to {action}.", "success")
        return redirect(url_for('admin.reviews_list'))
        
    return render_template('admin/reviews_list.html', reviews=reviews_docs)


@admin_bp.route('/users')
def users_list():
    """Manage registered customer accounts."""
    users = User.get_all(page=1, per_page=50)['users']
    return render_template('admin/users_list.html', users=users)


# ================= Store Configuration & Location Setup =================
@admin_bp.route('/location-settings', methods=['GET', 'POST'])
def location_settings():
    """Configure store coordinates and enforce the 50 km booking radius."""
    if request.method == 'POST':
        store_name = sanitize_input(request.form.get('store_name', 'Fancy Store HQ'))
        store_address = sanitize_input(request.form.get('store_address', 'Connaught Place, New Delhi, DL, India'))
        
        try:
            store_lat = float(request.form.get('store_latitude', 28.6139))
            store_lng = float(request.form.get('store_longitude', 77.2090))
        except (ValueError, TypeError):
            store_lat = 28.6139
            store_lng = 77.2090
            
        try:
            max_dist = float(request.form.get('max_booking_distance_km', 50.0))
            if max_dist <= 0:
                max_dist = 50.0
        except (ValueError, TypeError):
            max_dist = 50.0
            
        Setting.set('store_name', store_name)
        Setting.set('store_address', store_address)
        Setting.set('store_latitude', store_lat)
        Setting.set('store_longitude', store_lng)
        Setting.set('max_booking_distance_km', max_dist)
        
        flash(f"Store location updated! All new order bookings will be validated against a {max_dist} km radius from ({store_lat}, {store_lng}).", "success")
        return redirect(url_for('admin.location_settings'))
        
    all_settings = Setting.get_all()
    return render_template('admin/location_settings.html', settings=all_settings)


@admin_bp.route('/api/location/update', methods=['POST'])
def api_location_update():
    """AJAX endpoint to quickly update store coordinates from dashboard Location Setup Bar."""
    data = request.get_json() or request.form
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    try:
        lat = float(data.get('latitude', 28.6139))
        lng = float(data.get('longitude', 77.2090))
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid latitude/longitude numbers"}), 400
        
    try:
        max_rad = float(data.get('max_booking_distance_km', data.get('radius', Setting.get('max_booking_distance_km', 50.0))))
        if max_rad <= 0:
            max_rad = 50.0
    except (ValueError, TypeError):
        max_rad = 50.0

    address = sanitize_input(data.get('address', Setting.get('store_address', 'New Delhi, India')))
    name = sanitize_input(data.get('name', Setting.get('store_name', 'Fancy Store HQ')))
    
    Setting.set('store_name', name)
    Setting.set('store_address', address)
    Setting.set('store_latitude', lat)
    Setting.set('store_longitude', lng)
    Setting.set('max_booking_distance_km', max_rad)
    
    return jsonify({
        "status": "success",
        "message": f"Store GPS coordinates and {max_rad} km booking radius updated successfully!",
        "latitude": lat,
        "longitude": lng,
        "address": address,
        "max_radius_km": max_rad
    })


# ================= Global Settings & Security =================
@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    """Global configuration panel and Admin security settings."""
    settings_form = StoreSettingsForm()
    password_form = AdminPasswordResetForm()
    
    if request.method == 'POST':
        # Handle Store Settings Submission
        if 'submit_settings' in request.form and settings_form.validate_on_submit():
            Setting.set('store_name', sanitize_input(settings_form.store_name.data))
            Setting.set('contact_email', sanitize_input(settings_form.contact_email.data))
            Setting.set('contact_phone', sanitize_input(settings_form.contact_phone.data))
            if settings_form.delivery_charge_per_km.data is not None:
                Setting.set('delivery_charge_per_km', float(settings_form.delivery_charge_per_km.data))
            flash('Store configuration updated successfully!', 'success')
            return redirect(url_for('admin.settings'))
            
        # Handle Password Reset Submission
        if 'submit_password' in request.form and password_form.validate_on_submit():
            if current_user.check_password(password_form.current_password.data):
                if password_form.new_password.data == password_form.confirm_password.data:
                    current_user.update_password(password_form.new_password.data)
                    flash('Admin password updated successfully! Please use the new password on next login.', 'success')
                else:
                    flash('New passwords do not match.', 'danger')
            else:
                flash('Current password is incorrect.', 'danger')
            return redirect(url_for('admin.settings'))
            
    # GET method: Pre-fill Store Settings
    if request.method == 'GET':
        settings_form.store_name.data = Setting.get('store_name', 'Fancy Store')
        settings_form.contact_email.data = Setting.get('contact_email', 'support@fancystore.com')
        settings_form.contact_phone.data = Setting.get('contact_phone', '+91 98765 43210')
        settings_form.delivery_charge_per_km.data = float(Setting.get('delivery_charge_per_km', 10.0))
        
    return render_template('admin/settings.html', settings_form=settings_form, password_form=password_form)

# ================= Subadmins / Delivery Boys =================
@admin_bp.route('/subadmins', methods=['GET', 'POST'])
def subadmins_list():
    """List and create delivery personnel."""
    from app.admin.forms import SubAdminForm
    form = SubAdminForm()
    from app.models.user import Admin
    subadmins = Admin.get_by_role('delivery')
    
    if form.validate_on_submit():
        name = sanitize_input(form.name.data)
        email = sanitize_input(form.email.data)
        password = form.password.data
        role = form.role.data
        
        # Ensure email is unique
        existing = Admin.get_by_email(email)
        if existing:
            flash(f"A user with email {email} already exists.", "danger")
        else:
            Admin.create_subadmin(name, email, password, role)
            flash(f"Subadmin '{name}' created successfully!", "success")
            return redirect(url_for('admin.subadmins_list'))
            
    return render_template('admin/subadmins_list.html', subadmins=subadmins, form=form)

@admin_bp.route('/subadmins/delete/<admin_id>', methods=['POST'])
def subadmin_delete(admin_id):
    """Delete a subadmin."""
    from app.models.user import Admin
    subadmin = Admin.get_by_id(admin_id)
    if subadmin and subadmin.role == 'delivery':
        if subadmin.delete():
            flash(f"Subadmin '{subadmin.name}' has been deleted successfully.", "success")
        else:
            flash(f"Error deleting subadmin '{subadmin.name}'.", "danger")
    else:
        flash("Subadmin not found or invalid operation.", "danger")
    return redirect(url_for('admin.subadmins_list'))
