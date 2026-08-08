from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.orders import orders_bp
from app.orders.pdf_service import generate_invoice_pdf
from app.models.order import Order
from app.utils.email import send_order_cancellation

@orders_bp.route('/')
@login_required
def history():
    """Customer order history dashboard listing past purchases and active deliveries."""
    if getattr(current_user, 'is_admin', False):
        return redirect(url_for('admin.orders_list'))

    orders = Order.get_user_orders(current_user.id)
    return render_template('orders/history.html', orders=orders)


@orders_bp.route('/<order_number>')
@login_required
def order_detail(order_number):
    """Detailed view of a specific order including itemized list and address."""
    order = Order.get_by_order_number(order_number)
    if not order:
        abort(404)
        
    if not getattr(current_user, 'is_admin', False) and order.user_id != current_user.id:
        abort(403)

    return render_template('orders/detail.html', order=order)


@orders_bp.route('/track/<order_number>')
@login_required
def track_order(order_number):
    """Live order shipment tracking with visual progress timeline."""
    order = Order.get_by_order_number(order_number)
    if not order:
        abort(404)
        
    if not getattr(current_user, 'is_admin', False) and order.user_id != current_user.id:
        abort(403)

    return render_template('orders/track.html', order=order)


@orders_bp.route('/invoice/<order_number>')
@login_required
def download_invoice(order_number):
    """Download official GST Tax Invoice as PDF or printable document."""
    order = Order.get_by_order_number(order_number)
    if not order:
        abort(404)
        
    if not getattr(current_user, 'is_admin', False) and order.user_id != current_user.id:
        abort(403)

    return generate_invoice_pdf(order)


@orders_bp.route('/cancel/<order_number>', methods=['POST'])
@login_required
def cancel_order(order_number):
    """Allow customer to cancel order before shipment."""
    order = Order.get_by_order_number(order_number)
    if not order or order.user_id != current_user.id:
        abort(403)

    success, msg = order.cancel(reason="Cancelled by customer via User Dashboard")
    if success:
        # Trigger cancellation email
        if current_user.email:
            send_order_cancellation(order, current_user.email)
            
        flash(f"Order #{order_number} has been cancelled successfully. Any prepaid amount will be refunded in 3-5 business days.", "success")
    else:
        flash(f"Cannot cancel order: {msg}", "danger")

    return redirect(url_for('orders.order_detail', order_number=order_number))


@orders_bp.route('/return/<order_number>', methods=['POST'])
@login_required
def return_order(order_number):
    """Allow customer to request return/replacement for delivered orders."""
    order = Order.get_by_order_number(order_number)
    if not order or order.user_id != current_user.id:
        abort(403)

    reason = request.form.get('reason', 'Customer requested return').strip()
    success, msg = order.request_return(reason=reason)
    if success:
        flash(f"Return request for Order #{order_number} initiated. Our pickup executive will reach out within 24 hours.", "success")
    else:
        flash(f"Cannot return order: {msg}", "danger")

    return redirect(url_for('orders.order_detail', order_number=order_number))
