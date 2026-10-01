import datetime
from flask import render_template, redirect, url_for, flash, request, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.auth.forms import (
    LoginForm, AdminLoginForm, RegisterForm, ProfileUpdateForm,
    AddressForm, PasswordChangeForm, ForgotPasswordForm,
    VerifyOTPForm, ResetPasswordForm
)
from app.models.user import User, Admin
from app.middleware.security import sanitize_input
from app.utils.email import send_otp_email

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Customer authentication route."""
    if current_user.is_authenticated:
        if getattr(current_user, 'is_admin', False):
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        raw_email = form.email.data.strip().lower()
        user = User.get_by_email(raw_email)
        
        if user and user.check_password(form.password.data):
            if user.status != 'active':
                flash("Your account has been suspended or deactivated. Please contact support.", "danger")
                return redirect(url_for('auth.login'))
                
            login_user(user, remember=form.remember_me.data)
            user.update_last_login()
            
            flash(f"Welcome back, {user.name.split()[0]}!", "success")
            next_page = request.args.get('next') or request.form.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('admin.dashboard') if user.is_admin else url_for('main.index')
            return redirect(next_page)
        else:
            admin = Admin.get_by_email(raw_email)
            if admin and admin.check_password(form.password.data):
                if admin.status != 'active':
                    flash("Admin access denied. Account inactive.", "danger")
                    return redirect(url_for('auth.login'))
                login_user(admin, remember=form.remember_me.data)
                admin.update_last_login()
                flash(f"Welcome back to Admin Portal, {admin.name}!", "success")
                next_page = request.args.get('next') or request.form.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('admin.dashboard')
                return redirect(next_page)
            flash("Invalid email address or password.", "danger")

    return render_template('auth/login.html', form=form, is_admin_login=False)


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Administrative portal authentication route."""
    if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
        return redirect(url_for('admin.dashboard'))

    form = AdminLoginForm()
    if form.validate_on_submit():
        raw_email = form.email.data.strip().lower()
        admin = Admin.get_by_email(raw_email)
        
        if admin and admin.check_password(form.password.data):
            if admin.status != 'active':
                flash("Admin access denied. Account inactive.", "danger")
                return redirect(url_for('auth.admin_login'))
                
            logout_user()
            login_user(admin, remember=form.remember_me.data)
            admin.update_last_login()
            
            flash(f"Admin Portal authenticated. Welcome, {admin.name} ({admin.role}).", "success")
            next_page = request.args.get('next') or request.form.get('next')
            if not next_page or not next_page.startswith('/admin'):
                next_page = url_for('admin.dashboard')
            return redirect(next_page)
        else:
            flash("Invalid administrative credentials.", "danger")

    return render_template('auth/login.html', form=form, is_admin_login=True)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Customer registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        email = sanitize_input(form.email.data.strip().lower())
        
        # Check if user already exists
        if User.get_by_email(email) or Admin.get_by_email(email):
            flash("An account with this email address already exists.", "warning")
            return render_template('auth/register.html', form=form)
            
        name = sanitize_input(form.name.data.strip())
        phone = sanitize_input(form.phone.data.strip())
        
        user = User.create(name=name, email=email, password=form.password.data, phone=phone)
        login_user(user)
        user.update_last_login()
        
        flash("Your Fancy Store account has been created successfully! Welcome aboard.", "success")
        return redirect(url_for('main.index'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Sign out route for both users and admins."""
    name = getattr(current_user, 'name', 'User').split()[0]
    logout_user()
    session.clear()
    flash(f"Goodbye, {name}! You have been logged out securely.", "info")
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management, address book, and security settings."""
    profile_form = ProfileUpdateForm(obj=current_user)
    password_form = PasswordChangeForm()
    address_form = AddressForm()

    # Handle Profile Info update
    if 'submit_profile' in request.form and profile_form.validate_on_submit():
        current_user.update_profile(
            name=sanitize_input(profile_form.name.data),
            phone=sanitize_input(profile_form.phone.data),
            profile_pic=sanitize_input(profile_form.profile_pic.data or '')
        )
        flash("Your personal profile details have been updated.", "success")
        return redirect(url_for('auth.profile'))

    # Handle Password Change
    if 'submit_password' in request.form and password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash("Your current password was incorrect.", "danger")
        else:
            current_user.update_password(password_form.new_password.data)
            flash("Your account password has been updated securely.", "success")
            return redirect(url_for('auth.profile'))

    # Handle New Address Addition
    if 'submit_address' in request.form and address_form.validate_on_submit():
        new_addr = {
            "label": address_form.label.data,
            "full_name": sanitize_input(address_form.full_name.data),
            "phone": sanitize_input(address_form.phone.data),
            "address_line1": sanitize_input(address_form.address_line1.data),
            "address_line2": sanitize_input(address_form.address_line2.data or ''),
            "city": sanitize_input(address_form.city.data),
            "state": sanitize_input(address_form.state.data),
            "postal_code": sanitize_input(address_form.postal_code.data),
            "is_default": address_form.is_default.data
        }
        current_user.add_address(new_addr)
        flash("New address added to your address book.", "success")
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', 
                           profile_form=profile_form, 
                           password_form=password_form, 
                           address_form=address_form)


@auth_bp.route('/profile/address/delete/<int:index>', methods=['POST'])
@login_required
def delete_address(index):
    """Delete an address from the user's address book."""
    if getattr(current_user, 'is_admin', False):
        abort(403)
    if current_user.remove_address(index):
        flash("Address removed successfully.", "info")
    else:
        flash("Could not remove address.", "danger")
    return redirect(url_for('auth.profile'))


@auth_bp.route('/profile/address/default/<int:index>', methods=['POST'])
@login_required
def set_default_address(index):
    """Set an address as the default shipping destination."""
    if getattr(current_user, 'is_admin', False):
        abort(403)
    if current_user.set_default_address(index):
        flash("Default shipping address updated.", "success")
    else:
        flash("Could not update default address.", "danger")
    return redirect(url_for('auth.profile'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = sanitize_input(form.email.data.strip().lower())
        
        # Check both User and Admin collections
        account = User.get_by_email(email)
        is_admin = False
        if not account:
            account = Admin.get_by_email(email)
            is_admin = True
            
        if account:
            otp = account.generate_reset_otp()
            send_otp_email(account.email, otp)
            
            # Store email in session to know who is resetting
            session['reset_email'] = account.email
            session['reset_is_admin'] = is_admin
            
            flash("An OTP has been sent to your email address.", "success")
            return redirect(url_for('auth.verify_otp'))
        else:
            # Prevent email enumeration by showing success message anyway
            flash("If an account exists with this email, an OTP has been sent.", "success")
            return redirect(url_for('auth.login'))
            
    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    email = session.get('reset_email')
    if not email:
        flash("Session expired or invalid request. Please start over.", "danger")
        return redirect(url_for('auth.forgot_password'))
        
    form = VerifyOTPForm()
    if form.validate_on_submit():
        is_admin = session.get('reset_is_admin', False)
        account = Admin.get_by_email(email) if is_admin else User.get_by_email(email)
        
        if account and account.verify_reset_otp(form.otp.data):
            session['reset_authorized'] = True
            flash("OTP verified successfully. You may now reset your password.", "success")
            return redirect(url_for('auth.reset_password'))
        else:
            flash("Invalid or expired OTP. Please try again.", "danger")
            
    return render_template('auth/verify_otp.html', form=form)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    email = session.get('reset_email')
    authorized = session.get('reset_authorized')
    
    if not email or not authorized:
        flash("Unauthorized request. Please verify OTP first.", "danger")
        return redirect(url_for('auth.forgot_password'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        is_admin = session.get('reset_is_admin', False)
        account = Admin.get_by_email(email) if is_admin else User.get_by_email(email)
        
        if account:
            account.update_password(form.new_password.data)
            account.clear_reset_otp()
            
            # Clear session variables
            session.pop('reset_email', None)
            session.pop('reset_is_admin', None)
            session.pop('reset_authorized', None)
            
            flash("Your password has been successfully reset. You can now log in.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("Account not found. Please try again.", "danger")
            return redirect(url_for('auth.forgot_password'))
            
    return render_template('auth/reset_password.html', form=form)
