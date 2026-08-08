import datetime
from app.db import mongo

def get_dashboard_kpis():
    """Calculate key performance indicators (KPIs) for Enterprise Admin Dashboard using MongoDB aggregations."""
    orders_col = mongo.get_collection('orders')
    products_col = mongo.get_collection('products')
    users_col = mongo.get_collection('users')
    
    # 1. Total Revenue (sum of grand_total for non-cancelled orders)
    rev_pipeline = [
        {"$match": {"order_status": {"$ne": "Cancelled"}}},
        {"$group": {"_id": None, "total_revenue": {"$sum": {"$ifNull": ["$grand_total", "$billing_summary.grand_total", 0.0]}}}}
    ]
    rev_res = list(orders_col.aggregate(rev_pipeline))
    total_revenue = rev_res[0]['total_revenue'] if rev_res else 0.0

    # 2. Order Counts
    total_orders = orders_col.count_documents({})
    pending_orders = orders_col.count_documents({"order_status": {"$in": ["Pending", "Processing"]}})
    shipped_orders = orders_col.count_documents({"order_status": {"$in": ["Shipped", "Out for Delivery"]}})
    delivered_orders = orders_col.count_documents({"order_status": "Delivered"})

    # 3. Customer & Catalog Counts
    total_customers = users_col.count_documents({})
    total_products = products_col.count_documents({})
    active_products = products_col.count_documents({"status": "active"})
    low_stock_products = products_col.count_documents({"in_stock": True, "stock_quantity": {"$lte": 5}})

    # 4. Recent 7 Days Sales Trend
    seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    trend_pipeline = [
        {"$match": {"created_at": {"$gte": seven_days_ago}, "order_status": {"$ne": "Cancelled"}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "daily_revenue": {"$sum": {"$ifNull": ["$grand_total", "$billing_summary.grand_total", 0.0]}},
                "daily_orders": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    trend_res = list(orders_col.aggregate(trend_pipeline))
    
    dates = []
    revenues = []
    orders_count = []
    
    # Fill missing dates with 0
    for i in range(6, -1, -1):
        day_str = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        dates.append(day_str)
        found = next((item for item in trend_res if item['_id'] == day_str), None)
        if found:
            revenues.append(round(found['daily_revenue'], 2))
            orders_count.append(found['daily_orders'])
        else:
            revenues.append(0.0)
            orders_count.append(0)

    # 5. Top Selling Categories / Products (from order items)
    top_items_pipeline = [
        {"$match": {"order_status": {"$ne": "Cancelled"}}},
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.product_id",
                "name": {"$first": "$items.name"},
                "thumbnail": {"$first": "$items.thumbnail"},
                "total_sold": {"$sum": "$items.quantity"},
                "revenue_generated": {"$sum": "$items.total"}
            }
        },
        {"$sort": {"total_sold": -1}},
        {"$limit": 5}
    ]
    top_selling_items = list(orders_col.aggregate(top_items_pipeline))

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "shipped_orders": shipped_orders,
        "delivered_orders": delivered_orders,
        "total_customers": total_customers,
        "total_products": total_products,
        "active_products": active_products,
        "low_stock_products": low_stock_products,
        "chart_dates": dates,
        "chart_revenues": revenues,
        "chart_orders": orders_count,
        "top_selling_items": top_selling_items
    }
