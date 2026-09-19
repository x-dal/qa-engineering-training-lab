from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import OrderStatus, UserRole

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int


class UserBase(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    full_name: str = Field(min_length=2, max_length=120)
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(UserBase):
    password: str | None = Field(default=None, min_length=8, max_length=128)


class StatusUpdate(BaseModel):
    is_active: bool


class UserRead(UserBase, ORMModel):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str


class AccountRegister(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class DevPasswordReset(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    message: str


class CustomerBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=5, max_length=40, pattern=r"^[0-9+() .-]+$")
    address: str = Field(min_length=5, max_length=1000)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CustomerBase):
    pass


class CustomerRead(CustomerBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class ProductBase(BaseModel):
    sku: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=5000)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    stock_quantity: int = Field(ge=0)

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        return value.strip().upper()


class ProductCreate(ProductBase):
    is_active: bool = True


class ProductUpdate(ProductBase):
    is_active: bool


class ProductRead(ProductCreate, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    customer_id: int
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemRead(ORMModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    product: ProductRead


class OrderRead(ORMModel):
    id: int
    order_number: str
    customer_id: int
    status: OrderStatus
    total_amount: Decimal
    created_by: int
    created_at: datetime
    updated_at: datetime
    customer: CustomerRead
    items: list[OrderItemRead]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class StatusCount(BaseModel):
    status: OrderStatus
    count: int


class DashboardSummary(BaseModel):
    customer_count: int
    active_product_count: int
    order_count: int
    orders_by_status: list[StatusCount]
    low_stock_products: list[ProductRead]
    delivered_revenue: Decimal
