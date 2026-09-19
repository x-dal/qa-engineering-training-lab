"""Idempotently seed local development data. Run after `alembic upgrade head`."""
from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models import Customer, Order, OrderItem, OrderStatus, Product, User, UserRole

CUSTOMERS = [(f"Customer {i:02d}", f"customer{i:02d}@example.com", f"+46 70 100 {i:04d}", f"{i} Market Street, Stockholm") for i in range(1, 11)]
PRODUCTS = [(f"OF-{i:04d}", f"Warehouse Product {i:02d}", Decimal(f"{9 + i * 2}.95"), (i * 7) % 34, i not in (24, 25)) for i in range(1, 26)]


def run():
    with SessionLocal() as db:
        for email, name, password, role in [("admin@orderflow.local", "OrderFlow Admin", "Admin123!", UserRole.admin), ("staff@orderflow.local", "OrderFlow Staff", "Staff123!", UserRole.staff)]:
            user = db.scalar(select(User).where(User.email == email))
            if not user: db.add(User(email=email, full_name=name, password_hash=hash_password(password), role=role, is_active=True))
        for name, email, phone, address in CUSTOMERS:
            if not db.scalar(select(Customer).where(Customer.email == email)): db.add(Customer(name=name, email=email, phone=phone, address=address))
        for sku, name, price, stock, active in PRODUCTS:
            if not db.scalar(select(Product).where(Product.sku == sku)): db.add(Product(sku=sku, name=name, description=f"Reliable inventory item {sku}", price=price, stock_quantity=stock, is_active=active))
        db.commit()
        admin = db.scalar(select(User).where(User.email == "admin@orderflow.local")); customers = list(db.scalars(select(Customer).order_by(Customer.id).limit(5))); products = list(db.scalars(select(Product).where(Product.is_active.is_(True)).order_by(Product.id).limit(10)))
        statuses = [OrderStatus.pending, OrderStatus.paid, OrderStatus.shipped, OrderStatus.delivered, OrderStatus.cancelled]
        for idx, order_status_value in enumerate(statuses, 1):
            number = f"OF-SEED-{idx:04d}"
            if db.scalar(select(Order).where(Order.order_number == number)): continue
            selected = products[(idx - 1) * 2:idx * 2]; lines = [OrderItem(product_id=p.id, quantity=1, unit_price=p.price, line_total=p.price) for p in selected]
            db.add(Order(order_number=number, customer_id=customers[idx - 1].id, status=order_status_value, total_amount=sum((p.price for p in selected), Decimal("0")), created_by=admin.id, items=lines))
        db.commit()
    print("OrderFlow seed data is ready (no duplicate records created).")


if __name__ == "__main__": run()
