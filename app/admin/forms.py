from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, BooleanField, SelectField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Email
from flask_wtf.file import FileField, FileAllowed

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(min=3, max=150)])
    brand = StringField('Brand Name', validators=[DataRequired(), Length(min=2, max=50)])
    category_id = SelectField('Category', choices=[], validators=[DataRequired()])
    sku = StringField('SKU / Model Code', validators=[Optional(), Length(min=3, max=30)])
    regular_price = FloatField('Regular Price (₹)', validators=[DataRequired(), NumberRange(min=1.0)])
    discount = FloatField('Discount (%)', default=0.0, validators=[Optional(), NumberRange(min=0.0, max=99.0)])
    stock_quantity = IntegerField('Stock Quantity', default=10, validators=[DataRequired(), NumberRange(min=0)])
    short_description = TextAreaField('Short Description', validators=[Optional(), Length(max=250)])
    description = TextAreaField('Detailed Specifications / Overview', validators=[Optional(), Length(max=3000)])
    thumbnail = StringField('Main Thumbnail URL', validators=[Optional(), Length(max=500)])
    thumbnail_upload = FileField('Upload Thumbnail Image (replaces URL)', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp', 'gif'], 'Images only!')])
    images = TextAreaField('Additional Gallery Image URLs (one per line or comma-separated)', validators=[Optional()])
    gallery_upload = MultipleFileField('Upload Gallery Images', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp', 'gif'], 'Images only!')])
    variants = StringField('Variants / Options (comma-separated, e.g. 128GB, 256GB or Red, Blue)', validators=[Optional()])
    is_featured = BooleanField('Show in Featured Carousel on Homepage')
    status = SelectField('Catalog Status', choices=[
        ('active', 'Live Active (Published)'),
        ('not_available', 'Not Available / Out of Stock'),
        ('coming_soon', 'Coming Soon / Pre-Order'),
        ('draft', 'Draft (Hidden)'),
        ('archived', 'Archived / Discontinued')
    ], default='active')
    submit = SubmitField('Save Product')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(min=2, max=60)])
    description = StringField('Short Tagline / Promo Description (Optional)', validators=[Optional(), Length(max=200)])
    parent_id = SelectField('Parent Category (Optional)', choices=[], validators=[Optional()])
    icon = StringField('FontAwesome Icon Class (e.g. fa-tag, fa-mobile-screen, fa-shirt)', default='fa-tag', validators=[Optional(), Length(max=50)])
    image = StringField('Category Image URL (Optional)', validators=[Optional(), Length(max=500)])
    image_upload = FileField('Upload Image (Optional)', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp', 'gif'], 'Images only!')])

    submit = SubmitField('Save Category')


class BrandForm(FlaskForm):
    name = StringField('Brand Name', validators=[DataRequired(), Length(min=2, max=50)])
    logo = StringField('Brand Logo URL', validators=[Optional(), Length(max=500)])
    description = TextAreaField('Brand Overview', validators=[Optional(), Length(max=300)])
    submit = SubmitField('Save Brand')


class CouponForm(FlaskForm):
    code = StringField('Coupon Code (e.g. SUMMER20)', validators=[DataRequired(), Length(min=3, max=20)])
    description = StringField('Description', validators=[DataRequired(), Length(max=150)])
    discount_type = SelectField('Discount Type', choices=[('percentage', 'Percentage Off (%)'), ('fixed', 'Fixed Amount Off (₹)')], default='percentage')
    discount_value = FloatField('Discount Value', validators=[DataRequired(), NumberRange(min=1.0)])
    min_order_value = FloatField('Minimum Order Value (₹)', default=0.0, validators=[Optional(), NumberRange(min=0.0)])
    max_uses = IntegerField('Maximum Total Usage Limit', default=100, validators=[Optional(), NumberRange(min=1)])
    status = SelectField('Status', choices=[('active', 'Active'), ('expired', 'Disabled / Expired')], default='active')
    submit = SubmitField('Save Promo Coupon')


class BannerForm(FlaskForm):
    title = StringField('Headline Title', validators=[DataRequired(), Length(min=3, max=100)])
    subtitle = StringField('Sub-headline', validators=[Optional(), Length(max=200)])
    image_url = StringField('Background Image URL (Optional)', validators=[Optional(), Length(max=500)])
    image_upload = FileField('Upload Banner Image File (Optional)', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp', 'gif'], 'Images only!')])
    link_url = StringField('Button Destination URL', validators=[Optional(), Length(max=500)])
    banner_type = SelectField('Display Location', choices=[('homepage', 'Homepage Hero Slider'), ('promo', 'Mid-Page Strip')], default='homepage')
    sort_order = IntegerField('Sort Order (Lower appears first)', default=1, validators=[Optional()])
    status = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'Hidden')], default='active')
    submit = SubmitField('Save Banner')


class OrderStatusForm(FlaskForm):
    order_status = SelectField('Shipment Status', choices=[
        ('Pending', 'Pending'),
        ('Processing', 'Processing & Packed'),
        ('Shipped', 'Shipped via Courier'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled by Admin'),
        ('Returned', 'Returned / Refunded')
    ], validators=[DataRequired()])
    tracking_number = StringField('AWB Courier Tracking ID', validators=[Optional(), Length(max=50)])
    note = StringField('Status Audit Note (visible to customer)', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Update Order Status')


class StoreSettingsForm(FlaskForm):
    store_name = StringField('Store Name', validators=[DataRequired(), Length(min=2, max=100)])
    contact_email = StringField('Contact Email', validators=[DataRequired(), Length(max=100)])
    contact_phone = StringField('Contact Phone', validators=[DataRequired(), Length(max=20)])
    whatsapp_number = StringField('WhatsApp Business Number', validators=[Optional(), Length(max=25)])
    delivery_charge_per_km = FloatField('Delivery Cost (per km)', default=10.0, validators=[Optional(), NumberRange(min=0.0)])
    submit_settings = SubmitField('Save Configuration')


class AdminPasswordResetForm(FlaskForm):
    current_password = StringField('Current Password', validators=[DataRequired()])
    new_password = StringField('New Password', validators=[DataRequired(), Length(min=6, max=50)])
    confirm_password = StringField('Confirm New Password', validators=[DataRequired(), Length(min=6, max=50)])
    submit_password = SubmitField('Update Password')

class SubAdminForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = StringField('Account Password', validators=[DataRequired(), Length(min=6, max=50)])
    role = SelectField('Role', choices=[('delivery', 'Delivery Personnel')], validators=[DataRequired()])
    submit = SubmitField('Create Subadmin')
