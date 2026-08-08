from functools import wraps
from flask import abort, flash, redirect, url_for, request, jsonify
from flask_login import current_user

def admin_required(f):
    """Decorator to ensure the current user is an authenticated admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in as an admin to access the dashboard.", "warning")
            return redirect(url_for('auth.admin_login', next=request.url))
        if not getattr(current_user, 'is_admin', False):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def public_user_required(f):
    """Decorator to ensure the current user is a public customer account."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to your account.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        if getattr(current_user, 'is_admin', False):
            flash("Admins cannot perform customer checkout actions.", "warning")
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def ajax_required(f):
    """Decorator to ensure the route was requested via AJAX or JSON."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json):
            return jsonify({"status": "error", "message": "AJAX request required."}), 400
        return f(*args, **kwargs)
    return decorated_function
