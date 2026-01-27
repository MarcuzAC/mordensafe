import os
import uuid
from fastapi import UploadFile, HTTPException
from PIL import Image
import io

# Create upload directories
os.makedirs("static/products", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

async def save_product_image(file: UploadFile) -> str:
    """Save product image and return the file path"""
    
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail="Only JPEG, PNG, and WebP images are allowed"
        )
    
    # Validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size too large. Maximum size is 5MB"
        )
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{file_extension}"
    filepath = f"static/products/{filename}"
    
    try:
        # Optimize and save image
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # Resize if too large (max 800px width)
        if image.width > 800:
            ratio = 800 / image.width
            new_height = int(image.height * ratio)
            image = image.resize((800, new_height), Image.Resampling.LANCZOS)
        
        # Save optimized image
        image.save(filepath, "JPEG", quality=85, optimize=True)
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error processing image: {str(e)}"
        )
    
    return f"/static/products/{filename}"

def delete_product_image(image_url: str):
    """Delete product image file"""
    if image_url and image_url.startswith("/static/products/"):
        filename = image_url.split("/")[-1]
        filepath = f"static/products/{filename}"
        if os.path.exists(filepath):
            os.remove(filepath)
