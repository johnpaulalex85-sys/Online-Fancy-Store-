# Fancy Store - Production-Ready Flipkart-Style E-Commerce Platform 🛒🚀

**Fancy Store** is an enterprise-grade, full-stack e-commerce web application built using **Python 3, Flask, PyMongo (MongoDB), Jinja2 Templates, and Bootstrap 5**. Designed with modern industry-standard architecture, it emulates the core features, aesthetics, and user experience of leading e-commerce platforms like Flipkart and Amazon India.

---

## 🌟 Key Features & Highlights

### 🛍️ Storefront & Catalog
* **Dynamic Homepage Showcase:** Interactive hero slider carousels, countdown Flash Sales with progress indicators, and curated Featured Product grids.
* **Faceted Product Search & Filtering:** Comprehensive catalog browsing with multi-brand filtering, category drill-downs, price range sliders, sorting options (*Price Low-to-High, Popularity, Newest*), and stock availability toggles.
* **Rich Product Detail Pages:** Multi-image interactive photo gallery, variant selection badges (*RAM, Storage, Color options*), technical specification breakdown, and customer rating/review submission.

### 🛒 Shopping Cart, Wishlist & Checkout
* **Intelligent Cart & Session Merging:** Add items to cart or wishlist as a guest; items seamlessly merge into your user profile upon logging in.
* **Promo Coupon Engine:** Apply promotional discount codes with real-time percentage or fixed discount calculations and minimum order value validations.
* **Interactive 3-Step Checkout Flow:**
  * **Step 1:** Customer delivery address selection and form validation.
  * **Step 2:** Order summary preview and item verification.
  * **Step 3:** **Live Payment Gateway Simulation**:
    * 💵 **Cash on Delivery (COD):** Standard verification and order placement.
    * 📱 **UPI Instant Pay:** Interactive QR code modal simulating PhonePe, Google Pay, and Paytm checkout with animated timers.
    * 💳 **Credit / Debit Card:** 3D Secure payment gateway simulation with instant OTP verification.

### 📦 Customer Dashboard & Order Tracking
* **Order History:** Complete log of active shipments and past purchases with color-coded status badges.
* **Live Shipment Tracking:** Interactive visual 5-step delivery progress timeline (*Order Placed &rarr; Packed &rarr; Shipped &rarr; Out for Delivery &rarr; Delivered*) with courier AWB tracking IDs and activity audit log.
* **Official GST Tax Invoices:** Download professional, computer-generated PDF tax invoices with itemized GST breakdown and printable layouts.
* **Self-Service Returns & Cancellations:** Customer-initiated pre-shipment cancellations and 7-day doorstep return requests.

### 🏢 Enterprise Admin Dashboard & Analytics
* **Executive KPI Dashboard:** Real-time metrics tracking Gross Revenue, Order Volume, Active Customers, and Low Stock inventory warnings.
* **Visual Sales Analytics:** Dynamic bar and line charts powered by Chart.js displaying 7-day revenue trends and order counts.
* **Catalog Inventory Management:** Full CRUD capabilities for Products, Categories, Partner Brands, and SKU pricing.
* **Order Fulfillment Center:** Update shipment progression and assign AWB courier tracking numbers directly from the admin interface.
* **Marketing & Moderation Controls:** Create promotional coupon codes, manage hero banners, and moderate customer product reviews (*Approve/Reject/Delete*).

---

## 🏗️ Technical Architecture & Design Patterns

The codebase is built on **MVC (Model-View-Controller)** principles using the **Application Factory Pattern** (`create_app`) and **Flask Blueprints** for clean modularity:

```text
app/
├── __init__.py           # Application Factory, Blueprint registration, Logging & Error Handlers
├── db.py                 # PyMongo database connection pool & collection helpers
├── middleware/           # Robust Security Middleware (CSRF, RBAC, XSS Sanitization, Rate Limiting)
├── models/               # Domain Models & Data Access Objects (User, Product, Order, Coupon, Banner)
├── utils/                # Custom Jinja2 Filters (currency formatting, date helpers)
├── static/
│   ├── css/index.css     # Design System, Glassmorphism tokens, and custom UI styling
│   └── js/cart.js        # AJAX cart management, Wishlist toggling, and Payment Simulations
├── templates/            # Responsive Jinja2 templates (Bootstrap 5.3)
│   ├── base.html         # Master layout with navbar, category dropdowns, and toast notifications
│   ├── auth/             # Login, Registration, and User Profile screens
│   ├── main/             # Storefront Homepage, Catalog, and Product Detail views
│   ├── cart/             # Shopping Cart, Wishlist, Checkout, and Order Confirmation
│   ├── orders/           # Customer Order History, Live Shipment Tracker, and Tax Invoices
│   └── admin/            # Executive Admin Analytics Dashboard and Inventory Management
└── ...
run.py                    # Server startup script with CLI database seeding commands
tests/test_app.py         # Automated integration test suite
```

### 🔐 Security & DevOps Best Practices
* **Role-Based Access Control (RBAC):** Strict separation between Customer and Administrator privileges.
* **CSRF & XSS Protection:** Flask-WTF CSRF token validation on all state-changing endpoints and automatic input sanitization.
* **Atomic Order Processing:** Stock reduction, coupon usage tracking, and invoice generation executed atomically during checkout.

---

## 🚀 Getting Started & Setup Instructions

### 1. Prerequisites
* **Python 3.8+** installed on your system.
* **MongoDB** server running locally (`mongodb://localhost:27017/`) or a valid MongoDB Atlas connection string.

### 2. Installation & Environment Setup
Clone the repository and install dependencies in a virtual environment:

```bash
# Create and activate virtual environment (Windows PowerShell)
python -m venv venv
.\venv\Scripts\activate

# Install required Python packages
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` (or verify existing settings):
```ini
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=super-secret-key-change-in-production-2026
MONGO_URI=mongodb://localhost:27017/fancy_store_db
```

### 4. Seed Demo Flipkart Catalog & Admin Account
Run our automated database seeder to populate MongoDB with categories (*Mobiles, Electronics, Fashion*), top brands (*Apple, Samsung, Sony, Nike*), demo products, promo coupons, and an admin account:

```bash
python run.py seed
```

**Default Admin Credentials:**
* **Email:** `admin@fancystore.in`
* **Password:** `AdminPassword@2026`

### 5. Run the Application Server
Start the development server:
```bash
python run.py
```
Open your web browser and navigate to: **http://localhost:5000**

---

## 🧪 Automated Testing

The project includes an automated integration test suite verifying factory initialization, public storefront rendering, authentication workflows, REST APIs, and RBAC access control redirects.

To execute the test suite:
```bash
python -m unittest discover -v
```

---

## 📄 License & Credits
Developed as a production-ready reference implementation for scalable e-commerce platforms using Python and MongoDB.
"# Online-Fancy-Store-" 
