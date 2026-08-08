import uuid
import datetime
import logging
import math
from app.db import mongo
from app.utils.helpers import generate_order_number

logger = logging.getLogger(__name__)

class Cart:
    """Shopping cart model wrapping the MongoDB 'cart' collection."""
    def __init__(self, doc):
        self._doc = doc
        self.id = str(doc.get('_id'))
        self.user_id = doc.get('user_id')
        self.session_id = doc.get('session_id')
        self.items = doc.get('items', [])
        self.coupon_code = doc.get('coupon_code')
        self.updated_at = doc.get('updated_at')

    @classmethod
    def get_cart(cls, user_id=None, session_id=None):
        if not user_id and not session_id:
            return None
        try:
            col = mongo.get_collection('cart')
            query = {}
            if user_id:
                query = {"user_id": str(user_id)}
            elif session_id:
                query = {"session_id": str(session_id)}
                
            doc = col.find_one(query)
            if not doc:
                doc = {
                    "_id": str(uuid.uuid4()),
                    "user_id": str(user_id) if user_id else None,
                    "session_id": str(session_id) if session_id else None,
                    "items": [],
                    "coupon_code": None,
                    "updated_at": datetime.datetime.now()
                }
                col.insert_one(doc)
            return cls(doc)
        except Exception as e:
            logger.warning(f"Database error in Cart.get_cart (returning in-memory fallback): {e}")
            doc = {
                "_id": str(uuid.uuid4()),
                "user_id": str(user_id) if user_id else None,
                "session_id": str(session_id) if session_id else None,
                "items": [],
                "coupon_code": None,
                "updated_at": datetime.datetime.now()
            }
            return cls(doc)

    def add_item(self, product_id, quantity=1, variant=None):
        from app.models.product import Product
        prod = Product.get_by_id(product_id)
        if not prod or not prod.in_stock:
            return False, "Product out of stock or unavailable."
            
        quantity = int(quantity)
        if quantity <= 0:
            return False, "Invalid quantity."
            
        # Check if item exists in cart
        found = False
        for item in self.items:
            if item.get('product_id') == str(product_id) and item.get('variant') == variant:
                new_qty = item.get('quantity', 1) + quantity
                if new_qty > prod.stock_quantity:
                    return False, f"Only {prod.stock_quantity} units available in stock."
                item['quantity'] = new_qty
                found = True
                break
                
        if not found:
            if quantity > prod.stock_quantity:
                return False, f"Only {prod.stock_quantity} units available in stock."
            self.items.append({
                "product_id": str(product_id),
                "quantity": quantity,
                "variant": variant,
                "price_at_addition": prod.price_after_discount,
                "added_at": datetime.datetime.now()
            })
            
        mongo.get_collection('cart').update_one(
            {"_id": self.id},
            {"$set": {"items": self.items, "updated_at": datetime.datetime.now()}}
        )
        return True, "Item added to cart."

    def update_quantity(self, product_id, quantity, variant=None):
        quantity = int(quantity)
        if quantity <= 0:
            return self.remove_item(product_id, variant)
            
        from app.models.product import Product
        prod = Product.get_by_id(product_id)
        if prod and quantity > prod.stock_quantity:
            return False, f"Only {prod.stock_quantity} units available in stock."
            
        for item in self.items:
            if item.get('product_id') == str(product_id) and item.get('variant') == variant:
                item['quantity'] = quantity
                break
                
        mongo.get_collection('cart').update_one(
            {"_id": self.id},
            {"$set": {"items": self.items, "updated_at": datetime.datetime.now()}}
        )
        return True, "Cart updated."

    def remove_item(self, product_id, variant=None):
        self.items = [item for item in self.items if not (item.get('product_id') == str(product_id) and item.get('variant') == variant)]
        mongo.get_collection('cart').update_one(
            {"_id": self.id},
            {"$set": {"items": self.items, "updated_at": datetime.datetime.now()}}
        )
        return True, "Item removed from cart."

    def apply_coupon(self, coupon_code):
        from app.models.marketing import Coupon
        coupon = Coupon.get_by_code(coupon_code)
        if not coupon or not coupon.is_valid():
            return False, "Invalid or expired coupon code."
            
        summary = self.get_summary(ignore_coupon=True)
        if summary['subtotal'] < coupon.min_purchase:
            return False, f"Minimum purchase of ₹{coupon.min_purchase:,.2f} required for this coupon."
            
        self.coupon_code = coupon.code
        mongo.get_collection('cart').update_one(
            {"_id": self.id},
            {"$set": {"coupon_code": self.coupon_code, "updated_at": datetime.datetime.now()}}
        )
        return True, f"Coupon '{coupon.code}' applied successfully!"

    def remove_coupon(self):
        self.coupon_code = None
        mongo.get_collection('cart').update_one(
            {"_id": self.id},
            {"$set": {"coupon_code": None, "updated_at": datetime.datetime.now()}}
        )
        return True, "Coupon removed."

    def clear(self):
        self.items = []
        self.coupon_code = None
        mongo.get_collection('cart').update_one(
            {"_id": self.id},
            {"$set": {"items": [], "coupon_code": None, "updated_at": datetime.datetime.now()}}
        )

    def get_summary(self, ignore_coupon=False):
        from app.models.product import Product
        from app.models.marketing import Coupon
        
        detailed_items = []
        subtotal = 0.0
        
        for item in self.items:
            prod = Product.get_by_id(item['product_id'])
            if prod and prod.status == 'active':
                price = prod.price_after_discount
                qty = item.get('quantity', 1)
                item_total = price * qty
                subtotal += item_total
                detailed_items.append({
                    "product": prod,
                    "product_id": prod.id,
                    "name": prod.name,
                    "slug": prod.slug,
                    "thumbnail": prod.thumbnail,
                    "price": price,
                    "regular_price": prod.regular_price,
                    "discount": prod.discount,
                    "quantity": qty,
                    "variant": item.get('variant'),
                    "total": item_total
                })
                
        # Load shipping & GST settings
        free_thresh = 999.0
        shipping_charge = 49.0
        try:
            thresh_set = mongo.get_collection('settings').find_one({"key": "free_shipping_threshold"})
            if thresh_set:
                free_thresh = float(thresh_set['value'])
            ship_set = mongo.get_collection('settings').find_one({"key": "standard_shipping_charge"})
            if ship_set:
                shipping_charge = float(ship_set['value'])
        except Exception:
            pass
            
        actual_shipping = 0.0 if (subtotal == 0 or subtotal >= free_thresh) else shipping_charge
        
        # Coupon discount
        discount_amount = 0.0
        applied_coupon = None
        if not ignore_coupon and self.coupon_code:
            coupon = Coupon.get_by_code(self.coupon_code)
            if coupon and coupon.is_valid() and subtotal >= coupon.min_purchase:
                applied_coupon = coupon
                if coupon.discount_type == 'percentage':
                    calc_disc = (subtotal * coupon.discount_value) / 100.0
                    discount_amount = min(calc_disc, coupon.max_discount) if coupon.max_discount > 0 else calc_disc
                else:
                    discount_amount = coupon.discount_value
            else:
                self.remove_coupon()
                
        tax_amount = round((subtotal - discount_amount) * 0.18, 2) if subtotal > 0 else 0.0
        grand_total = max(0.0, round(subtotal - discount_amount + actual_shipping, 2))
        
        return {
            "cart_items": detailed_items,
            "items": detailed_items,
            "item_count": sum(item['quantity'] for item in detailed_items),
            "subtotal": round(subtotal, 2),
            "shipping_charge": round(actual_shipping, 2),
            "free_shipping_threshold": free_thresh,
            "discount_amount": round(discount_amount, 2),
            "applied_coupon": applied_coupon,
            "tax_amount": tax_amount,
            "grand_total": grand_total
        }


class Order:
    """Order model wrapping the MongoDB 'orders' collection."""
    def __init__(self, doc):
        self._doc = doc
        self.id = str(doc.get('_id'))
        self.order_number = doc.get('order_number', '')
        self.user_id = doc.get('user_id')
        self.user_name = doc.get('user_name', '')
        self.user_email = doc.get('user_email', '')
        self.items = doc.get('items', [])
        self.shipping_address = doc.get('shipping_address', {})
        self.billing_summary = doc.get('billing_summary', {})
        self.grand_total = doc.get('grand_total') if doc.get('grand_total') is not None else self.billing_summary.get('grand_total', 0.0)
        self.subtotal = doc.get('subtotal') if doc.get('subtotal') is not None else self.billing_summary.get('subtotal', 0.0)
        self.shipping_charge = doc.get('shipping_charge') if doc.get('shipping_charge') is not None else self.billing_summary.get('shipping_charge', 0.0)
        self.discount_amount = doc.get('discount_amount') if doc.get('discount_amount') is not None else self.billing_summary.get('discount_amount', 0.0)
        self.tax_amount = doc.get('tax_amount') if doc.get('tax_amount') is not None else self.billing_summary.get('tax_amount', 0.0)
        self.payment_method = doc.get('payment_method', 'COD')
        self.payment_status = doc.get('payment_status', 'Pending')
        self.order_status = doc.get('order_status', 'Placed')
        self.tracking_number = doc.get('tracking_number', '')
        self.tracking_history = doc.get('tracking_history', [])
        self.delivery_boy_id = doc.get('delivery_boy_id')
        self.delivery_boy_name = doc.get('delivery_boy_name')
        self.created_at = doc.get('created_at')

    @classmethod
    def create_from_cart(cls, cart, user, shipping_address, payment_method="COD", payment_status="Pending"):
        from app.models.product import Product
        from app.models.marketing import Coupon
        
        summary = cart.get_summary()
        if not summary['items']:
            return None, "Cart is empty."
            
        # Override shipping charge based on distance
        distance_km = shipping_address.get('distance_km', 0.0) if isinstance(shipping_address, dict) else 0.0
        if distance_km > 0:
            from app.db import mongo
            delivery_charge_per_km = 10.0
            try:
                setting_doc = mongo.get_collection('settings').find_one({"key": "delivery_charge_per_km"})
                if setting_doc:
                    delivery_charge_per_km = float(setting_doc['value'])
            except Exception:
                pass
            
            summary['shipping_charge'] = round(distance_km * delivery_charge_per_km, 2)
            summary['grand_total'] = max(0.0, round(summary['subtotal'] - summary['discount_amount'] + summary['shipping_charge'], 2))
            
        order_id = str(uuid.uuid4())
        order_num = generate_order_number()
        
        # Deduct stock for each item
        order_items = []
        for item in summary['items']:
            prod = item['product']
            prod.update_stock(-item['quantity'])
            order_items.append({
                "product_id": prod.id,
                "name": prod.name,
                "slug": prod.slug,
                "price": item['price'],
                "quantity": item['quantity'],
                "variant": item.get('variant'),
                "thumbnail": prod.thumbnail,
                "total": item['total']
            })
            
        # Increment coupon usage
        if summary['applied_coupon']:
            summary['applied_coupon'].increment_usage()
            
        tracking = [
            {
                "status": "Placed",
                "timestamp": datetime.datetime.now(),
                "note": f"Order placed successfully via {payment_method}."
            }
        ]
        if payment_status == "Paid":
            tracking.append({
                "status": "Processing",
                "timestamp": datetime.datetime.now(),
                "note": "Payment verified. Order is being processed."
            })
            
        doc = {
            "_id": order_id,
            "order_number": order_num,
            "user_id": user.id,
            "user_name": user.name,
            "user_email": user.email,
            "items": order_items,
            "shipping_address": shipping_address,
            "billing_summary": {
                "subtotal": summary['subtotal'],
                "shipping_charge": summary['shipping_charge'],
                "discount_amount": summary['discount_amount'],
                "coupon_code": cart.coupon_code,
                "tax_amount": summary['tax_amount'],
                "grand_total": summary['grand_total']
            },
            "subtotal": summary['subtotal'],
            "shipping_charge": summary['shipping_charge'],
            "discount_amount": summary['discount_amount'],
            "tax_amount": summary['tax_amount'],
            "grand_total": summary['grand_total'],
            "payment_method": payment_method,
            "payment_status": payment_status,
            "order_status": "Processing" if payment_status == "Paid" else "Placed",
            "tracking_history": tracking,
            "created_at": datetime.datetime.now()
        }
        
        mongo.get_collection('orders').insert_one(doc)
        
        # Create user notification
        mongo.get_collection('notifications').insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": user.id,
            "title": f"Order Confirmed: {order_num}",
            "message": f"Your order of ₹{summary['grand_total']:,.2f} has been placed successfully.",
            "type": "order",
            "is_read": False,
            "created_at": datetime.datetime.now()
        })
        
        # Clear cart
        cart.clear()
        
        return cls(doc), "Order placed successfully!"

    @classmethod
    def get_by_id(cls, order_id):
        doc = mongo.get_collection('orders').find_one({"_id": str(order_id)})
        return cls(doc) if doc else None

    @classmethod
    def get_by_order_number(cls, order_number):
        doc = mongo.get_collection('orders').find_one({"order_number": order_number})
        return cls(doc) if doc else None

    @classmethod
    def get_user_orders(cls, user_id):
        cursor = mongo.get_collection('orders').find({"user_id": str(user_id)}).sort("created_at", -1)
        return [cls(doc) for doc in cursor]

    @classmethod
    def get_all(cls, filter_dict=None, sort_by=None, page=1, per_page=20):
        if filter_dict is None:
            filter_dict = {}
            
        col = mongo.get_collection('orders')
        total_count = col.count_documents(filter_dict)
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
        page = max(1, min(page, total_pages))
        
        cursor = col.find(filter_dict).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page)
        orders = [cls(doc) for doc in cursor]
        
        return {
            "orders": orders,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page
        }

    def update_status(self, new_status, note="", tracking_number=None):
        self.order_status = new_status
        if new_status == "Delivered":
            self.payment_status = "Paid"
            
        if tracking_number:
            self.tracking_number = tracking_number
            
        history_entry = {
            "status": new_status,
            "timestamp": datetime.datetime.now(),
            "note": note or f"Order marked as {new_status}."
        }
        if tracking_number:
            history_entry["tracking_number"] = tracking_number
            
        self.tracking_history.append(history_entry)
        
        update_dict = {
            "order_status": self.order_status,
            "payment_status": self.payment_status,
            "tracking_history": self.tracking_history
        }
        if tracking_number:
            update_dict["tracking_number"] = self.tracking_number
            
        mongo.get_collection('orders').update_one({"_id": self.id}, {"$set": update_dict})
        
        # Notify user
        mongo.get_collection('notifications').insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": self.user_id,
            "title": f"Order {self.order_number} Update: {new_status}",
            "message": f"Your order status has been updated to {new_status}. {note}",
            "type": "order",
            "is_read": False,
            "created_at": datetime.datetime.now()
        })

    def assign_delivery_boy(self, delivery_boy_id, delivery_boy_name):
        self.delivery_boy_id = delivery_boy_id
        self.delivery_boy_name = delivery_boy_name
        mongo.get_collection('orders').update_one(
            {"_id": self.id},
            {"$set": {
                "delivery_boy_id": delivery_boy_id,
                "delivery_boy_name": delivery_boy_name
            }}
        )

    def cancel(self, reason="Cancelled by user"):
        if self.order_status in ["Out for Delivery", "Delivered", "Cancelled", "Returned"]:
            return False, f"Cannot cancel order in {self.order_status} state."
            
        # Restore stock
        from app.models.product import Product
        for item in self.items:
            prod = Product.get_by_id(item['product_id'])
            if prod:
                prod.update_stock(item['quantity'])
                
        self.update_status("Cancelled", note=f"Reason: {reason}")
        return True, "Order cancelled successfully."

    def request_return(self, reason="Return requested"):
        if self.order_status != "Delivered":
            return False, "Only delivered orders can be returned."
        self.update_status("Return Requested", note=f"Reason: {reason}")
        return True, "Return request initiated."

    def delete(self):
        # Restore stock if deleting an active order that hasn't been cancelled or returned
        if self.order_status not in ["Cancelled", "Returned", "Return Requested"]:
            from app.models.product import Product
            for item in self.items:
                prod = Product.get_by_id(item.get('product_id'))
                if prod:
                    prod.update_stock(item.get('quantity', 0))
        mongo.get_collection('orders').delete_one({"_id": self.id})

