import enum
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    admin = "admin"
    staff = "staff"


class OrderStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)
    orders: Mapped[list["Order"]] = relationship(back_populates="creator")


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("email", name="uq_customers_email"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    phone: Mapped[str] = mapped_column(String(40))
    address: Mapped[str] = mapped_column(Text)
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("sku", name="uq_products_sku"),
        CheckConstraint("price >= 0", name="price_nonnegative"),
        CheckConstraint("stock_quantity >= 0", name="stock_nonnegative"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stock_quantity: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")


class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("order_number", name="uq_orders_order_number"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(32), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), index=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, name="order_status"), index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    customer: Mapped[Customer] = relationship(back_populates="orders")
    creator: Mapped[User] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "product_id", name="uq_order_items_order_product"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price >= 0", name="unit_price_nonnegative"),
        CheckConstraint("line_total >= 0", name="line_total_nonnegative"),
        Index("ix_order_items_order_id", "order_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="order_items")
