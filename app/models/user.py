import uuid
import datetime
import logging
import random
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import mongo
from app.extensions import login_manager

logger = logging.getLogger(__name__)

class User(UserMixin):
    """Customer user model wrapping the MongoDB 'users' collection."""
    def __init__(self, doc):
        self._doc = doc
        self.id = str(doc.get('_id'))
        self.name = doc.get('name', '')
        self.email = doc.get('email', '')
        self.password_hash = doc.get('password', '')
        self.phone = doc.get('phone', '')
        self.status = doc.get('status', 'active')
        self.email_verified = doc.get('email_verified', False)
        self.addresses = doc.get('addresses', [])
        self.created_at = doc.get('created_at')
        self.reset_otp = doc.get('reset_otp')
        self.reset_otp_expiry = doc.get('reset_otp_expiry')
        self.last_login = doc.get('last_login')
        self.profile_pic = doc.get('profile_pic', '')

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_admin(self):
        return False

    def get_id(self):
        return self.id

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_id(cls, user_id):
        try:
            doc = mongo.get_collection('users').find_one({"_id": str(user_id)})
            return cls(doc) if doc else None
        except Exception as e:
            logger.error(f"Error fetching user by id {user_id}: {e}")
            return None

    @classmethod
    def get_by_email(cls, email):
        try:
            doc = mongo.get_collection('users').find_one({"email": email.lower().strip()})
            return cls(doc) if doc else None
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            return None

    @classmethod
    def create(cls, name, email, password, phone='', is_admin=False, **kwargs):
        user_id = str(uuid.uuid4())
        hashed_pw = generate_password_hash(password)
        doc = {
            "_id": user_id,
            "name": name.strip(),
            "email": email.lower().strip(),
            "password": hashed_pw,
            "phone": phone.strip() if phone else '',
            "status": "active",
            "email_verified": True,
            "is_admin": is_admin,
            "addresses": [],
            "created_at": datetime.datetime.now()
        }
        doc.update(kwargs)
        try:
            mongo.get_collection('users').insert_one(doc)
            return cls(doc)
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            return None

    def update_profile(self, name, phone, profile_pic=''):
        self.name = name.strip()
        self.phone = phone.strip() if phone else ''
        self.profile_pic = profile_pic.strip() if profile_pic else ''
        mongo.get_collection('users').update_one(
            {"_id": self.id},
            {"$set": {"name": self.name, "phone": self.phone, "profile_pic": self.profile_pic}}
        )

    def update_last_login(self):
        self.last_login = datetime.datetime.now()
        mongo.get_collection('users').update_one(
            {"_id": self.id},
            {"$set": {"last_login": self.last_login}}
        )

    def update_password(self, new_password):
        self.password_hash = generate_password_hash(new_password)
        mongo.get_collection('users').update_one(
            {"_id": self.id},
            {"$set": {"password": self.password_hash}}
        )
        return True

    def generate_reset_otp(self):
        self.reset_otp = str(random.randint(100000, 999999))
        self.reset_otp_expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
        mongo.get_collection('users').update_one(
            {"_id": self.id},
            {"$set": {"reset_otp": self.reset_otp, "reset_otp_expiry": self.reset_otp_expiry}}
        )
        return self.reset_otp

    def verify_reset_otp(self, otp):
        if self.reset_otp and self.reset_otp == otp.strip():
            if self.reset_otp_expiry and self.reset_otp_expiry > datetime.datetime.now():
                return True
        return False

    def clear_reset_otp(self):
        self.reset_otp = None
        self.reset_otp_expiry = None
        mongo.get_collection('users').update_one(
            {"_id": self.id},
            {"$unset": {"reset_otp": "", "reset_otp_expiry": ""}}
        )

    def add_address(self, address_data):
        address_id = str(uuid.uuid4())
        address_data['address_id'] = address_id
        
        # If this is the first address or marked default, unset others as default
        is_default = address_data.get('is_default', False) or len(self.addresses) == 0
        address_data['is_default'] = is_default
        
        if is_default:
            for addr in self.addresses:
                addr['is_default'] = False
                
        self.addresses.append(address_data)
        mongo.get_collection('users').update_one(
            {"_id": self.id},
            {"$set": {"addresses": self.addresses}}
        )
        return address_id

    def update_address(self, address_id, address_data):
        is_default = address_data.get('is_default', False)
        for i, addr in enumerate(self.addresses):
            if addr.get('address_id') == address_id:
                address_data['address_id'] = address_id
                self.addresses[i] = address_data
                break
                
        if is_default:
            for addr in self.addresses:
                if addr.get('address_id') != address_id:
                    addr['is_default'] = False
                    
        mongo.get_collection('users').update_one(
            {"_id": self.id},
            {"$set": {"addresses": self.addresses}}
        )

    def remove_address(self, index_or_id):
        return self.delete_address(index_or_id)

    def delete_address(self, index_or_id):
        if isinstance(index_or_id, int) or (isinstance(index_or_id, str) and index_or_id.isdigit()):
            idx = int(index_or_id)
            if 0 <= idx < len(self.addresses):
                self.addresses.pop(idx)
            else:
                return False
        else:
            initial_len = len(self.addresses)
            self.addresses = [a for a in self.addresses if a.get('address_id') != index_or_id]
            if len(self.addresses) == initial_len:
                return False
        if self.addresses and not any(a.get('is_default') for a in self.addresses):
            self.addresses[0]['is_default'] = True
        mongo.get_collection('users').update_one(
            {"_id": self.id},
            {"$set": {"addresses": self.addresses}}
        )
        return True

    def set_default_address(self, index_or_id):
        found = False
        if isinstance(index_or_id, int) or (isinstance(index_or_id, str) and index_or_id.isdigit()):
            idx = int(index_or_id)
            for i, addr in enumerate(self.addresses):
                addr['is_default'] = (i == idx)
                if i == idx:
                    found = True
        else:
            for addr in self.addresses:
                addr['is_default'] = (addr.get('address_id') == index_or_id)
                if addr['is_default']:
                    found = True
        if found:
            mongo.get_collection('users').update_one(
                {"_id": self.id},
                {"$set": {"addresses": self.addresses}}
            )
            return True
        return False

    def get_default_address(self):
        for addr in self.addresses:
            if addr.get('is_default'):
                return addr
        return self.addresses[0] if self.addresses else None

    def toggle_wishlist(self, product_id):
        wish_col = mongo.get_collection('wishlist')
        doc = wish_col.find_one({"user_id": self.id})
        if not doc:
            wish_col.insert_one({
                "_id": str(uuid.uuid4()),
                "user_id": self.id,
                "product_ids": [product_id],
                "updated_at": datetime.datetime.now()
            })
            return True, "Added to wishlist"
        
        product_ids = doc.get('product_ids', [])
        if product_id in product_ids:
            product_ids.remove(product_id)
            status = False
            msg = "Removed from wishlist"
        else:
            product_ids.append(product_id)
            status = True
            msg = "Added to wishlist"
            
        wish_col.update_one(
            {"user_id": self.id},
            {"$set": {"product_ids": product_ids, "updated_at": datetime.datetime.now()}}
        )
        return status, msg

    def get_wishlist_products(self):
        doc = mongo.get_collection('wishlist').find_one({"user_id": self.id})
        if not doc or not doc.get('product_ids'):
            return []
        
        from app.models.product import Product
        products = []
        for pid in doc['product_ids']:
            prod = Product.get_by_id(pid)
            if prod and prod.status == 'active':
                products.append(prod)
        return products


class Admin(UserMixin):
    """Admin user model wrapping the MongoDB 'admins' collection."""
    def __init__(self, doc):
        self._doc = doc
        self.id = str(doc.get('_id'))
        self.name = doc.get('name', 'Admin')
        self.email = doc.get('email', '')
        self.password_hash = doc.get('password', '')
        self.role = doc.get('role', 'admin')
        self.status = doc.get('status', 'active')
        self.last_login = doc.get('last_login')
        self.profile_pic = doc.get('profile_pic', '')
        self.reset_otp = doc.get('reset_otp')
        self.reset_otp_expiry = doc.get('reset_otp_expiry')

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_admin(self):
        return True

    def get_id(self):
        return self.id

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_password(self, new_password):
        self.password_hash = generate_password_hash(new_password)
        mongo.get_collection('admins').update_one(
            {"_id": self.id},
            {"$set": {"password": self.password_hash}}
        )
        return True

    def update_last_login(self):
        self.last_login = datetime.datetime.now()
        mongo.get_collection('admins').update_one(
            {"_id": self.id},
            {"$set": {"last_login": self.last_login}}
        )

    def generate_reset_otp(self):
        self.reset_otp = str(random.randint(100000, 999999))
        self.reset_otp_expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
        mongo.get_collection('admins').update_one(
            {"_id": self.id},
            {"$set": {"reset_otp": self.reset_otp, "reset_otp_expiry": self.reset_otp_expiry}}
        )
        return self.reset_otp

    def verify_reset_otp(self, otp):
        if self.reset_otp and self.reset_otp == otp.strip():
            if self.reset_otp_expiry and self.reset_otp_expiry > datetime.datetime.now():
                return True
        return False

    def clear_reset_otp(self):
        self.reset_otp = None
        self.reset_otp_expiry = None
        mongo.get_collection('admins').update_one(
            {"_id": self.id},
            {"$unset": {"reset_otp": "", "reset_otp_expiry": ""}}
        )

    @classmethod
    def get_by_id(cls, admin_id):
        try:
            doc = mongo.get_collection('admins').find_one({"_id": str(admin_id)})
            return cls(doc) if doc else None
        except Exception as e:
            logger.error(f"Error fetching admin by id {admin_id}: {e}")
            return None

    @classmethod
    def get_by_email(cls, email):
        try:
            doc = mongo.get_collection('admins').find_one({"email": email.lower().strip()})
            return cls(doc) if doc else None
        except Exception as e:
            logger.error(f"Error fetching admin by email {email}: {e}")
            return None

    @classmethod
    def get_by_role(cls, role):
        try:
            docs = mongo.get_collection('admins').find({"role": role})
            return [cls(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error fetching admins by role {role}: {e}")
            return []

    @classmethod
    def create_subadmin(cls, name, email, password, role="delivery"):
        import uuid
        admin_id = str(uuid.uuid4())
        doc = {
            "_id": admin_id,
            "name": name,
            "email": email.lower().strip(),
            "password": generate_password_hash(password),
            "role": role,
            "status": "active",
            "created_at": datetime.datetime.now()
        }
        mongo.get_collection('admins').insert_one(doc)
        return cls(doc)

    def delete(self):
        try:
            mongo.get_collection('admins').delete_one({"_id": self.id})
            return True
        except Exception as e:
            logger.error(f"Error deleting admin {self.id}: {e}")
            return False

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader callback trying Admin first, then User."""
    return Admin.get_by_id(user_id) or User.get_by_id(user_id)
