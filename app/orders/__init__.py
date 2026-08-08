from flask import Blueprint

orders_bp = Blueprint('orders', __name__, template_folder='../templates/orders')

from app.orders import routes, pdf_service
