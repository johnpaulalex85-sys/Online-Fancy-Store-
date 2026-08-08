from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.cart import cart_bp
from app.cart.services import get_current_cart, get_user_wishlist, toggle_wishlist_item
from app.models.order import Order
from app.models.product import Product
from app.middleware.decorators import ajax_required
from app.utils.helpers import format_currency, calculate_haversine_distance
from app.models.marketing import Setting
from app.utils.email import send_order_confirmation

@cart_bp.route('/')
def view_cart():
    """Shopping cart page displaying items, quantities, coupons, and billing summary."""
    cart = get_current_cart()
    summary = cart.get_summary()
    return render_template('cart/cart.html', cart=cart, summary=summary)


@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    """Add product to shopping cart from catalog or product detail page."""
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity', 1, type=int)
    variant = request.form.get('variant')
    buy_now = request.form.get('buy_now')

    if not product_id:
        flash("Invalid product.", "danger")
        return redirect(request.referrer or url_for('main.index'))

    cart = get_current_cart()
    success, msg = cart.add_item(product_id, quantity=quantity, variant=variant)
    
    if success:
        if buy_now:
            return redirect(url_for('cart.checkout'))
        flash(msg, "success")
    else:
        flash(msg, "danger")
        
    return redirect(request.referrer or url_for('cart.view_cart'))


@cart_bp.route('/update', methods=['POST'])
@ajax_required
def update_cart():
    """AJAX endpoint to update item quantity in cart and recalculate totals."""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    variant = data.get('variant')

    cart = get_current_cart()
    success, msg = cart.update_quantity(product_id, quantity, variant)
    
    if not success:
        return jsonify({"status": "error", "message": msg}), 400
        
    summary = cart.get_summary()
    return jsonify({
        "status": "success",
        "message": "Cart updated",
        "summary": {
            "subtotal": format_currency(summary['subtotal']),
            "shipping_charge": format_currency(summary['shipping_charge']) if summary['shipping_charge'] > 0 else "FREE",
            "discount_amount": format_currency(summary['discount_amount']),
            "tax_amount": format_currency(summary['tax_amount']),
            "grand_total": format_currency(summary['grand_total']),
            "item_count": summary['item_count'],
            "coupon_code": cart.coupon_code
        }
    })


@cart_bp.route('/remove/<product_id>', methods=['GET', 'POST'])
def remove_from_cart(product_id):
    """Remove item from shopping cart."""
    variant = request.args.get('variant') or request.form.get('variant')
    cart = get_current_cart()
    cart.remove_item(product_id, variant)
    flash("Item removed from cart.", "info")
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/coupon/apply', methods=['POST'])
@ajax_required
def apply_coupon():
    """AJAX endpoint to validate and apply promotional discount coupon."""
    data = request.get_json()
    code = data.get('coupon_code', '').strip()
    
    cart = get_current_cart()
    success, msg = cart.apply_coupon(code)
    
    if not success:
        return jsonify({"status": "error", "message": msg}), 400
        
    summary = cart.get_summary()
    return jsonify({
        "status": "success",
        "message": msg,
        "summary": {
            "subtotal": format_currency(summary['subtotal']),
            "shipping_charge": format_currency(summary['shipping_charge']) if summary['shipping_charge'] > 0 else "FREE",
            "discount_amount": format_currency(summary['discount_amount']),
            "tax_amount": format_currency(summary['tax_amount']),
            "grand_total": format_currency(summary['grand_total']),
            "coupon_code": cart.coupon_code
        }
    })


@cart_bp.route('/coupon/remove', methods=['GET', 'POST'])
def remove_coupon():
    """Remove promotional coupon from cart."""
    cart = get_current_cart()
    cart.remove_coupon()
    flash("Coupon removed.", "info")
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/wishlist')
def wishlist_view():
    """Customer wishlist page."""
    products = get_user_wishlist()
    return render_template('cart/wishlist.html', products=products)


@cart_bp.route('/api/wishlist/toggle', methods=['POST'])
@ajax_required
def wishlist_toggle_api():
    """AJAX endpoint triggered when heart icon is clicked on product cards."""
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


@cart_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Multi-step checkout with simulated UPI, COD, and Credit Card payment gateways."""
    if getattr(current_user, 'is_admin', False):
        flash("Admins cannot place customer orders.", "warning")
        return redirect(url_for('admin.dashboard'))

    cart = get_current_cart()
    summary = cart.get_summary()
    
    if not summary['items']:
        flash("Your shopping cart is empty.", "warning")
        return redirect(url_for('main.catalog'))

    if request.method == 'POST':
        # Get selected or new shipping address
        addr_index = request.form.get('address_index', type=int)
        if addr_index is not None and 0 <= addr_index < len(current_user.addresses):
            shipping_address = current_user.addresses[addr_index]
        else:
            # Check if one-time address filled
            shipping_address = {
                "full_name": request.form.get('full_name', current_user.name),
                "phone": request.form.get('phone', current_user.phone),
                "address_line1": request.form.get('address_line1', ''),
                "address_line2": request.form.get('address_line2', ''),
                "city": request.form.get('city', ''),
                "state": request.form.get('state', ''),
                "postal_code": request.form.get('postal_code', '')
            }
            if not shipping_address['address_line1'] or not shipping_address['postal_code']:
                flash("Please select a valid delivery address.", "danger")
                return render_template('cart/checkout.html', cart=cart, summary=summary)

        # ================= 50 KM Booking Radius Validation =================
        try:
            store_lat = float(Setting.get('store_latitude', 28.6139))
            store_lng = float(Setting.get('store_longitude', 77.2090))
            max_dist = float(Setting.get('max_booking_distance_km', 50.0))
        except (ValueError, TypeError):
            store_lat, store_lng, max_dist = 28.6139, 77.2090, 50.0
            
        delivery_lat = request.form.get('delivery_latitude', type=float)
        delivery_lng = request.form.get('delivery_longitude', type=float)
        
        if delivery_lat is None and isinstance(shipping_address, dict):
            delivery_lat = shipping_address.get('latitude')
        if delivery_lng is None and isinstance(shipping_address, dict):
            delivery_lng = shipping_address.get('longitude')
            
        if delivery_lat is not None and delivery_lng is not None:
            dist_km = calculate_haversine_distance(store_lat, store_lng, delivery_lat, delivery_lng)
            if dist_km > max_dist:
                store_addr_label = Setting.get('store_address', 'Fancy Store HQ')
                flash(f"🚫 Booking Rejected: Your delivery address is {dist_km:.1f} km away from our store ({store_addr_label}). Booking is strictly applicable only within the {max_dist} km area of our store location.", "danger")
                return redirect(url_for('cart.checkout'))
            if isinstance(shipping_address, dict):
                shipping_address['latitude'] = delivery_lat
                shipping_address['longitude'] = delivery_lng
                shipping_address['distance_km'] = round(dist_km, 2)
        else:
            flash("📍 Delivery location coordinates required! Please set or verify your delivery location pin on the map below to confirm you are within our 50 km booking area.", "warning")
            return redirect(url_for('cart.checkout'))

        payment_method = request.form.get('payment_method', 'COD') # COD, UPI, CARD
        payment_status = "Paid" if payment_method in ['UPI', 'CARD'] else "Pending"

        # Validate stock availability before final placement
        for item in summary['items']:
            if not item['product'].in_stock or item['product'].stock_quantity < item['quantity']:
                flash(f"Sorry, {item['product'].name} does not have enough stock available.", "danger")
                return redirect(url_for('cart.view_cart'))

        # Create Order
        order, msg = Order.create_from_cart(
            cart=cart,
            user=current_user,
            shipping_address=shipping_address,
            payment_method=payment_method,
            payment_status=payment_status
        )

        if order:
            # Trigger confirmation email in the background
            if current_user.email:
                send_order_confirmation(order, current_user.email)
                
            flash(f"Order #{order.order_number} confirmed! Thank you for shopping with Fancy Store.", "success")
            return redirect(url_for('cart.checkout_success', order_number=order.order_number))
        else:
            flash(f"Failed to place order: {msg}", "danger")

    return render_template('cart/checkout.html', cart=cart, summary=summary)


@cart_bp.route('/checkout/success/<order_number>')
@login_required
def checkout_success(order_number):
    """Order placement confirmation and thank you screen."""
    order = Order.get_by_order_number(order_number)
    if not order or order.user_id != current_user.id:
        abort(404)
    return render_template('cart/success.html', order=order)
