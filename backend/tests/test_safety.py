import pytest

from app.models.stock import Stock
from app.services.safety import check_can_trade, check_stop_loss_take_profit, safety


def _setup_stock(db):
    stock = Stock(code="005930", name="삼성전자", market="KOSPI")
    db.add(stock)
    db.commit()


@pytest.fixture(autouse=True)
def reset_safety():
    """각 테스트 전 안전장치 리셋."""
    safety.kill_switch = False
    safety.daily_max_trades = 50
    safety.daily_max_amount = 10_000_000
    safety.stop_loss_pct = -5.0
    safety.take_profit_pct = 10.0
    safety._daily_trade_count = 0
    safety._daily_trade_amount = 0.0
    yield


# --- check_can_trade ---


def test_can_trade_normal():
    ok, reason = check_can_trade(70000, 10)
    assert ok is True


def test_kill_switch_blocks():
    safety.kill_switch = True
    ok, reason = check_can_trade(70000, 10)
    assert ok is False
    assert "Kill switch" in reason


def test_daily_trade_count_limit():
    safety.daily_max_trades = 2
    safety._daily_trade_count = 2
    ok, reason = check_can_trade(70000, 1)
    assert ok is False
    assert "횟수" in reason


def test_daily_amount_limit():
    safety.daily_max_amount = 1_000_000
    safety._daily_trade_amount = 900_000
    ok, reason = check_can_trade(70000, 10)  # 700,000원 추가 → 초과
    assert ok is False
    assert "금액" in reason


def test_record_trade():
    safety.record_trade(500_000)
    assert safety.daily_trade_count == 1
    assert safety.daily_trade_amount == 500_000


# --- stop loss / take profit ---


def test_stop_loss_triggered(db_session):
    avg_price = 100000
    current_price = 94000  # -6%
    result = check_stop_loss_take_profit(db_session, "005930", current_price, avg_price, 10)
    assert result == "stop_loss"


def test_take_profit_triggered(db_session):
    avg_price = 100000
    current_price = 111000  # +11%
    result = check_stop_loss_take_profit(db_session, "005930", current_price, avg_price, 10)
    assert result == "take_profit"


def test_no_trigger(db_session):
    avg_price = 100000
    current_price = 102000  # +2%, 임계 미달
    result = check_stop_loss_take_profit(db_session, "005930", current_price, avg_price, 10)
    assert result is None


# --- API ---


def test_api_safety_status(client):
    response = client.get("/api/safety/status")
    assert response.status_code == 200
    data = response.json()
    assert "kill_switch" in data
    assert data["kill_switch"] is False


def test_api_kill_switch(client):
    response = client.post("/api/safety/kill-switch", json={"active": True})
    assert response.json()["kill_switch"] is True

    response = client.post("/api/safety/kill-switch", json={"active": False})
    assert response.json()["kill_switch"] is False


def test_api_update_config(client):
    response = client.patch(
        "/api/safety/config",
        json={"daily_max_trades": 10, "stop_loss_pct": -3.0},
    )
    data = response.json()
    assert data["max_trades"] == 10
    assert data["stop_loss_pct"] == -3.0


def test_kill_switch_blocks_auto_trade(client, db_session):
    _setup_stock(db_session)
    client.post(
        "/api/auto-trade/configs",
        json={"stock_code": "005930", "strategy_name": "momentum", "quantity": 5},
    )

    # Kill switch 활성화
    client.post("/api/safety/kill-switch", json={"active": True})

    # 자동매매 트리거 → 로그 0건 (전부 스킵)
    client.post("/api/auto-trade/scheduler/trigger")
    response = client.get("/api/auto-trade/logs")
    assert len(response.json()) == 0
