from flask import Blueprint

cart_bp = Blueprint('cart', __name__, template_folder='../templates/cart')

from app.cart import routes, services
