import os
import uuid
import datetime
from app import create_app
from app.db import mongo
from werkzeug.security import generate_password_hash

app = create_app(os.getenv('FLASK_ENV', 'development'))

with app.app_context():
    admin_doc = {
        "_id": str(uuid.uuid4()),
        "name": "Super Admin",
        "email": "admin@fancystore.com",
        "password": generate_password_hash("admin123"),
        "role": "super_admin",
        "status": "active",
        "created_at": datetime.datetime.now(),
        "last_login": None
    }
    mongo.get_collection('admins').insert_one(admin_doc)
    print("Admin account created successfully!")
