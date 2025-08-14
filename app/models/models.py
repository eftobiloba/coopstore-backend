from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from bson import ObjectId
from datetime import datetime


# Custom ObjectId for MongoDB
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


# ---------- User & Membership ----------
class User(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    username: str
    email: EmailStr
    password: str
    full_name: str
    is_active: bool = True
    is_member: bool = False
    cooperative_account_id: Optional[str] = None
    role: Literal["admin", "user"] = "user"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    carts: Optional[List[PyObjectId]] = []

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True


class MembershipApplication(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    full_name: str
    email: EmailStr
    phone: str
    status: Literal['pending', 'approved', 'rejected'] = 'pending'
    applied_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True


# ---------- Products & Categories ----------
class Category(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    products: Optional[List[PyObjectId]] = []

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True


class Product(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    title: str
    description: str
    price: int
    discount_percentage: float
    rating: float
    stock: int
    brand: str
    thumbnail: str
    images: List[str]
    features: Optional[List[str]] = []
    is_published: bool = True
    type: Literal["physical", "financial"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    category_id: PyObjectId
    cart_items: Optional[List[PyObjectId]] = []

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True


class FinancialProduct(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: str
    category: Literal['mutual_fund', 'bond', 'treasury_bill']
    min_investment: float
    return_rate: float
    duration_months: int
    image: Optional[str] = None
    is_published: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True


# ---------- Cart & Order ----------
class CartItem(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    cart_id: PyObjectId
    product_id: PyObjectId
    quantity: int
    subtotal: float

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True


class Cart(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_amount: float
    cart_items: Optional[List[PyObjectId]] = []

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True


class Order(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    items: List[CartItem]
    total: float
    payment_method: Literal['pay_now', 'bnpl']
    status: Literal['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'] = 'pending'
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True


# ---------- BNPL ----------
class BNPLApplication(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    order_id: PyObjectId
    approved: bool = False
    status: Literal['pending', 'approved', 'rejected', 'repaid'] = 'pending'
    repayment_schedule: Optional[List[dict]] = []  # e.g. [{due_date, amount}]
    applied_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True


# ---------- Reviews ----------
class Review(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    product_id: PyObjectId
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True


# ---------- Promo Banners ----------
class PromoBanner(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    image_url: str
    redirect_link: Optional[str] = None
    alt_text: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        orm_mode = True
