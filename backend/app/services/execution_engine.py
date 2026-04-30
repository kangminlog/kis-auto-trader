from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.models.order import Order, OrderSide, OrderStatus, OrderType
from app.models.portfolio import PortfolioItem
from app.services.market_data import MarketDataProvider


def process_pending_orders(db: Session, market: MarketDataProvider) -> list[Execution]:
    """대기 중인 주문을 시뮬레이션 체결 처리."""
    pending_orders = db.query(Order).filter_by(status=OrderStatus.PENDING).all()
    executions = []

    for order in pending_orders:
        price_info = market.get_price(order.stock_code)
        fill_price = _determine_fill_price(order, price_info.current_price)

        if fill_price is None:
            continue

        execution = Execution(
            order_id=order.id,
            quantity=order.quantity,
            price=fill_price,
        )
        db.add(execution)

        order.status = OrderStatus.FILLED
        _update_portfolio(db, order, fill_price)

        executions.append(execution)

    db.commit()
    return executions


def _determine_fill_price(order: Order, current_price: float) -> float | None:
    if order.order_type == OrderType.MARKET:
        return current_price

    # Limit order: buy only if market price <= limit price, sell only if >= limit price
    if order.side == OrderSide.BUY and current_price <= order.price:
        return float(order.price)
    if order.side == OrderSide.SELL and current_price >= order.price:
        return float(order.price)

    return None


def _update_portfolio(db: Session, order: Order, fill_price: float) -> None:
    item = db.query(PortfolioItem).filter_by(stock_code=order.stock_code).first()

    if order.side == OrderSide.BUY:
        if item is None:
            item = PortfolioItem(
                stock_code=order.stock_code,
                quantity=order.quantity,
                avg_price=fill_price,
            )
            db.add(item)
        else:
            total_cost = float(item.avg_price) * item.quantity + fill_price * order.quantity
            item.quantity += order.quantity
            item.avg_price = total_cost / item.quantity

    elif order.side == OrderSide.SELL:
        if item is None or item.quantity < order.quantity:
            order.status = OrderStatus.REJECTED
            return
        item.quantity -= order.quantity
        if item.quantity == 0:
            db.delete(item)
