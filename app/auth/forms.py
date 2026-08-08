from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, Regexp

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Enter a valid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    remember_me = BooleanField('Remember me on this device')
    submit = SubmitField('Sign In')


class AdminLoginForm(FlaskForm):
    email = StringField('Admin Email', validators=[
        DataRequired(message="Admin email is required."),
        Email()
    ])
    password = PasswordField('Security Password', validators=[
        DataRequired(message="Password is required.")
    ])
    remember_me = BooleanField('Remember session')
    submit = SubmitField('Authenticate to Portal')


class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required."),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Enter a valid email address.")
    ])
    phone = StringField('Phone Number', validators=[
        DataRequired(message="Phone number is required."),
        Regexp(r'^\+?[0-9\s\-]{10,15}$', message="Enter a valid phone number (10-15 digits).")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=6, message="Password must be at least 6 characters.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match exactly.")
    ])
    terms = BooleanField('I agree to the Terms of Service & Privacy Policy', validators=[
        DataRequired(message="You must accept the terms to register.")
    ])
    submit = SubmitField('Create Account')


class ProfileUpdateForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required."),
        Length(min=2, max=100)
    ])
    phone = StringField('Phone Number', validators=[
        DataRequired(message="Phone number is required."),
        Regexp(r'^\+?[0-9\s\-]{10,15}$', message="Enter a valid phone number.")
    ])
    profile_pic = StringField('Profile Picture URL', validators=[Optional()])
    submit = SubmitField('Save Changes')


class AddressForm(FlaskForm):
    label = SelectField('Address Type', choices=[('Home', 'Home (All day delivery)'), ('Work', 'Work (10 AM - 6 PM)'), ('Other', 'Other')], validators=[DataRequired()])
    full_name = StringField('Recipient Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Contact Phone', validators=[DataRequired(), Regexp(r'^\+?[0-9\s\-]{10,15}$', message="Valid phone required.")])
    address_line1 = StringField('House No. / Building / Street', validators=[DataRequired(), Length(min=5, max=150)])
    address_line2 = StringField('Area / Locality / Landmark', validators=[Optional(), Length(max=150)])
    city = StringField('City / District', validators=[DataRequired(), Length(min=2, max=50)])
    state = StringField('State', validators=[DataRequired(), Length(min=2, max=50)])
    postal_code = StringField('PIN Code / ZIP', validators=[DataRequired(), Regexp(r'^[0-9]{6}$', message="Enter a 6-digit PIN code.")])
    is_default = BooleanField('Make this my default shipping address')
    submit = SubmitField('Save Address')


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message="New password must be at least 6 characters.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message="New passwords do not match.")
    ])
    submit = SubmitField('Update Password')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Enter a valid email address.")
    ])
    submit = SubmitField('Send OTP')


class VerifyOTPForm(FlaskForm):
    otp = StringField('Enter 6-digit OTP', validators=[
        DataRequired(message="OTP is required."),
        Regexp(r'^[0-9]{6}$', message="OTP must be a 6-digit number.")
    ])
    submit = SubmitField('Verify')


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=6, message="Password must be at least 6 characters.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('new_password', message="Passwords must match exactly.")
    ])
    submit = SubmitField('Reset Password')
