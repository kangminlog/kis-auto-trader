from app.models.auto_trade import AutoTradeConfig, AutoTradeLog
from app.models.stock import Stock
from app.services.auto_trader import run_auto_trade_cycle
from app.services.market_data import DummyMarketDataProvider


def _setup(db):
    stock = Stock(code="005930", name="삼성전자", market="KOSPI")
    db.add(stock)
    db.commit()


def test_create_config(db_session):
    config = AutoTradeConfig(
        stock_code="005930",
        stock_name="삼성전자",
        strategy_name="momentum",
        quantity=10,
        max_invest_amount=1_000_000,
    )
    db_session.add(config)
    db_session.commit()

    result = db_session.query(AutoTradeConfig).first()
    assert result.stock_code == "005930"
    assert result.is_active is True


def test_run_auto_trade_cycle(db_session):
    _setup(db_session)
    config = AutoTradeConfig(
        stock_code="005930",
        strategy_name="momentum",
        quantity=10,
    )
    db_session.add(config)
    db_session.commit()

    market = DummyMarketDataProvider()
    logs = run_auto_trade_cycle(db_session, market)

    assert len(logs) == 1
    assert logs[0].stock_code == "005930"
    assert logs[0].signal in ("buy", "sell", "hold")
    assert logs[0].action_taken in ("order_placed", "skipped", "error")


def test_inactive_config_skipped(db_session):
    _setup(db_session)
    config = AutoTradeConfig(
        stock_code="005930",
        strategy_name="momentum",
        quantity=10,
        is_active=False,
    )
    db_session.add(config)
    db_session.commit()

    market = DummyMarketDataProvider()
    logs = run_auto_trade_cycle(db_session, market)
    assert len(logs) == 0


def test_auto_trade_log_recorded(db_session):
    _setup(db_session)
    config = AutoTradeConfig(stock_code="005930", strategy_name="golden_cross", quantity=5)
    db_session.add(config)
    db_session.commit()

    market = DummyMarketDataProvider()
    run_auto_trade_cycle(db_session, market)

    logs = db_session.query(AutoTradeLog).all()
    assert len(logs) == 1
    assert logs[0].strategy_name == "golden_cross"


def test_per_stock_stop_loss(db_session):
    _setup(db_session)
    # 종목별 손절가 설정
    config = AutoTradeConfig(
        stock_code="005930",
        strategy_name="momentum",
        quantity=10,
        stop_loss_price=48000,
        take_profit_price=100000,
    )
    db_session.add(config)
    db_session.commit()

    from app.services.auto_trader import _check_per_stock_price

    # 현재가 47000 < 손절가 48000 → stop_loss
    assert _check_per_stock_price(db_session, "005930", 47000) == "stop_loss"
    # 현재가 50000 → None
    assert _check_per_stock_price(db_session, "005930", 50000) is None
    # 현재가 101000 > 익절가 100000 → take_profit
    assert _check_per_stock_price(db_session, "005930", 101000) == "take_profit"


def test_per_stock_no_config(db_session):
    from app.services.auto_trader import _check_per_stock_price

    assert _check_per_stock_price(db_session, "999999", 50000) is None


# --- API tests ---


def test_api_create_config_with_prices(client, db_session):
    response = client.post(
        "/api/auto-trade/configs",
        json={
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "strategy_name": "momentum",
            "quantity": 10,
            "stop_loss_price": 48000,
            "take_profit_price": 100000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stop_loss_price"] == 48000
    assert data["take_profit_price"] == 100000


def test_api_create_config(client, db_session):
    response = client.post(
        "/api/auto-trade/configs",
        json={"stock_code": "005930", "stock_name": "삼성전자", "strategy_name": "momentum", "quantity": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stock_code"] == "005930"
    assert data["is_active"] is True
    assert data["stop_loss_price"] is None


def test_api_list_configs(client, db_session):
    client.post(
        "/api/auto-trade/configs",
        json={"stock_code": "005930", "strategy_name": "momentum"},
    )
    response = client.get("/api/auto-trade/configs")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_api_toggle_config(client, db_session):
    resp = client.post(
        "/api/auto-trade/configs",
        json={"stock_code": "005930", "strategy_name": "momentum"},
    )
    config_id = resp.json()["id"]

    resp = client.patch(f"/api/auto-trade/configs/{config_id}/toggle")
    assert resp.json()["is_active"] is False

    resp = client.patch(f"/api/auto-trade/configs/{config_id}/toggle")
    assert resp.json()["is_active"] is True


def test_api_delete_config(client, db_session):
    resp = client.post(
        "/api/auto-trade/configs",
        json={"stock_code": "005930", "strategy_name": "momentum"},
    )
    config_id = resp.json()["id"]

    resp = client.delete(f"/api/auto-trade/configs/{config_id}")
    assert resp.json()["deleted"] == config_id

    resp = client.get("/api/auto-trade/configs")
    assert len(resp.json()) == 0


def test_api_scheduler_status(client):
    response = client.get("/api/auto-trade/scheduler/status")
    assert response.status_code == 200
    assert response.json()["running"] is False


def test_api_trigger(client, db_session):
    _setup(db_session)
    client.post(
        "/api/auto-trade/configs",
        json={"stock_code": "005930", "strategy_name": "momentum", "quantity": 5},
    )
    response = client.post("/api/auto-trade/scheduler/trigger")
    assert response.json()["triggered"] is True

    response = client.get("/api/auto-trade/logs")
    assert len(response.json()) >= 1


def test_api_logs(client, db_session):
    response = client.get("/api/auto-trade/logs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
