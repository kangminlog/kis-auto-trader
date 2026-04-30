from app.models.execution import Execution
from app.models.order import Order, OrderSide, OrderStatus, OrderType
from app.models.portfolio import PortfolioItem
from app.models.stock import Stock


def test_create_stock(db_session):
    stock = Stock(code="005930", name="삼성전자", market="KOSPI")
    db_session.add(stock)
    db_session.commit()

    result = db_session.query(Stock).filter_by(code="005930").first()
    assert result is not None
    assert result.name == "삼성전자"
    assert result.market == "KOSPI"


def test_create_order(db_session):
    stock = Stock(code="005930", name="삼성전자", market="KOSPI")
    db_session.add(stock)
    db_session.commit()

    order = Order(
        stock_code="005930",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        status=OrderStatus.PENDING,
        quantity=10,
        price=70000,
    )
    db_session.add(order)
    db_session.commit()

    result = db_session.query(Order).first()
    assert result is not None
    assert result.stock_code == "005930"
    assert result.side == OrderSide.BUY
    assert result.quantity == 10


def test_create_execution(db_session):
    stock = Stock(code="005930", name="삼성전자", market="KOSPI")
    db_session.add(stock)
    db_session.commit()

    order = Order(
        stock_code="005930",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=5,
    )
    db_session.add(order)
    db_session.commit()

    execution = Execution(order_id=order.id, quantity=5, price=70500)
    db_session.add(execution)
    db_session.commit()

    result = db_session.query(Execution).first()
    assert result is not None
    assert result.order_id == order.id
    assert result.quantity == 5


def test_create_portfolio_item(db_session):
    stock = Stock(code="005930", name="삼성전자", market="KOSPI")
    db_session.add(stock)
    db_session.commit()

    item = PortfolioItem(stock_code="005930", quantity=10, avg_price=70000)
    db_session.add(item)
    db_session.commit()

    result = db_session.query(PortfolioItem).filter_by(stock_code="005930").first()
    assert result is not None
    assert result.quantity == 10
    assert float(result.avg_price) == 70000
