from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, File, UploadFile, Form
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import List, Optional
import random
from bson import ObjectId
import json
import os
from database import db
from auth import hash_password, verify_password, create_token, verify_token
from models import *
from pdf_generator import generate_receipt

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

# Create upload directories
os.makedirs("static/products", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)

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
        "service_type": request["service_type"],
        "extinguisher_type": request.get("extinguisher_type"),
        "quantity": request.get("quantity", 1),
        "address": request["address"],
        "description": request.get("description"),
        "status": request["status"],
        "quote_amount": request.get("quote_amount"),
        "completion_notes": request.get("completion_notes"),
        "created_at": request.get("created_at")
    }

def product_to_response(product):
    return {
        "id": str(product["_id"]),
        "name": product["name"],
        "description": product["description"],
        "category": product["category"],
        "price": product["price"],
        "stock_quantity": product.get("stock_quantity", 0),
        "images": product.get("images", []),  # Changed from image_url to images array
        "specifications": product.get("specifications", {}),
        "is_available": product.get("is_available", True),
        "created_at": product.get("created_at"),
        "updated_at": product.get("updated_at")
    }

def create_notification(user_id, title, message, request_id=None):
    notification = {
        "user_id": ObjectId(user_id),
        "title": title,
        "message": message,
        "is_read": False,
        "created_at": datetime.utcnow()
    }
    if request_id:
        notification["request_id"] = ObjectId(request_id)
    notifications_db.insert_one(notification)

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
    
    # NOTE: Removed hardcoded sample products
    # Products should now be added through the admin interface

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

# SERVICE REQUEST ENDPOINTS
@app.post("/api/requests")
async def create_request(
    request_data: ServiceRequestCreate,
    user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    request_dict = request_data.dict()
    request_dict["client_id"] = ObjectId(user["_id"])
    request_dict["request_number"] = f"SR{datetime.now().strftime('%Y%m%d')}{random.randint(100, 999)}"
    request_dict["status"] = "pending"
    request_dict["created_at"] = datetime.utcnow()
    
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
async def get_all_requests(admin: dict = Depends(get_current_admin)):
    requests = list(requests_db.find().sort("created_at", -1))
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

# PRODUCT MANAGEMENT ENDPOINTS
@app.post("/api/admin/products")
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    stock_quantity: int = Form(0),
    specifications: str = Form("{}"),
    is_available: bool = Form(True),
    images: List[UploadFile] = File([]),  # Changed to support multiple images
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
        for i, image in enumerate(images[:MAX_IMAGES_PER_PRODUCT]):  # Limit to first 5 images
            if image and image.filename:
                try:
                    image_url = await save_product_image(image)
                    image_urls.append(image_url)
                except HTTPException as e:
                    # Skip invalid images but continue with others
                    print(f"Error uploading image {i+1}: {str(e)}")
                    continue
        
        product_data = {
            "name": name,
            "description": description,
            "category": category,
            "price": price,
            "stock_quantity": stock_quantity,
            "specifications": specs_dict,
            "images": image_urls,  # Store as array
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
    images: List[UploadFile] = File([]),  # Changed to support multiple files
    existing_images: List[str] = Form([]),  # New parameter for keeping existing images
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
    
    # Handle images - combine existing and new images
    image_urls = []
    
    # Add existing images (sent as JSON string from frontend)
    if existing_images:
        if isinstance(existing_images, str):
            # Parse if sent as JSON string
            try:
                existing_images_list = json.loads(existing_images)
                image_urls.extend(existing_images_list)
            except:
                # If not JSON, treat as single string
                image_urls.append(existing_images)
        elif isinstance(existing_images, list):
            image_urls.extend(existing_images)
    
    # Add new images
    for i, image in enumerate(images[:MAX_IMAGES_PER_PRODUCT]):
        if image and image.filename:
            try:
                image_url = await save_product_image(image)
                image_urls.append(image_url)
            except HTTPException as e:
                print(f"Error uploading image {i+1}: {str(e)}")
                continue
    
    # Remove duplicates and limit to MAX_IMAGES_PER_PRODUCT
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

# NOTIFICATIONS
@app.get("/api/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    notifications = list(notifications_db.find(
        {"user_id": ObjectId(user["_id"])}
    ).sort("created_at", -1).limit(50))
    
    # Convert to response
    result = []
    for notif in notifications:
        result.append({
            "id": str(notif["_id"]),
            "title": notif["title"],
            "message": notif["message"],
            "is_read": notif.get("is_read", False),
            "created_at": notif.get("created_at")
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

# PDF RECEIPTS
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

# ADMIN STATS
@app.get("/api/admin/stats")
async def get_admin_stats(admin: dict = Depends(get_current_admin)):
    total_requests = requests_db.count_documents({})
    pending_requests = requests_db.count_documents({"status": "pending"})
    total_clients = users_db.count_documents({"role": "client"})
    total_products = products_db.count_documents({})
    low_stock_products = products_db.count_documents({"stock_quantity": {"$lt": 10}})
    
    return {
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "total_clients": total_clients,
        "total_products": total_products,
        "low_stock_products": low_stock_products
    }

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