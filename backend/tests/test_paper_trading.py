from app.models.order import OrderSide, OrderStatus, OrderType
from app.models.portfolio import PortfolioItem
from app.models.stock import Stock
from app.services.execution_engine import process_pending_orders
from app.services.market_data import DummyMarketDataProvider, MarketDataProvider, PriceInfo
from app.services.order_service import cancel_order, get_orders, submit_order


class FixedPriceProvider(MarketDataProvider):
    """테스트용 고정 시세 제공자."""

    def __init__(self, price: float):
        self.price = price

    def get_price(self, code: str) -> PriceInfo:
        return PriceInfo(code=code, current_price=self.price, high=self.price, low=self.price, volume=1000)


def _setup_stock(db):
    stock = Stock(code="005930", name="삼성전자", market="KOSPI")
    db.add(stock)
    db.commit()


def test_submit_market_order(db_session):
    _setup_stock(db_session)
    order = submit_order(db_session, stock_code="005930", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=10)
    assert order.id is not None
    assert order.status == OrderStatus.PENDING
    assert order.quantity == 10


def test_submit_limit_order(db_session):
    _setup_stock(db_session)
    order = submit_order(
        db_session, stock_code="005930", side=OrderSide.BUY, order_type=OrderType.LIMIT, quantity=5, price=70000
    )
    assert order.price == 70000


def test_cancel_order(db_session):
    _setup_stock(db_session)
    order = submit_order(db_session, stock_code="005930", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=10)
    cancelled = cancel_order(db_session, order.id)
    assert cancelled.status == OrderStatus.CANCELLED


def test_get_orders(db_session):
    _setup_stock(db_session)
    submit_order(db_session, stock_code="005930", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=10)
    submit_order(db_session, stock_code="005930", side=OrderSide.SELL, order_type=OrderType.MARKET, quantity=5)
    orders = get_orders(db_session)
    assert len(orders) == 2


def test_execute_market_buy(db_session):
    _setup_stock(db_session)
    submit_order(db_session, stock_code="005930", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=10)

    market = FixedPriceProvider(70000)
    executions = process_pending_orders(db_session, market)

    assert len(executions) == 1
    assert executions[0].price == 70000
    assert executions[0].quantity == 10

    item = db_session.query(PortfolioItem).filter_by(stock_code="005930").first()
    assert item is not None
    assert item.quantity == 10
    assert float(item.avg_price) == 70000


def test_execute_limit_buy_filled(db_session):
    _setup_stock(db_session)
    submit_order(
        db_session, stock_code="005930", side=OrderSide.BUY, order_type=OrderType.LIMIT, quantity=10, price=71000
    )

    market = FixedPriceProvider(70000)  # 현재가 < 지정가 → 체결
    executions = process_pending_orders(db_session, market)
    assert len(executions) == 1


def test_execute_limit_buy_not_filled(db_session):
    _setup_stock(db_session)
    submit_order(
        db_session, stock_code="005930", side=OrderSide.BUY, order_type=OrderType.LIMIT, quantity=10, price=69000
    )

    market = FixedPriceProvider(70000)  # 현재가 > 지정가 → 미체결
    executions = process_pending_orders(db_session, market)
    assert len(executions) == 0


def test_sell_updates_portfolio(db_session):
    _setup_stock(db_session)

    # 먼저 매수
    submit_order(db_session, stock_code="005930", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=10)
    process_pending_orders(db_session, FixedPriceProvider(70000))

    # 일부 매도
    submit_order(db_session, stock_code="005930", side=OrderSide.SELL, order_type=OrderType.MARKET, quantity=3)
    process_pending_orders(db_session, FixedPriceProvider(72000))

    item = db_session.query(PortfolioItem).filter_by(stock_code="005930").first()
    assert item.quantity == 7


def test_sell_all_removes_portfolio(db_session):
    _setup_stock(db_session)

    submit_order(db_session, stock_code="005930", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=5)
    process_pending_orders(db_session, FixedPriceProvider(70000))

    submit_order(db_session, stock_code="005930", side=OrderSide.SELL, order_type=OrderType.MARKET, quantity=5)
    process_pending_orders(db_session, FixedPriceProvider(70000))

    item = db_session.query(PortfolioItem).filter_by(stock_code="005930").first()
    assert item is None


def test_dummy_market_data_provider():
    provider = DummyMarketDataProvider()
    price = provider.get_price("005930")
    assert price.code == "005930"
    assert price.current_price > 0
    assert price.volume > 0


def test_api_create_order(client, db_session):
    _setup_stock(db_session)

    response = client.post(
        "/api/orders",
        json={"stock_code": "005930", "side": "buy", "order_type": "market", "quantity": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stock_code"] == "005930"
    assert data["status"] == "pending"


def test_api_execute_and_portfolio(client, db_session):
    _setup_stock(db_session)

    client.post("/api/orders", json={"stock_code": "005930", "side": "buy", "order_type": "market", "quantity": 10})
    response = client.post("/api/execute")
    assert response.json()["executed"] == 1

    response = client.get("/api/portfolio")
    assert len(response.json()) == 1
    assert response.json()[0]["stock_code"] == "005930"
