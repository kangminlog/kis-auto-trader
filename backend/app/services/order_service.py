from sqlalchemy.orm import Session

from app.models.order import Order, OrderSide, OrderStatus, OrderType


def submit_order(
    db: Session,
    *,
    stock_code: str,
    side: OrderSide,
    order_type: OrderType,
    quantity: int,
    price: float | None = None,
) -> Order:
    if order_type == OrderType.LIMIT and price is None:
        raise ValueError("Limit order requires a price")

    order = Order(
        stock_code=stock_code,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order_id: int) -> Order:
    order = db.query(Order).filter_by(id=order_id).first()
    if order is None:
        raise ValueError(f"Order {order_id} not found")
    if order.status != OrderStatus.PENDING:
        raise ValueError(f"Cannot cancel order in status: {order.status}")

    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return order


def get_orders(db: Session, status: OrderStatus | None = None) -> list[Order]:
    query = db.query(Order)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Order.created_at.desc()).all()
