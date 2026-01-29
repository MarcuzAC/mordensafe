from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, File, UploadFile, Form
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
from typing import List, Optional
import random
from bson import ObjectId
import json
import os
from database import db
from auth import hash_password, verify_password, create_token, verify_token
from models import *
from pdf_generator import generate_receipt, generate_order_invoice

app = FastAPI(title="Morden Safety Management System")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Security
security = HTTPBearer()

# Collections
users_db = db.get_collection("users")
requests_db = db.get_collection("service_requests")
notifications_db = db.get_collection("notifications")
products_db = db.get_collection("products")
orders_db = db.get_collection("orders")
order_items_db = db.get_collection("order_items")
transactions_db = db.get_collection("transactions")
expenses_db = db.get_collection("expenses")

# Create upload directories
os.makedirs("static/products", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/receipts", exist_ok=True)
os.makedirs("static/invoices", exist_ok=True)

# Dependency to get current user
async def get_current_user(credentials: str = Depends(security)):
    token = credentials.credentials
    email = verify_token(token)
    user = users_db.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_current_admin(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def get_current_client(user: dict = Depends(get_current_user)):
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Client access required")
    return user

# Helper functions
def user_to_response(user):
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "full_name": user["full_name"],
        "phone": user["phone"],
        "role": user["role"],
        "created_at": user.get("created_at")
    }

def request_to_response(request):
    return {
        "id": str(request["_id"]),
        "request_number": request["request_number"],
        "client_id": str(request["client_id"]),
        "client_name": request.get("client_name"),
        "service_type": request["service_type"],
        "extinguisher_type": request.get("extinguisher_type"),
        "quantity": request.get("quantity", 1),
        "address": request["address"],
        "description": request.get("description"),
        "status": request["status"],
        "quote_amount": request.get("quote_amount"),
        "completion_notes": request.get("completion_notes"),
        "assigned_to": str(request.get("assigned_to")) if request.get("assigned_to") else None,
        "assigned_to_name": request.get("assigned_to_name"),
        "created_at": request.get("created_at"),
        "updated_at": request.get("updated_at"),
        "completed_at": request.get("completed_at")
    }

def product_to_response(product):
    return {
        "id": str(product["_id"]),
        "name": product["name"],
        "description": product["description"],
        "category": product["category"],
        "price": product["price"],
        "stock_quantity": product.get("stock_quantity", 0),
        "images": product.get("images", []),
        "specifications": product.get("specifications", {}),
        "is_available": product.get("is_available", True),
        "created_at": product.get("created_at"),
        "updated_at": product.get("updated_at")
    }

def order_to_response(order):
    response = {
        "id": str(order["_id"]),
        "order_number": order["order_number"],
        "client_id": str(order["client_id"]),
        "client_name": order.get("client_name"),
        "client_email": order.get("client_email"),
        "client_phone": order.get("client_phone"),
        "status": order["status"],
        "subtotal": order["subtotal"],
        "tax": order.get("tax", 0),
        "shipping_fee": order.get("shipping_fee", 0),
        "total_amount": order["total_amount"],
        "payment_method": order.get("payment_method"),
        "payment_status": order.get("payment_status", "pending"),
        "shipping_address": order.get("shipping_address"),
        "billing_address": order.get("billing_address"),
        "notes": order.get("notes"),
        "created_at": order.get("created_at"),
        "updated_at": order.get("updated_at"),
        "items_count": order.get("items_count", 0),
        "items": []
    }
    
    # Get order items if needed
    if "items" in order:
        response["items"] = order["items"]
    
    return response

def order_item_to_response(item):
    return {
        "id": str(item["_id"]),
        "order_id": str(item["order_id"]),
        "product_id": str(item["product_id"]),
        "product_name": item.get("product_name"),
        "product_image": item.get("product_image"),
        "quantity": item["quantity"],
        "unit_price": item["unit_price"],
        "total_price": item["total_price"],
        "created_at": item.get("created_at")
    }

def transaction_to_response(transaction):
    return {
        "id": str(transaction["_id"]),
        "transaction_number": transaction["transaction_number"],
        "order_id": str(transaction.get("order_id")) if transaction.get("order_id") else None,
        "request_id": str(transaction.get("request_id")) if transaction.get("request_id") else None,
        "type": transaction["type"],  # 'order_payment', 'service_payment', 'expense', 'refund'
        "amount": transaction["amount"],
        "payment_method": transaction.get("payment_method"),
        "status": transaction.get("status", "completed"),
        "description": transaction.get("description"),
        "client_id": str(transaction.get("client_id")) if transaction.get("client_id") else None,
        "client_name": transaction.get("client_name"),
        "admin_id": str(transaction.get("admin_id")) if transaction.get("admin_id") else None,
        "admin_name": transaction.get("admin_name"),
        "created_at": transaction.get("created_at"),
        "processed_at": transaction.get("processed_at")
    }

def expense_to_response(expense):
    return {
        "id": str(expense["_id"]),
        "expense_number": expense["expense_number"],
        "category": expense["category"],
        "amount": expense["amount"],
        "description": expense["description"],
        "receipt_image": expense.get("receipt_image"),
        "status": expense.get("status", "approved"),
        "approved_by": str(expense.get("approved_by")) if expense.get("approved_by") else None,
        "approved_by_name": expense.get("approved_by_name"),
        "created_at": expense.get("created_at"),
        "updated_at": expense.get("updated_at")
    }

def create_notification(user_id, title, message, request_id=None, order_id=None):
    notification = {
        "user_id": ObjectId(user_id),
        "title": title,
        "message": message,
        "is_read": False,
        "created_at": datetime.utcnow()
    }
    if request_id:
        notification["request_id"] = ObjectId(request_id)
    if order_id:
        notification["order_id"] = ObjectId(order_id)
    notifications_db.insert_one(notification)

def generate_order_number():
    date_str = datetime.now().strftime('%Y%m%d')
    count_today = orders_db.count_documents({
        "order_number": {"$regex": f"^ORD{date_str}"}
    }) + 1
    return f"ORD{date_str}{str(count_today).zfill(4)}"

def generate_transaction_number():
    date_str = datetime.now().strftime('%Y%m%d')
    count_today = transactions_db.count_documents({
        "transaction_number": {"$regex": f"^TXN{date_str}"}
    }) + 1
    return f"TXN{date_str}{str(count_today).zfill(4)}"

def generate_expense_number():
    date_str = datetime.now().strftime('%Y%m%d')
    count_today = expenses_db.count_documents({
        "expense_number": {"$regex": f"^EXP{date_str}"}
    }) + 1
    return f"EXP{date_str}{str(count_today).zfill(4)}"

# File upload utility functions
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGES_PER_PRODUCT = 5

async def save_product_image(file: UploadFile) -> str:
    """Save product image and return the file path"""
    
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file.content_type} not allowed. Only JPEG, PNG, and WebP are supported"
        )
    
    # Validate file size
    contents = await file.read()
    await file.seek(0)  # Reset file pointer for future reads
    
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size {len(contents)/1024/1024:.1f}MB too large. Maximum size is 5MB"
        )
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1].lower()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_num = random.randint(1000, 9999)
    filename = f"product_{timestamp}_{random_num}.{file_extension}"
    filepath = f"static/products/{filename}"
    
    try:
        # Save file
        with open(filepath, "wb") as f:
            f.write(contents)
        
        return f"/static/products/{filename}"
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error saving image: {str(e)}"
        )

def delete_product_image(image_url: str):
    """Delete product image file"""
    if image_url and image_url.startswith("/static/products/"):
        filename = image_url.split("/")[-1]
        filepath = f"static/products/{filename}"
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error deleting image {filepath}: {str(e)}")

async def save_receipt_image(file: UploadFile) -> str:
    """Save expense receipt image and return the file path"""
    
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file.content_type} not allowed. Only JPEG, PNG, and WebP are supported"
        )
    
    contents = await file.read()
    await file.seek(0)
    
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size {len(contents)/1024/1024:.1f}MB too large. Maximum size is 5MB"
        )
    
    file_extension = file.filename.split('.')[-1].lower()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_num = random.randint(1000, 9999)
    filename = f"expense_{timestamp}_{random_num}.{file_extension}"
    filepath = f"static/uploads/{filename}"
    
    try:
        with open(filepath, "wb") as f:
            f.write(contents)
        
        return f"/static/uploads/{filename}"
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error saving receipt: {str(e)}"
        )

# Create default admin on startup
@app.on_event("startup")
async def startup():
    admin = users_db.find_one({"email": "admin@firesafety.mw"})
    if not admin:
        users_db.insert_one({
            "email": "admin@firesafety.mw",
            "password": hash_password("admin123"),
            "full_name": "System Administrator",
            "phone": "0999756168",
            "role": "admin",
            "created_at": datetime.utcnow()
        })
        print("✅ Default admin created: admin@firesafety.mw / admin123")

# AUTH ENDPOINTS
@app.post("/api/auth/register")
async def register(user_data: UserCreate):
    if users_db.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = user_data.dict()
    user_dict["password"] = hash_password(user_dict["password"])
    user_dict["created_at"] = datetime.utcnow()
    
    result = users_db.insert_one(user_dict)
    user = users_db.find_one({"_id": result.inserted_id})
    
    token = create_token(user["email"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_to_response(user)
    }

@app.post("/api/auth/login")
async def login(login_data: UserLogin):
    user = users_db.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["email"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_to_response(user)
    }

@app.get("/api/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user_to_response(user)

# ORDER MANAGEMENT ENDPOINTS
@app.post("/api/orders/checkout")
async def checkout_order(
    order_data: OrderCreate,
    user: dict = Depends(get_current_client),
    background_tasks: BackgroundTasks = None
):
    """Create an order from cart checkout"""
    
    # Validate stock availability and calculate totals
    subtotal = 0
    items_data = []
    
    for item in order_data.items:
        product = products_db.find_one({"_id": ObjectId(item.product_id)})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        
        if not product.get("is_available", True):
            raise HTTPException(status_code=400, detail=f"Product {product['name']} is not available")
        
        if product.get("stock_quantity", 0) < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product['name']}")
        
        item_total = product["price"] * item.quantity
        subtotal += item_total
        
        items_data.append({
            "product_id": ObjectId(item.product_id),
            "product_name": product["name"],
            "product_image": product.get("images", [None])[0] if product.get("images") else None,
            "quantity": item.quantity,
            "unit_price": product["price"],
            "total_price": item_total
        })
    
    # Calculate totals
    tax = subtotal * 0.16  # 16% VAT (adjust as needed)
    shipping_fee = order_data.shipping_fee or 0
    total_amount = subtotal + tax + shipping_fee
    
    # Create order
    order_dict = {
        "order_number": generate_order_number(),
        "client_id": ObjectId(user["_id"]),
        "client_name": user["full_name"],
        "client_email": user["email"],
        "client_phone": user["phone"],
        "status": "pending",
        "subtotal": subtotal,
        "tax": tax,
        "shipping_fee": shipping_fee,
        "total_amount": total_amount,
        "payment_method": order_data.payment_method,
        "payment_status": "pending",
        "shipping_address": order_data.shipping_address,
        "billing_address": order_data.billing_address or order_data.shipping_address,
        "notes": order_data.notes,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "items_count": len(items_data)
    }
    
    # Start transaction
    result = orders_db.insert_one(order_dict)
    order_id = result.inserted_id
    
    # Create order items and update stock
    for item_data in items_data:
        item_data["order_id"] = order_id
        item_data["created_at"] = datetime.utcnow()
        order_items_db.insert_one(item_data)
        
        # Reduce stock quantity
        products_db.update_one(
            {"_id": item_data["product_id"]},
            {"$inc": {"stock_quantity": -item_data["quantity"]}}
        )
    
    # Get complete order with items
    order = orders_db.find_one({"_id": order_id})
    order["items"] = items_data
    
    # Notify all admins
    admins = users_db.find({"role": "admin"})
    for admin in admins:
        create_notification(
            str(admin["_id"]),
            "New Order Placed",
            f"New order #{order['order_number']} from {user['full_name']}",
            order_id=str(order_id)
        )
    
    # Optionally process payment here if using payment gateway
    
    return {
        "success": True, 
        "order": order_to_response(order),
        "message": "Order placed successfully. Admin will process it shortly."
    }

@app.get("/api/orders/my-orders")
async def get_my_orders(user: dict = Depends(get_current_client)):
    """Get all orders for the current client"""
    orders = list(orders_db.find({"client_id": ObjectId(user["_id"])}).sort("created_at", -1))
    
    # Add items to each order
    orders_with_items = []
    for order in orders:
        items = list(order_items_db.find({"order_id": order["_id"]}))
        order["items"] = [order_item_to_response(item) for item in items]
        orders_with_items.append(order_to_response(order))
    
    return {"orders": orders_with_items}

@app.get("/api/orders/{order_id}")
async def get_order(order_id: str, user: dict = Depends(get_current_user)):
    """Get order details"""
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")
    
    order = orders_db.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check permissions
    if user["role"] == "client" and str(order["client_id"]) != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get order items
    items = list(order_items_db.find({"order_id": ObjectId(order_id)}))
    order["items"] = [order_item_to_response(item) for item in items]
    
    return {"order": order_to_response(order)}

@app.get("/api/orders")
async def get_all_orders(
    status: str = None,
    start_date: str = None,
    end_date: str = None,
    page: int = 1,
    limit: int = 20,
    admin: dict = Depends(get_current_admin)
):
    """Get all orders (admin only)"""
    query = {}
    
    if status:
        query["status"] = status
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query["created_at"] = {"$gte": start_dt}
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if "created_at" in query:
                query["created_at"]["$lte"] = end_dt
            else:
                query["created_at"] = {"$lte": end_dt}
        except:
            pass
    
    skip = (page - 1) * limit
    orders = list(orders_db.find(query).sort("created_at", -1).skip(skip).limit(limit))
    total = orders_db.count_documents(query)
    
    # Add items to each order
    orders_with_items = []
    for order in orders:
        items = list(order_items_db.find({"order_id": order["_id"]}))
        order["items"] = [order_item_to_response(item) for item in items]
        orders_with_items.append(order_to_response(order))
    
    return {
        "orders": orders_with_items,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@app.put("/api/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update order status (admin only)"""
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")
    
    order = orders_db.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    update_data = {
        "status": status_update.status,
        "updated_at": datetime.utcnow()
    }
    
    if status_update.status == "completed" and status_update.completion_notes:
        update_data["completion_notes"] = status_update.completion_notes
        update_data["completed_at"] = datetime.utcnow()
    
    # If order is cancelled, restore stock
    if status_update.status == "cancelled" and order["status"] != "cancelled":
        items = list(order_items_db.find({"order_id": ObjectId(order_id)}))
        for item in items:
            products_db.update_one(
                {"_id": item["product_id"]},
                {"$inc": {"stock_quantity": item["quantity"]}}
            )
    
    orders_db.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": update_data}
    )
    
    # Notify client
    create_notification(
        str(order["client_id"]),
        "Order Status Updated",
        f"Your order #{order['order_number']} is now {status_update.status}",
        order_id=order_id
    )
    
    # Record transaction if order is completed and paid
    if status_update.status == "completed" and order["payment_status"] == "paid":
        transaction = {
            "transaction_number": generate_transaction_number(),
            "order_id": ObjectId(order_id),
            "type": "order_payment",
            "amount": order["total_amount"],
            "payment_method": order.get("payment_method"),
            "status": "completed",
            "description": f"Payment for order #{order['order_number']}",
            "client_id": order["client_id"],
            "client_name": order.get("client_name"),
            "created_at": datetime.utcnow(),
            "processed_at": datetime.utcnow()
        }
        transactions_db.insert_one(transaction)
    
    return {"success": True, "message": f"Order status updated to {status_update.status}"}

@app.put("/api/orders/{order_id}/payment")
async def update_payment_status(
    order_id: str,
    payment_update: PaymentStatusUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update payment status (admin only)"""
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")
    
    order = orders_db.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    update_data = {
        "payment_status": payment_update.payment_status,
        "updated_at": datetime.utcnow()
    }
    
    orders_db.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": update_data}
    )
    
    # Record transaction if payment is marked as paid
    if payment_update.payment_status == "paid":
        transaction = {
            "transaction_number": generate_transaction_number(),
            "order_id": ObjectId(order_id),
            "type": "order_payment",
            "amount": order["total_amount"],
            "payment_method": order.get("payment_method"),
            "status": "completed",
            "description": f"Payment received for order #{order['order_number']}",
            "client_id": order["client_id"],
            "client_name": order.get("client_name"),
            "admin_id": ObjectId(admin["_id"]),
            "admin_name": admin["full_name"],
            "created_at": datetime.utcnow(),
            "processed_at": datetime.utcnow()
        }
        transactions_db.insert_one(transaction)
    
    # Notify client
    create_notification(
        str(order["client_id"]),
        "Payment Status Updated",
        f"Payment for order #{order['order_number']} is now {payment_update.payment_status}",
        order_id=order_id
    )
    
    return {"success": True, "message": f"Payment status updated to {payment_update.payment_status}"}

@app.get("/api/orders/{order_id}/invoice")
async def get_order_invoice(order_id: str, user: dict = Depends(get_current_user)):
    """Generate and download order invoice"""
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")
    
    order = orders_db.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check permissions
    if user["role"] == "client" and str(order["client_id"]) != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get order items
    items = list(order_items_db.find({"order_id": ObjectId(order_id)}))
    order["items"] = [order_item_to_response(item) for item in items]
    
    # Get client info
    client = users_db.find_one({"_id": order["client_id"]})
    
    # Generate invoice PDF
    filepath = generate_order_invoice(order_to_response(order), user_to_response(client))
    filename = filepath.split("/")[-1]
    
    return {"invoice_url": f"/static/invoices/{filename}"}

# TRANSACTION MANAGEMENT
@app.get("/api/transactions")
async def get_transactions(
    type: str = None,
    start_date: str = None,
    end_date: str = None,
    page: int = 1,
    limit: int = 20,
    admin: dict = Depends(get_current_admin)
):
    """Get all transactions (admin only)"""
    query = {}
    
    if type:
        query["type"] = type
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query["created_at"] = {"$gte": start_dt}
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if "created_at" in query:
                query["created_at"]["$lte"] = end_dt
            else:
                query["created_at"] = {"$lte": end_dt}
        except:
            pass
    
    skip = (page - 1) * limit
    transactions = list(transactions_db.find(query).sort("created_at", -1).skip(skip).limit(limit))
    total = transactions_db.count_documents(query)
    
    return {
        "transactions": [transaction_to_response(t) for t in transactions],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@app.get("/api/transactions/revenue-summary")
async def get_revenue_summary(
    period: str = "month",  # day, week, month, year
    admin: dict = Depends(get_current_admin)
):
    """Get revenue summary for dashboard (admin only)"""
    from datetime import timedelta
    
    now = datetime.utcnow()
    
    if period == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=now.weekday())
    elif period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # year
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get order revenue
    order_pipeline = [
        {"$match": {
            "type": "order_payment",
            "status": "completed",
            "created_at": {"$gte": start_date}
        }},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$amount"},
            "transaction_count": {"$sum": 1}
        }}
    ]
    
    order_result = list(transactions_db.aggregate(order_pipeline))
    order_revenue = order_result[0]["total_revenue"] if order_result else 0
    order_count = order_result[0]["transaction_count"] if order_result else 0
    
    # Get service revenue
    service_pipeline = [
        {"$match": {
            "type": "service_payment",
            "status": "completed",
            "created_at": {"$gte": start_date}
        }},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$amount"},
            "transaction_count": {"$sum": 1}
        }}
    ]
    
    service_result = list(transactions_db.aggregate(service_pipeline))
    service_revenue = service_result[0]["total_revenue"] if service_result else 0
    service_count = service_result[0]["transaction_count"] if service_result else 0
    
    # Get expenses
    expense_pipeline = [
        {"$match": {
            "created_at": {"$gte": start_date}
        }},
        {"$group": {
            "_id": None,
            "total_expenses": {"$sum": "$amount"},
            "expense_count": {"$sum": 1}
        }}
    ]
    
    expense_result = list(expenses_db.aggregate(expense_pipeline))
    total_expenses = expense_result[0]["total_expenses"] if expense_result else 0
    expense_count = expense_result[0]["expense_count"] if expense_result else 0
    
    # Get net profit
    total_revenue = order_revenue + service_revenue
    net_profit = total_revenue - total_expenses
    
    return {
        "period": period,
        "total_revenue": total_revenue,
        "order_revenue": order_revenue,
        "service_revenue": service_revenue,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "order_count": order_count,
        "service_count": service_count,
        "expense_count": expense_count,
        "start_date": start_date,
        "end_date": now
    }

# EXPENSE MANAGEMENT
@app.post("/api/expenses")
async def create_expense(
    category: str = Form(...),
    amount: float = Form(...),
    description: str = Form(...),
    status: str = Form("pending"),
    receipt_image: UploadFile = File(None),
    admin: dict = Depends(get_current_admin)
):
    """Create new expense (admin only)"""
    
    expense_data = {
        "expense_number": generate_expense_number(),
        "category": category,
        "amount": amount,
        "description": description,
        "status": status,
        "approved_by": ObjectId(admin["_id"]),
        "approved_by_name": admin["full_name"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Save receipt image if provided
    if receipt_image and receipt_image.filename:
        receipt_url = await save_receipt_image(receipt_image)
        expense_data["receipt_image"] = receipt_url
    
    result = expenses_db.insert_one(expense_data)
    expense = expenses_db.find_one({"_id": result.inserted_id})
    
    # Record transaction for expense
    transaction = {
        "transaction_number": generate_transaction_number(),
        "type": "expense",
        "amount": amount,
        "status": "completed",
        "description": f"Expense: {category} - {description}",
        "admin_id": ObjectId(admin["_id"]),
        "admin_name": admin["full_name"],
        "created_at": datetime.utcnow(),
        "processed_at": datetime.utcnow()
    }
    transactions_db.insert_one(transaction)
    
    return {"success": True, "expense": expense_to_response(expense)}

@app.get("/api/expenses")
async def get_expenses(
    category: str = None,
    status: str = None,
    start_date: str = None,
    end_date: str = None,
    page: int = 1,
    limit: int = 20,
    admin: dict = Depends(get_current_admin)
):
    """Get all expenses (admin only)"""
    query = {}
    
    if category:
        query["category"] = category
    
    if status:
        query["status"] = status
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query["created_at"] = {"$gte": start_dt}
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if "created_at" in query:
                query["created_at"]["$lte"] = end_dt
            else:
                query["created_at"] = {"$lte": end_dt}
        except:
            pass
    
    skip = (page - 1) * limit
    expenses = list(expenses_db.find(query).sort("created_at", -1).skip(skip).limit(limit))
    total = expenses_db.count_documents(query)
    
    return {
        "expenses": [expense_to_response(expense) for expense in expenses],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@app.put("/api/expenses/{expense_id}")
async def update_expense(
    expense_id: str,
    category: str = Form(None),
    amount: float = Form(None),
    description: str = Form(None),
    status: str = Form(None),
    receipt_image: UploadFile = File(None),
    admin: dict = Depends(get_current_admin)
):
    """Update expense (admin only)"""
    if not ObjectId.is_valid(expense_id):
        raise HTTPException(status_code=400, detail="Invalid expense ID")
    
    expense = expenses_db.find_one({"_id": ObjectId(expense_id)})
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    update_data = {"updated_at": datetime.utcnow()}
    
    if category is not None:
        update_data["category"] = category
    
    if amount is not None:
        update_data["amount"] = amount
    
    if description is not None:
        update_data["description"] = description
    
    if status is not None:
        update_data["status"] = status
    
    # Handle receipt image
    if receipt_image and receipt_image.filename:
        # Delete old receipt if exists
        if expense.get("receipt_image"):
            old_receipt = expense["receipt_image"]
            if old_receipt.startswith("/static/uploads/"):
                filename = old_receipt.split("/")[-1]
                filepath = f"static/uploads/{filename}"
                if os.path.exists(filepath):
                    os.remove(filepath)
        
        # Save new receipt
        receipt_url = await save_receipt_image(receipt_image)
        update_data["receipt_image"] = receipt_url
    
    expenses_db.update_one(
        {"_id": ObjectId(expense_id)},
        {"$set": update_data}
    )
    
    # Update transaction if amount changed
    if amount is not None and amount != expense["amount"]:
        transactions_db.update_one(
            {"type": "expense", "description": f"Expense: {expense['category']} - {expense['description']}"},
            {"$set": {"amount": amount}}
        )
    
    updated_expense = expenses_db.find_one({"_id": ObjectId(expense_id)})
    return {"success": True, "expense": expense_to_response(updated_expense)}

@app.delete("/api/expenses/{expense_id}")
async def delete_expense(expense_id: str, admin: dict = Depends(get_current_admin)):
    """Delete expense (admin only)"""
    if not ObjectId.is_valid(expense_id):
        raise HTTPException(status_code=400, detail="Invalid expense ID")
    
    expense = expenses_db.find_one({"_id": ObjectId(expense_id)})
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Delete receipt image
    if expense.get("receipt_image"):
        receipt_url = expense["receipt_image"]
        if receipt_url.startswith("/static/uploads/"):
            filename = receipt_url.split("/")[-1]
            filepath = f"static/uploads/{filename}"
            if os.path.exists(filepath):
                os.remove(filepath)
    
    # Delete related transaction
    transactions_db.delete_one({
        "type": "expense",
        "description": f"Expense: {expense['category']} - {expense['description']}"
    })
    
    # Delete expense
    expenses_db.delete_one({"_id": ObjectId(expense_id)})
    
    return {"success": True, "message": "Expense deleted successfully"}

# Update Service Request to include payment tracking
@app.put("/api/requests/{request_id}/quote")
async def update_request_quote(
    request_id: str,
    quote_amount: float,
    admin: dict = Depends(get_current_admin)
):
    """Update service request quote amount (admin only)"""
    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID")
    
    request = requests_db.find_one({"_id": ObjectId(request_id)})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    requests_db.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"quote_amount": quote_amount, "updated_at": datetime.utcnow()}}
    )
    
    # Notify client
    create_notification(
        str(request["client_id"]),
        "Service Quote Updated",
        f"Your request #{request['request_number']} has a quote of MK {quote_amount:,.2f}",
        request_id=request_id
    )
    
    return {"success": True, "message": "Quote amount updated"}

@app.put("/api/requests/{request_id}/complete-payment")
async def complete_service_payment(
    request_id: str,
    payment_method: str,
    amount: float,
    admin: dict = Depends(get_current_admin)
):
    """Record service payment completion (admin only)"""
    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID")
    
    request = requests_db.find_one({"_id": ObjectId(request_id)})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Record transaction
    transaction = {
        "transaction_number": generate_transaction_number(),
        "request_id": ObjectId(request_id),
        "type": "service_payment",
        "amount": amount,
        "payment_method": payment_method,
        "status": "completed",
        "description": f"Payment for service request #{request['request_number']}",
        "client_id": request["client_id"],
        "client_name": request.get("client_name"),
        "admin_id": ObjectId(admin["_id"]),
        "admin_name": admin["full_name"],
        "created_at": datetime.utcnow(),
        "processed_at": datetime.utcnow()
    }
    transactions_db.insert_one(transaction)
    
    # Update request status
    requests_db.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {
            "status": "completed",
            "updated_at": datetime.utcnow(),
            "completed_at": datetime.utcnow()
        }}
    )
    
    return {"success": True, "message": "Service payment recorded and request completed"}

# Enhanced ADMIN STATS
@app.get("/api/admin/stats")
async def get_admin_stats(
    start_date: str = None,
    end_date: str = None,
    admin: dict = Depends(get_current_admin)
):
    """Get comprehensive admin statistics"""
    
    date_filter = {}
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            date_filter["$gte"] = start_dt
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            date_filter["$lte"] = end_dt
        except:
            pass
    
    # Counts
    total_requests = requests_db.count_documents({})
    pending_requests = requests_db.count_documents({"status": "pending"})
    total_clients = users_db.count_documents({"role": "client"})
    total_products = products_db.count_documents({})
    low_stock_products = products_db.count_documents({"stock_quantity": {"$lt": 10}})
    total_orders = orders_db.count_documents({})
    pending_orders = orders_db.count_documents({"status": "pending"})
    
    # Revenue calculations
    revenue_pipeline = [
        {"$match": {"type": {"$in": ["order_payment", "service_payment"]}, "status": "completed"}},
        {"$group": {
            "_id": "$type",
            "total": {"$sum": "$amount"}
        }}
    ]
    
    revenue_result = list(transactions_db.aggregate(revenue_pipeline))
    total_revenue = sum(item["total"] for item in revenue_result)
    order_revenue = next((item["total"] for item in revenue_result if item["_id"] == "order_payment"), 0)
    service_revenue = next((item["total"] for item in revenue_result if item["_id"] == "service_payment"), 0)
    
    # Expenses
    expenses_pipeline = [
        {"$group": {
            "_id": None,
            "total_expenses": {"$sum": "$amount"}
        }}
    ]
    
    expenses_result = list(expenses_db.aggregate(expenses_pipeline))
    total_expenses = expenses_result[0]["total_expenses"] if expenses_result else 0
    
    # Net profit
    net_profit = total_revenue - total_expenses
    
    # Recent orders
    recent_orders = list(orders_db.find().sort("created_at", -1).limit(5))
    
    # Recent requests
    recent_requests = list(requests_db.find().sort("created_at", -1).limit(5))
    
    # Sales trends (last 7 days)
    seven_days_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6)
    
    daily_sales = []
    for i in range(7):
        day_start = seven_days_ago + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        day_sales = transactions_db.aggregate([
            {"$match": {
                "type": {"$in": ["order_payment", "service_payment"]},
                "status": "completed",
                "created_at": {"$gte": day_start, "$lt": day_end}
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$amount"}
            }}
        ])
        
        day_sales_list = list(day_sales)
        total = day_sales_list[0]["total"] if day_sales_list else 0
        
        daily_sales.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "total": total
        })
    
    return {
        "counts": {
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "total_clients": total_clients,
            "total_products": total_products,
            "low_stock_products": low_stock_products,
            "total_orders": total_orders,
            "pending_orders": pending_orders
        },
        "financials": {
            "total_revenue": total_revenue,
            "order_revenue": order_revenue,
            "service_revenue": service_revenue,
            "total_expenses": total_expenses,
            "net_profit": net_profit
        },
        "recent_orders": [order_to_response(order) for order in recent_orders],
        "recent_requests": [request_to_response(req) for req in recent_requests],
        "sales_trends": {
            "period": "7_days",
            "daily_sales": daily_sales
        }
    }

# Keep existing endpoints (they remain the same as in your original code)
# SERVICE REQUEST ENDPOINTS (existing)
@app.post("/api/requests")
async def create_request(
    request_data: ServiceRequestCreate,
    user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    request_dict = request_data.dict()
    request_dict["client_id"] = ObjectId(user["_id"])
    request_dict["client_name"] = user["full_name"]
    request_dict["request_number"] = f"SR{datetime.now().strftime('%Y%m%d')}{random.randint(100, 999)}"
    request_dict["status"] = "pending"
    request_dict["created_at"] = datetime.utcnow()
    request_dict["updated_at"] = datetime.utcnow()
    
    result = requests_db.insert_one(request_dict)
    service_request = requests_db.find_one({"_id": result.inserted_id})
    
    # Notify admin
    admins = users_db.find({"role": "admin"})
    for admin in admins:
        create_notification(
            str(admin["_id"]),
            "New Service Request",
            f"New {request_data.service_type} request from {user['full_name']}",
            str(service_request["_id"])
        )
    
    return {"success": True, "request": request_to_response(service_request)}

@app.get("/api/requests/my-requests")
async def get_my_requests(user: dict = Depends(get_current_user)):
    requests = list(requests_db.find({"client_id": ObjectId(user["_id"])}).sort("created_at", -1))
    return {"requests": [request_to_response(req) for req in requests]}

@app.get("/api/requests")
async def get_all_requests(
    status: str = None,
    admin: dict = Depends(get_current_admin)
):
    query = {}
    if status:
        query["status"] = status
    
    requests = list(requests_db.find(query).sort("created_at", -1))
    return {"requests": [request_to_response(req) for req in requests]}

@app.put("/api/requests/{request_id}")
async def update_request(
    request_id: str,
    update_data: ServiceRequestUpdate,
    admin: dict = Depends(get_current_admin)
):
    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    if update_data.status == "completed" and not update_dict.get("completed_at"):
        update_dict["completed_at"] = datetime.utcnow()
    
    requests_db.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": update_dict}
    )
    
    updated_request = requests_db.find_one({"_id": ObjectId(request_id)})
    
    # Notify client about status change
    if update_data.status:
        create_notification(
            str(updated_request["client_id"]),
            "Request Status Updated",
            f"Your request #{updated_request['request_number']} is now {update_data.status}",
            request_id
        )
    
    return {"success": True, "request": request_to_response(updated_request)}

# PRODUCT MANAGEMENT ENDPOINTS (existing - keep as is)
@app.post("/api/admin/products")
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    stock_quantity: int = Form(0),
    specifications: str = Form("{}"),
    is_available: bool = Form(True),
    images: List[UploadFile] = File([]),
    admin: dict = Depends(get_current_admin)
):
    """Create a new product with multiple images (admin only)"""
    try:
        # Parse specifications
        specs_dict = {}
        if specifications and specifications != "{}":
            try:
                specs_dict = json.loads(specifications)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid specifications format")
        
        # Handle image uploads (limit to 5 images)
        image_urls = []
        for i, image in enumerate(images[:MAX_IMAGES_PER_PRODUCT]):
            if image and image.filename:
                try:
                    image_url = await save_product_image(image)
                    image_urls.append(image_url)
                except HTTPException as e:
                    print(f"Error uploading image {i+1}: {str(e)}")
                    continue
        
        product_data = {
            "name": name,
            "description": description,
            "category": category,
            "price": price,
            "stock_quantity": stock_quantity,
            "specifications": specs_dict,
            "images": image_urls,
            "is_available": is_available,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = products_db.insert_one(product_data)
        product = products_db.find_one({"_id": result.inserted_id})
        
        return {"success": True, "product": product_to_response(product)}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/products")
async def get_products(
    category: str = None,
    available_only: bool = True,
    page: int = 1,
    limit: int = 20
):
    """Get all products (available to all users)"""
    query = {}
    
    if category:
        query["category"] = category
    if available_only:
        query["is_available"] = True
    
    skip = (page - 1) * limit
    products = list(products_db.find(query)
                   .sort("created_at", -1)
                   .skip(skip)
                   .limit(limit))
    
    total = products_db.count_documents(query)
    
    return {
        "products": [product_to_response(product) for product in products],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    """Get single product details"""
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = products_db.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"product": product_to_response(product)}

@app.put("/api/admin/products/{product_id}")
async def update_product(
    product_id: str,
    name: str = Form(None),
    description: str = Form(None),
    category: str = Form(None),
    price: float = Form(None),
    stock_quantity: int = Form(None),
    specifications: str = Form(None),
    is_available: bool = Form(None),
    images: List[UploadFile] = File([]),
    existing_images: List[str] = Form([]),
    admin: dict = Depends(get_current_admin)
):
    """Update product with multiple images (admin only)"""
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = products_db.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = {}
    
    # Text fields
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if category is not None:
        update_data["category"] = category
    if price is not None:
        update_data["price"] = price
    if stock_quantity is not None:
        update_data["stock_quantity"] = stock_quantity
    if is_available is not None:
        update_data["is_available"] = is_available
    
    # Specifications
    if specifications is not None and specifications != "{}":
        try:
            update_data["specifications"] = json.loads(specifications)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid specifications format")
    
    # Handle images
    image_urls = []
    
    if existing_images:
        if isinstance(existing_images, str):
            try:
                existing_images_list = json.loads(existing_images)
                image_urls.extend(existing_images_list)
            except:
                image_urls.append(existing_images)
        elif isinstance(existing_images, list):
            image_urls.extend(existing_images)
    
    for i, image in enumerate(images[:MAX_IMAGES_PER_PRODUCT]):
        if image and image.filename:
            try:
                image_url = await save_product_image(image)
                image_urls.append(image_url)
            except HTTPException as e:
                print(f"Error uploading image {i+1}: {str(e)}")
                continue
    
    image_urls = list(dict.fromkeys(image_urls))[:MAX_IMAGES_PER_PRODUCT]
    
    # Delete old images that are no longer needed
    old_images = product.get("images", [])
    for old_image in old_images:
        if old_image not in image_urls:
            delete_product_image(old_image)
    
    update_data["images"] = image_urls
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        products_db.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
    
    updated_product = products_db.find_one({"_id": ObjectId(product_id)})
    return {"success": True, "product": product_to_response(updated_product)}

@app.delete("/api/admin/products/{product_id}")
async def delete_product(product_id: str, admin: dict = Depends(get_current_admin)):
    """Delete product (admin only)"""
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = products_db.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Delete all associated images
    for image_url in product.get("images", []):
        delete_product_image(image_url)
    
    # Delete product
    products_db.delete_one({"_id": ObjectId(product_id)})
    
    return {"success": True, "message": "Product deleted successfully"}

@app.get("/api/admin/products")
async def get_all_products_admin(
    category: str = None,
    page: int = 1,
    limit: int = 20,
    admin: dict = Depends(get_current_admin)
):
    """Get all products with admin privileges (includes unavailable products)"""
    query = {}
    if category:
        query["category"] = category
    
    skip = (page - 1) * limit
    products = list(products_db.find(query)
                   .sort("created_at", -1)
                   .skip(skip)
                   .limit(limit))
    
    total = products_db.count_documents(query)
    
    return {
        "products": [product_to_response(product) for product in products],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

# NOTIFICATIONS (existing)
@app.get("/api/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    notifications = list(notifications_db.find(
        {"user_id": ObjectId(user["_id"])}
    ).sort("created_at", -1).limit(50))
    
    result = []
    for notif in notifications:
        result.append({
            "id": str(notif["_id"]),
            "title": notif["title"],
            "message": notif["message"],
            "is_read": notif.get("is_read", False),
            "created_at": notif.get("created_at"),
            "order_id": str(notif.get("order_id")) if notif.get("order_id") else None,
            "request_id": str(notif.get("request_id")) if notif.get("request_id") else None
        })
    
    return {"notifications": result}

@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(notification_id):
        raise HTTPException(status_code=400, detail="Invalid notification ID")
    
    notifications_db.update_one(
        {"_id": ObjectId(notification_id), "user_id": ObjectId(user["_id"])},
        {"$set": {"is_read": True}}
    )
    
    return {"success": True}

# PDF RECEIPTS (existing)
@app.get("/api/requests/{request_id}/receipt")
async def generate_request_receipt(request_id: str, user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID")
    
    service_request = requests_db.find_one({"_id": ObjectId(request_id)})
    if not service_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check permissions
    if user["role"] == "client" and str(service_request["client_id"]) != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    client = users_db.find_one({"_id": service_request["client_id"]})
    
    filepath = generate_receipt(request_to_response(service_request), user_to_response(client))
    filename = filepath.split("/")[-1]
    
    return {"receipt_url": f"/static/receipts/{filename}"}

# Additional admin endpoints
@app.get("/api/admin/users")
async def get_all_users(admin: dict = Depends(get_current_admin)):
    """Get all users (admin only)"""
    users = list(users_db.find({"role": {"$ne": "admin"}}).sort("created_at", -1))
    return {"users": [user_to_response(user) for user in users]}

# File upload endpoint (optional)
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """General file upload endpoint"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Only image files are allowed")
        
        # Validate file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size too large")
        
        await file.seek(0)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1].lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_num = random.randint(1000, 9999)
        filename = f"upload_{timestamp}_{random_num}.{file_extension}"
        filepath = f"static/uploads/{filename}"
        
        # Save file
        with open(filepath, "wb") as f:
            f.write(contents)
        
        return {"success": True, "file_url": f"/static/uploads/{filename}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Morden Safety System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)