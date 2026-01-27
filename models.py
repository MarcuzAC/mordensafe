from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENT = "client"

class ServiceType(str, Enum):
    NEW_PURCHASE = "new_purchase"
    REFILL = "refill"
    MAINTENANCE = "maintenance"
    INSPECTION = "inspection"

class ServiceStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Request/Response Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str
    role: UserRole = UserRole.CLIENT

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    phone: str
    role: UserRole
    created_at: datetime

class ServiceRequestCreate(BaseModel):
    service_type: ServiceType
    extinguisher_type: Optional[str] = None
    quantity: int = 1
    address: str
    description: Optional[str] = None

class ServiceRequestUpdate(BaseModel):
    status: Optional[ServiceStatus] = None
    quote_amount: Optional[float] = None
    completion_notes: Optional[str] = None

class ServiceRequestResponse(BaseModel):
    id: str
    request_number: str
    client_id: str
    service_type: ServiceType
    extinguisher_type: Optional[str]
    quantity: int
    address: str
    description: Optional[str]
    status: ServiceStatus
    quote_amount: Optional[float]
    completion_notes: Optional[str]
    created_at: datetime

class ProductCategory(str, Enum):
    FIRE_EXTINGUISHERS = "fire_extinguishers"
    SAFETY_EQUIPMENT = "safety_equipment"
    ACCESSORIES = "accessories"
    MAINTENANCE_KITS = "maintenance_kits"

class ProductCreate(BaseModel):
    name: str
    description: str
    category: ProductCategory
    price: float = Field(..., gt=0)
    stock_quantity: int = Field(default=0, ge=0)
    image_url: Optional[str] = None
    specifications: Optional[dict] = None
    is_available: bool = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    specifications: Optional[dict] = None
    is_available: Optional[bool] = None

class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    category: ProductCategory
    price: float
    stock_quantity: int
    image_url: Optional[str]
    specifications: Optional[dict]
    is_available: bool
    created_at: datetime
    updated_at: datetime

