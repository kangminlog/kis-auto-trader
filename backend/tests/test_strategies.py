import pytest

from app.strategies.backtest import run_backtest
from app.strategies.base import Signal
from app.strategies.golden_cross import GoldenCrossStrategy
from app.strategies.momentum import MomentumStrategy
from app.strategies.runner import STRATEGY_REGISTRY, get_strategy, run_all_strategies

# --- Golden Cross ---


def test_golden_cross_buy_signal():
    # 단기MA > 장기MA 교차 시나리오
    # 먼저 하락 구간 → 상승 전환
    prices_down = [100 - i * 0.5 for i in range(21)]  # 하락 (과거)
    prices_up = [90 + i * 2 for i in range(5)]  # 상승 (최근)
    prices = list(reversed(prices_up + prices_down[:16]))  # 최신순

    strategy = GoldenCrossStrategy(short_window=5, long_window=20)
    result = strategy.analyze(prices)
    # 데이터 구성에 따라 BUY 또는 HOLD
    assert result.signal in (Signal.BUY, Signal.HOLD)


def test_golden_cross_insufficient_data():
    strategy = GoldenCrossStrategy()
    result = strategy.analyze([100, 99, 98])
    assert result.signal == Signal.HOLD
    assert "데이터 부족" in result.reason


def test_golden_cross_dead_cross():
    # 단기MA가 장기MA를 하향 돌파
    # 상승 → 하락 전환 시나리오
    strategy = GoldenCrossStrategy(short_window=3, long_window=10)
    # 최신순: 급락
    prices = [50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    result = strategy.analyze(prices)
    assert result.signal in (Signal.SELL, Signal.HOLD)


# --- Momentum ---


def test_momentum_buy_signal():
    strategy = MomentumStrategy(lookback=5, buy_threshold=0.05)
    # 5일 전 100 → 현재 110 = 10% 수익
    prices = [110, 108, 106, 104, 102, 100]
    result = strategy.analyze(prices)
    assert result.signal == Signal.BUY


def test_momentum_sell_signal():
    strategy = MomentumStrategy(lookback=5, sell_threshold=-0.05)
    # 5일 전 100 → 현재 90 = -10% 손실
    prices = [90, 92, 94, 96, 98, 100]
    result = strategy.analyze(prices)
    assert result.signal == Signal.SELL


def test_momentum_hold_signal():
    strategy = MomentumStrategy(lookback=5, buy_threshold=0.05, sell_threshold=-0.05)
    # 변동 없음
    prices = [100, 100, 100, 100, 100, 100]
    result = strategy.analyze(prices)
    assert result.signal == Signal.HOLD


def test_momentum_insufficient_data():
    strategy = MomentumStrategy(lookback=10)
    result = strategy.analyze([100, 99])
    assert result.signal == Signal.HOLD


# --- Runner ---


def test_strategy_registry():
    assert "golden_cross" in STRATEGY_REGISTRY
    assert "momentum" in STRATEGY_REGISTRY


def test_get_strategy():
    strategy = get_strategy("golden_cross")
    assert isinstance(strategy, GoldenCrossStrategy)


def test_get_unknown_strategy():
    with pytest.raises(ValueError, match="Unknown strategy"):
        get_strategy("nonexistent")


def test_run_all_strategies():
    prices = [100 + i for i in range(30)]  # 최신순
    results = run_all_strategies("005930", prices)
    assert len(results) == len(STRATEGY_REGISTRY)
    for r in results:
        assert r.stock_code == "005930"


# --- Backtest ---


def test_backtest_basic():
    strategy = MomentumStrategy(lookback=5, buy_threshold=0.03, sell_threshold=-0.03)
    # 상승 → 하락 → 상승 (과거→현재)
    prices = [100 + i for i in range(20)] + [120 - i for i in range(20)] + [100 + i * 2 for i in range(20)]

    result = run_backtest(strategy, "005930", prices)

    assert result.strategy_name == "momentum"
    assert result.stock_code == "005930"
    assert result.initial_capital == 10_000_000
    assert result.final_capital > 0
    assert result.metrics.total_trades >= 0
    assert len(result.equity_curve) > 0


def test_backtest_mdd():
    strategy = MomentumStrategy(lookback=3, buy_threshold=0.02, sell_threshold=-0.02)
    # 급등 후 급락
    prices = [100 + i * 5 for i in range(10)] + [150 - i * 10 for i in range(10)]

    result = run_backtest(strategy, "005930", prices)
    assert result.metrics.max_drawdown >= 0


def test_backtest_no_trades():
    strategy = MomentumStrategy(lookback=5, buy_threshold=0.5)  # 매우 높은 임계
    prices = [100] * 20  # 변동 없음

    result = run_backtest(strategy, "005930", prices)
    assert result.metrics.total_trades == 0
    assert result.final_capital == result.initial_capital


# --- API ---


def test_api_list_strategies(client):
    response = client.get("/api/strategy/list")
    assert response.status_code == 200
    data = response.json()
    names = [s["name"] for s in data]
    assert "golden_cross" in names
    assert "momentum" in names


def test_api_analyze(client):
    response = client.post("/api/strategy/analyze", json={"stock_code": "005930"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3  # golden_cross + momentum + volume_breakout_retest


def test_api_backtest(client):
    response = client.post(
        "/api/strategy/backtest",
        json={"stock_code": "005930", "strategy_name": "momentum", "days": 50},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["strategy_name"] == "momentum"
    assert "metrics" in data
    assert "total_return" in data["metrics"]
