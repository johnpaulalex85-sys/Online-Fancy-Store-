from app import create_app
from app.models.order import Order
from flask import render_template
app=create_app()
with app.test_request_context('/'):
    order=Order.get_by_order_number('ORD-20260801-4365F6')
    try:
        html = render_template('orders/detail.html', order=order)
        print('Render successful')
    except Exception as e:
        import traceback; traceback.print_exc()
