from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

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
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_PAID = "partially_paid"

class PaymentMethod(str, Enum):
    CASH = "cash"
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"

class TransactionType(str, Enum):
    ORDER_PAYMENT = "order_payment"
    SERVICE_PAYMENT = "service_payment"
    EXPENSE = "expense"
    REFUND = "refund"
    OTHER = "other"

class ExpenseCategory(str, Enum):
    OFFICE_SUPPLIES = "office_supplies"
    TRANSPORTATION = "transportation"
    UTILITIES = "utilities"
    SALARIES = "salaries"
    MAINTENANCE = "maintenance"
    MARKETING = "marketing"
    RENT = "rent"
    EQUIPMENT = "equipment"
    OTHER = "other"

class ExpenseStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# Request/Response Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    phone: str
    role: UserRole = UserRole.CLIENT

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: PyObjectId
    email: EmailStr
    full_name: str
    phone: str
    role: UserRole
    created_at: datetime

    class Config:
        json_encoders = {ObjectId: str}

class ServiceRequestCreate(BaseModel):
    service_type: ServiceType
    extinguisher_type: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
    address: str
    description: Optional[str] = None

class ServiceRequestUpdate(BaseModel):
    status: Optional[ServiceStatus] = None
    quote_amount: Optional[float] = Field(None, ge=0)
    completion_notes: Optional[str] = None
    assigned_to: Optional[str] = None

class ServiceRequestResponse(BaseModel):
    id: PyObjectId
    request_number: str
    client_id: PyObjectId
    client_name: Optional[str] = None
    service_type: ServiceType
    extinguisher_type: Optional[str]
    quantity: int
    address: str
    description: Optional[str]
    status: ServiceStatus
    quote_amount: Optional[float]
    completion_notes: Optional[str]
    assigned_to: Optional[PyObjectId] = None
    assigned_to_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        json_encoders = {ObjectId: str}

class ProductCategory(str, Enum):
    FIRE_EXTINGUISHERS = "fire_extinguishers"
    SAFETY_EQUIPMENT = "safety_equipment"
    ACCESSORIES = "accessories"
    MAINTENANCE_KITS = "maintenance_kits"
    OTHER = "other"

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: str
    category: ProductCategory
    price: float = Field(..., gt=0)
    stock_quantity: int = Field(default=0, ge=0)
    images: List[str] = []  # Changed from image_url to images array
    specifications: Optional[Dict[str, str]] = None
    is_available: bool = True

    @validator('images')
    def validate_images(cls, v):
        if len(v) > 5:
            raise ValueError("Maximum 5 images allowed per product")
        return v

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    images: Optional[List[str]] = None
    specifications: Optional[Dict[str, str]] = None
    is_available: Optional[bool] = None

    @validator('images')
    def validate_images(cls, v):
        if v is not None and len(v) > 5:
            raise ValueError("Maximum 5 images allowed per product")
        return v

class ProductResponse(BaseModel):
    id: PyObjectId
    name: str
    description: str
    category: ProductCategory
    price: float
    stock_quantity: int
    images: List[str]
    specifications: Optional[Dict[str, str]]
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {ObjectId: str}

# Order Management Models
class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1)

    @validator('product_id')
    def validate_product_id(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid product ID format")
        return v

class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_items=1)
    shipping_address: str
    billing_address: Optional[str] = None
    payment_method: PaymentMethod
    shipping_fee: float = Field(default=0, ge=0)
    notes: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    completion_notes: Optional[str] = None

class PaymentStatusUpdate(BaseModel):
    payment_status: PaymentStatus
    payment_method: Optional[PaymentMethod] = None
    amount_paid: Optional[float] = Field(None, ge=0)

class OrderResponse(BaseModel):
    id: PyObjectId
    order_number: str
    client_id: PyObjectId
    client_name: str
    client_email: str
    client_phone: str
    status: OrderStatus
    subtotal: float
    tax: float
    shipping_fee: float
    total_amount: float
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    shipping_address: str
    billing_address: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    items_count: int
    items: Optional[List['OrderItemResponse']] = None

    class Config:
        json_encoders = {ObjectId: str}

class OrderItemResponse(BaseModel):
    id: PyObjectId
    order_id: PyObjectId
    product_id: PyObjectId
    product_name: str
    product_image: Optional[str]
    quantity: int
    unit_price: float
    total_price: float
    created_at: datetime

    class Config:
        json_encoders = {ObjectId: str}

# Transaction Models
class TransactionCreate(BaseModel):
    order_id: Optional[str] = None
    request_id: Optional[str] = None
    type: TransactionType
    amount: float = Field(..., gt=0)
    payment_method: Optional[PaymentMethod] = None
    description: Optional[str] = None

    @validator('order_id')
    def validate_order_id(cls, v):
        if v and not ObjectId.is_valid(v):
            raise ValueError("Invalid order ID format")
        return v

    @validator('request_id')
    def validate_request_id(cls, v):
        if v and not ObjectId.is_valid(v):
            raise ValueError("Invalid request ID format")
        return v

class TransactionResponse(BaseModel):
    id: PyObjectId
    transaction_number: str
    order_id: Optional[PyObjectId] = None
    request_id: Optional[PyObjectId] = None
    type: TransactionType
    amount: float
    payment_method: Optional[PaymentMethod]
    status: PaymentStatus
    description: Optional[str]
    client_id: Optional[PyObjectId] = None
    client_name: Optional[str] = None
    admin_id: Optional[PyObjectId] = None
    admin_name: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        json_encoders = {ObjectId: str}

# Expense Models
class ExpenseCreate(BaseModel):
    category: ExpenseCategory
    amount: float = Field(..., gt=0)
    description: str
    receipt_image: Optional[str] = None
    status: ExpenseStatus = ExpenseStatus.PENDING

class ExpenseUpdate(BaseModel):
    category: Optional[ExpenseCategory] = None
    amount: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    status: Optional[ExpenseStatus] = None
    receipt_image: Optional[str] = None

class ExpenseResponse(BaseModel):
    id: PyObjectId
    expense_number: str
    category: ExpenseCategory
    amount: float
    description: str
    receipt_image: Optional[str]
    status: ExpenseStatus
    approved_by: Optional[PyObjectId] = None
    approved_by_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {ObjectId: str}

# Notification Models
class NotificationResponse(BaseModel):
    id: PyObjectId
    user_id: PyObjectId
    title: str
    message: str
    is_read: bool
    order_id: Optional[PyObjectId] = None
    request_id: Optional[PyObjectId] = None
    created_at: datetime

    class Config:
        json_encoders = {ObjectId: str}

# Dashboard/Stats Models
class RevenueSummary(BaseModel):
    period: str
    total_revenue: float
    order_revenue: float
    service_revenue: float
    total_expenses: float
    net_profit: float
    order_count: int
    service_count: int
    expense_count: int
    start_date: datetime
    end_date: datetime

class DailySalesData(BaseModel):
    date: str
    total: float

class SalesTrends(BaseModel):
    period: str
    daily_sales: List[DailySalesData]

class AdminStats(BaseModel):
    counts: Dict[str, int]
    financials: Dict[str, float]
    recent_orders: List[OrderResponse]
    recent_requests: List[ServiceRequestResponse]
    sales_trends: SalesTrends

# Service Payment Models
class ServicePaymentCreate(BaseModel):
    request_id: str
    payment_method: PaymentMethod
    amount: float = Field(..., gt=0)

    @validator('request_id')
    def validate_request_id(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid request ID format")
        return v

class QuoteUpdate(BaseModel):
    quote_amount: float = Field(..., gt=0)

# Forward references for recursive models
OrderResponse.update_forward_refs()
OrderItemResponse.update_forward_refs()
TransactionResponse.update_forward_refs()
ExpenseResponse.update_forward_refs()
NotificationResponse.update_forward_refs()
ServiceRequestResponse.update_forward_refs()