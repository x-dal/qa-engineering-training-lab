from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Customer, Order, OrderItem, OrderStatus, Product, User
from app.schemas.models import OrderCreate

TRANSITIONS = {
    OrderStatus.pending: {OrderStatus.paid, OrderStatus.cancelled},
    OrderStatus.paid: {OrderStatus.shipped, OrderStatus.cancelled},
    OrderStatus.shipped: {OrderStatus.delivered},
    OrderStatus.delivered: set(),
    OrderStatus.cancelled: set(),
}


def order_options():
    return (joinedload(Order.customer), selectinload(Order.items).joinedload(OrderItem.product))


def get_order(db: Session, order_id: int, *, lock: bool = False) -> Order:
    stmt = select(Order).where(Order.id == order_id)
    if lock:
        stmt = stmt.with_for_update()
    else:
        stmt = stmt.options(*order_options())
    order = db.scalar(stmt)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


def create_order(db: Session, payload: OrderCreate, user: User) -> Order:
    if db.get(Customer, payload.customer_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Customer not found")
    product_ids = [item.product_id for item in payload.items]
    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "The same product cannot appear twice in an order")
    products = {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(product_ids)).with_for_update()).all()}
    if len(products) != len(product_ids):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "One or more products were not found")
    total = Decimal("0.00")
    lines: list[OrderItem] = []
    for requested in payload.items:
        product = products[requested.product_id]
        if not product.is_active:
            raise HTTPException(status.HTTP_409_CONFLICT, f"Product {product.sku} is inactive")
        if requested.quantity > product.stock_quantity:
            raise HTTPException(status.HTTP_409_CONFLICT, f"Insufficient stock for {product.sku}; available: {product.stock_quantity}")
        product.stock_quantity -= requested.quantity
        line_total = product.price * requested.quantity
        total += line_total
        lines.append(OrderItem(product_id=product.id, quantity=requested.quantity, unit_price=product.price, line_total=line_total))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    order = Order(order_number=f"OF-{stamp}", customer_id=payload.customer_id, status=OrderStatus.pending, total_amount=total, created_by=user.id, items=lines)
    db.add(order)
    db.commit()
    return get_order(db, order.id)


def transition_order(db: Session, order_id: int, target: OrderStatus) -> Order:
    order = get_order(db, order_id, lock=True)
    if target not in TRANSITIONS[order.status]:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Cannot transition order from {order.status.value} to {target.value}")
    if target == OrderStatus.cancelled:
        product_ids = [item.product_id for item in order.items]
        products = {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(product_ids)).with_for_update()).all()}
        for item in order.items:
            products[item.product_id].stock_quantity += item.quantity
    order.status = target
    db.commit()
    return get_order(db, order.id)
