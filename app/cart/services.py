import uuid
import datetime
from flask import session
from flask_login import current_user
from app.db import mongo
from app.models.order import Cart
from app.models.product import Product

def get_current_cart():
    """Retrieve active Cart instance for authenticated user or anonymous session."""
    user_id = None
    session_id = None
    
    if current_user.is_authenticated and not getattr(current_user, 'is_admin', False):
        user_id = current_user.id
        # Check if there is an anonymous cart to merge
        if 'cart_session_id' in session:
            merge_session_cart_to_user(user_id, session['cart_session_id'])
            session.pop('cart_session_id', None)
    else:
        if 'cart_session_id' not in session:
            session['cart_session_id'] = str(uuid.uuid4())
        session_id = session['cart_session_id']
        
    return Cart.get_cart(user_id=user_id, session_id=session_id)


def merge_session_cart_to_user(user_id, session_id):
    """Merge anonymous session cart items into authenticated user cart upon login."""
    if not session_id or not user_id:
        return
        
    try:
        col = mongo.get_collection('cart')
        session_doc = col.find_one({"session_id": str(session_id)})
        if not session_doc or not session_doc.get('items'):
            return
            
        user_cart = Cart.get_cart(user_id=user_id)
        for item in session_doc['items']:
            user_cart.add_item(item['product_id'], quantity=item.get('quantity', 1), variant=item.get('variant'))
            
        col.delete_one({"_id": session_doc['_id']})
    except Exception as e:
        pass


def get_user_wishlist():
    """Get list of Product objects currently saved in user's wishlist."""
    try:
        col = mongo.get_collection('wishlist')
        query = {}
        if current_user.is_authenticated and not getattr(current_user, 'is_admin', False):
            query = {"user_id": str(current_user.id)}
        elif 'wishlist_session_id' in session:
            query = {"session_id": str(session['wishlist_session_id'])}
        else:
            return []
            
        doc = col.find_one(query)
        if not doc or not doc.get('product_ids'):
            return []
            
        products = []
        for pid in doc['product_ids']:
            prod = Product.get_by_id(pid)
            if prod and prod.status == 'active':
                products.append(prod)
                
        session['wishlist_items'] = doc['product_ids']
        return products
    except Exception as e:
        return []


def toggle_wishlist_item(product_id):
    """Add or remove product ID from user's wishlist document."""
    try:
        col = mongo.get_collection('wishlist')
        query = {}
        
        if current_user.is_authenticated and not getattr(current_user, 'is_admin', False):
            query = {"user_id": str(current_user.id)}
        else:
            if 'wishlist_session_id' not in session:
                session['wishlist_session_id'] = str(uuid.uuid4())
            query = {"session_id": str(session['wishlist_session_id'])}
            
        doc = col.find_one(query)
        product_ids = doc.get('product_ids', []) if doc else []
        
        in_wishlist = False
        if str(product_id) in product_ids:
            product_ids.remove(str(product_id))
            in_wishlist = False
            msg = "Item removed from your wishlist."
        else:
            product_ids.append(str(product_id))
            in_wishlist = True
            msg = "Item saved to your wishlist!"
            
        if doc:
            col.update_one({"_id": doc['_id']}, {"$set": {"product_ids": product_ids, "updated_at": datetime.datetime.now()}})
        else:
            new_doc = {
                "_id": str(uuid.uuid4()),
                "user_id": query.get('user_id'),
                "session_id": query.get('session_id'),
                "product_ids": product_ids,
                "updated_at": datetime.datetime.now()
            }
            col.insert_one(new_doc)
            
        session['wishlist_items'] = product_ids
        return in_wishlist, len(product_ids), msg
    except Exception as e:
        return False, 0, "Database connection error."
