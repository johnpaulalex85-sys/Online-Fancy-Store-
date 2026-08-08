from app import create_app
from app.models.order import Order
from app.models.user import Admin
from flask_login import login_user
from flask import render_template

app=create_app()
app.config['SERVER_NAME'] = 'localhost:5000'
app.config['WTF_CSRF_ENABLED'] = False
app.app_context().push()
admin = Admin.get_by_email('admin@fancystore.com')

with app.test_request_context('/'):
    login_user(admin)
    order=Order.get_by_order_number('ORD-20260801-4365F6')
    try:
        html = render_template('orders/detail.html', order=order)
        print('Render successful')
    except Exception as e:
        import traceback; traceback.print_exc()
