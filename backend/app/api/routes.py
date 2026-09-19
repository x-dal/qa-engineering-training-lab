from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_current_user, hash_password, require_admin, verify_password
from app.database.session import get_db
from app.models import Customer, Order, OrderStatus, Product, User, UserRole
from app.schemas.models import (
    AccountRegister, CustomerCreate, CustomerRead, CustomerUpdate, DashboardSummary, DevPasswordReset,
    LoginRequest, MessageResponse, OrderCreate,
    OrderRead, OrderStatusUpdate, Page, ProductCreate, ProductRead, ProductUpdate, StatusCount,
    StatusUpdate, Token, UserCreate, UserRead, UserUpdate,
)
from app.services.common import commit_or_conflict, paginate
from app.services.orders import create_order, get_order, order_options, transition_order

router = APIRouter()


def sort_column(model, sort_by: str, allowed: set[str]):
    if sort_by not in allowed:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"sort_by must be one of: {', '.join(sorted(allowed))}")
    return getattr(model, sort_by)


@router.post("/auth/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This user account is inactive")
    return Token(access_token=create_access_token(user), user=user)


@router.post("/auth/register", response_model=Token, status_code=201)
def register(payload: AccountRegister, db: Session = Depends(get_db)):
    """Create an active staff account; administrative roles cannot be self-assigned."""
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name.strip(),
        role=UserRole.staff,
        is_active=True,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    commit_or_conflict(db, "An account with this email already exists")
    db.refresh(user)
    return Token(access_token=create_access_token(user), user=user)


@router.post("/auth/reset-password", response_model=MessageResponse)
def reset_password(payload: DevPasswordReset, db: Session = Depends(get_db)):
    """Development-only password reset without an email token."""
    if not settings.enable_dev_password_reset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Password reset is not available")
    user = db.scalar(select(User).where(func.lower(User.email) == payload.email.lower()))
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No account exists with this email")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return MessageResponse(message="Password reset successfully")


@router.get("/auth/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/users", response_model=Page[UserRead], dependencies=[Depends(require_admin)])
def list_users(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None,
               sort_by: str = "created_at", sort_order: str = Query("desc", pattern="^(asc|desc)$"),
               is_active: bool | None = None, db: Session = Depends(get_db)):
    stmt = select(User)
    if search: stmt = stmt.where(or_(User.email.ilike(f"%{search}%"), User.full_name.ilike(f"%{search}%")))
    if is_active is not None: stmt = stmt.where(User.is_active == is_active)
    col = sort_column(User, sort_by, {"id", "email", "full_name", "role", "is_active", "created_at"})
    stmt = stmt.order_by(desc(col) if sort_order == "desc" else asc(col))
    items, total, pages = paginate(db, stmt, page, page_size)
    return Page(items=items, page=page, page_size=page_size, total=total, total_pages=pages)


@router.post("/users", response_model=UserRead, status_code=201)
def add_user(payload: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = User(email=payload.email.lower(), full_name=payload.full_name, role=payload.role, password_hash=hash_password(payload.password))
    db.add(user); commit_or_conflict(db, "A user with this email already exists"); db.refresh(user); return user


@router.get("/users/{user_id}", response_model=UserRead)
def read_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    return user


@router.put("/users/{user_id}", response_model=UserRead)
def edit_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    user.email, user.full_name, user.role = payload.email.lower(), payload.full_name, payload.role
    if payload.password: user.password_hash = hash_password(payload.password)
    commit_or_conflict(db, "A user with this email already exists"); db.refresh(user); return user


@router.patch("/users/{user_id}/status", response_model=UserRead)
def user_status(user_id: int, payload: StatusUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    if user.id == admin.id and not payload.is_active: raise HTTPException(409, "You cannot deactivate your own account")
    user.is_active = payload.is_active; db.commit(); db.refresh(user); return user


@router.get("/customers", response_model=Page[CustomerRead])
def list_customers(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None,
                   sort_by: str = "name", sort_order: str = Query("asc", pattern="^(asc|desc)$"),
                   db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    stmt = select(Customer)
    if search: stmt = stmt.where(or_(Customer.name.ilike(f"%{search}%"), Customer.email.ilike(f"%{search}%"), Customer.phone.ilike(f"%{search}%")))
    col = sort_column(Customer, sort_by, {"id", "name", "email", "created_at"}); stmt = stmt.order_by(desc(col) if sort_order == "desc" else asc(col))
    items, total, pages = paginate(db, stmt, page, page_size); return Page(items=items, page=page, page_size=page_size, total=total, total_pages=pages)


@router.post("/customers", response_model=CustomerRead, status_code=201)
def add_customer(payload: CustomerCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    customer = Customer(**payload.model_dump(), email=payload.email.lower()); db.add(customer)
    commit_or_conflict(db, "A customer with this email already exists"); db.refresh(customer); return customer


@router.get("/customers/{customer_id}", response_model=CustomerRead)
def read_customer(customer_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.get(Customer, customer_id)
    if not item: raise HTTPException(404, "Customer not found")
    return item


@router.put("/customers/{customer_id}", response_model=CustomerRead)
def edit_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.get(Customer, customer_id)
    if not item: raise HTTPException(404, "Customer not found")
    for key, value in payload.model_dump().items(): setattr(item, key, value.lower() if key == "email" else value)
    commit_or_conflict(db, "A customer with this email already exists"); db.refresh(item); return item


@router.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.get(Customer, customer_id)
    if not item: raise HTTPException(404, "Customer not found")
    db.delete(item)
    try: db.commit()
    except Exception as exc:
        db.rollback(); raise HTTPException(409, "Customers with orders cannot be deleted") from exc
    return Response(status_code=204)


@router.get("/products", response_model=Page[ProductRead])
def list_products(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None,
                  is_active: bool | None = None, sort_by: str = "name", sort_order: str = Query("asc", pattern="^(asc|desc)$"),
                  db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    stmt = select(Product)
    if search: stmt = stmt.where(or_(Product.name.ilike(f"%{search}%"), Product.sku.ilike(f"%{search}%")))
    if is_active is not None: stmt = stmt.where(Product.is_active == is_active)
    col = sort_column(Product, sort_by, {"id", "sku", "name", "price", "stock_quantity", "created_at"}); stmt = stmt.order_by(desc(col) if sort_order == "desc" else asc(col))
    items, total, pages = paginate(db, stmt, page, page_size); return Page(items=items, page=page, page_size=page_size, total=total, total_pages=pages)


@router.post("/products", response_model=ProductRead, status_code=201)
def add_product(payload: ProductCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    item = Product(**payload.model_dump()); db.add(item); commit_or_conflict(db, "A product with this SKU already exists"); db.refresh(item); return item


@router.get("/products/{product_id}", response_model=ProductRead)
def read_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.get(Product, product_id)
    if not item: raise HTTPException(404, "Product not found")
    return item


@router.put("/products/{product_id}", response_model=ProductRead)
def edit_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    item = db.get(Product, product_id)
    if not item: raise HTTPException(404, "Product not found")
    for key, value in payload.model_dump().items(): setattr(item, key, value)
    commit_or_conflict(db, "A product with this SKU already exists"); db.refresh(item); return item


@router.patch("/products/{product_id}/status", response_model=ProductRead)
def product_status(product_id: int, payload: StatusUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    item = db.get(Product, product_id)
    if not item: raise HTTPException(404, "Product not found")
    item.is_active = payload.is_active; db.commit(); db.refresh(item); return item


@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    item = db.get(Product, product_id)
    if not item: raise HTTPException(404, "Product not found")
    db.delete(item)
    try: db.commit()
    except Exception as exc: db.rollback(); raise HTTPException(409, "Products used by orders cannot be deleted") from exc
    return Response(status_code=204)


@router.get("/orders", response_model=Page[OrderRead])
def list_orders(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None,
                status_filter: OrderStatus | None = Query(None, alias="status"), sort_by: str = "created_at", sort_order: str = Query("desc", pattern="^(asc|desc)$"),
                db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    stmt = select(Order).options(*order_options())
    if search: stmt = stmt.where(Order.order_number.ilike(f"%{search}%"))
    if status_filter: stmt = stmt.where(Order.status == status_filter)
    col = sort_column(Order, sort_by, {"id", "order_number", "status", "total_amount", "created_at"}); stmt = stmt.order_by(desc(col) if sort_order == "desc" else asc(col))
    items, total, pages = paginate(db, stmt, page, page_size); return Page(items=items, page=page, page_size=page_size, total=total, total_pages=pages)


@router.post("/orders", response_model=OrderRead, status_code=201)
def add_order(payload: OrderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_order(db, payload, user)


@router.get("/orders/{order_id}", response_model=OrderRead)
def read_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return get_order(db, order_id)


@router.patch("/orders/{order_id}/status", response_model=OrderRead)
def order_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return transition_order(db, order_id, payload.status)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    status_rows = dict(db.execute(select(Order.status, func.count(Order.id)).group_by(Order.status)).all())
    low = list(db.scalars(select(Product).where(Product.is_active.is_(True), Product.stock_quantity <= 5).order_by(Product.stock_quantity).limit(10)).all())
    revenue = db.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)).where(Order.status == OrderStatus.delivered)) or Decimal("0.00")
    return DashboardSummary(customer_count=db.scalar(select(func.count(Customer.id))) or 0,
        active_product_count=db.scalar(select(func.count(Product.id)).where(Product.is_active.is_(True))) or 0,
        order_count=db.scalar(select(func.count(Order.id))) or 0,
        orders_by_status=[StatusCount(status=s, count=status_rows.get(s, 0)) for s in OrderStatus],
        low_stock_products=low, delivered_revenue=revenue)
