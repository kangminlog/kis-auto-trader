from app.strategies.base import Signal
from app.strategies.indicators import OHLCV, MarketRegime, atr, calc_sizing, detect_regime, find_peak_day
from app.strategies.volume_breakout import VolumeBreakoutRetestStrategy


def _make_candle(
    close: float,
    volume: int = 1000,
    turnover: float = 0,
    open_: float | None = None,
    high: float | None = None,
    low: float | None = None,
) -> OHLCV:
    o = open_ if open_ is not None else close * 0.99
    h = high if high is not None else close * 1.01
    lo = low if low is not None else close * 0.98
    return OHLCV(open=o, high=h, low=lo, close=close, volume=volume, turnover=turnover)


def _make_scenario(
    peak_price: float = 10000,
    peak_turnover: float = 15_000_000_000,  # 150억 거래대금
    market_cap: float = 100_000_000_000,  # 1000억 시총
    days_after_peak: int = 20,
    current_price: float | None = None,
):
    """peak day + 횡보 + 현재가 근접 시나리오 생성."""
    candles = []

    # peak 전 데이터 (20일)
    for i in range(20):
        candles.append(_make_candle(peak_price * 0.95, volume=500, turnover=5_000_000_000))

    # peak day (양봉, 거래대금 폭발)
    candles.append(
        OHLCV(
            open=peak_price * 0.98,
            high=peak_price * 1.05,
            low=peak_price * 0.97,
            close=peak_price,
            volume=50000,
            turnover=peak_turnover,
        )
    )

    # 횡보 구간
    for i in range(days_after_peak):
        price = peak_price * (1 + (i % 3 - 1) * 0.005)  # ±0.5% 횡보
        candles.append(_make_candle(price, volume=1000, turnover=2_000_000_000))

    # 현재가 (peak 근처로 복귀)
    final_price = current_price if current_price else peak_price * 1.01
    candles.append(_make_candle(final_price, volume=1200, turnover=3_000_000_000))

    return candles, market_cap


# --- Indicator tests ---


def test_atr():
    candles = [_make_candle(100 + i, volume=1000) for i in range(20)]
    result = atr(candles, period=14)
    assert result > 0


def test_detect_regime_bull():
    candles = [_make_candle(100 + i * 2, volume=1000) for i in range(80)]
    regime = detect_regime(candles)
    assert regime == MarketRegime.BULL


def test_detect_regime_bear():
    candles = [_make_candle(200 - i * 2, volume=1000) for i in range(80)]
    regime = detect_regime(candles)
    assert regime == MarketRegime.BEAR


def test_find_peak_day():
    candles = [_make_candle(100, volume=1000, turnover=1_000_000) for _ in range(10)]
    candles[5] = _make_candle(100, volume=50000, turnover=50_000_000)  # peak
    idx, ratio = find_peak_day(candles, market_cap=100_000_000)
    assert idx == 5
    assert ratio > 0


def test_calc_sizing():
    # 10,000원 → 40만원/10,000원 = 40주
    assert calc_sizing(10000) == 40
    # 500,000원 → 40만원/500,000원 = 0 → min 1주
    assert calc_sizing(500000) == 1


# --- Strategy tests ---


def test_buy_signal():
    """모든 조건 충족 → BUY."""
    candles, market_cap = _make_scenario(
        peak_price=10000,
        days_after_peak=20,
        current_price=10050,
    )
    strategy = VolumeBreakoutRetestStrategy(
        min_turnover_pct=10.0,
        min_days_since_peak=15,
        proximity_pct=3.0,
    )
    result = strategy.analyze_candles(candles, market_cap)
    assert result.signal == Signal.BUY
    assert result.tp_price > 0
    assert result.sl_price > 0
    assert result.suggested_qty > 0


def test_low_turnover():
    """거래대금 부족 → HOLD."""
    candles, market_cap = _make_scenario(
        peak_turnover=5_000_000_000,  # 5% < 10%
    )
    strategy = VolumeBreakoutRetestStrategy(min_turnover_pct=10.0)
    result = strategy.analyze_candles(candles, market_cap)
    assert result.signal == Signal.HOLD
    assert "turnover" in result.reason


def test_bearish_peak():
    """음봉 peak day → HOLD."""
    candles, market_cap = _make_scenario()
    # peak day를 음봉으로 변경
    peak_idx = 20
    candles[peak_idx] = OHLCV(
        open=10500,
        high=10600,
        low=9800,
        close=9900,
        volume=50000,
        turnover=15_000_000_000,
    )
    strategy = VolumeBreakoutRetestStrategy()
    result = strategy.analyze_candles(candles, market_cap)
    assert result.signal == Signal.HOLD
    assert "음봉" in result.reason


def test_insufficient_days():
    """횡보 기간 부족 → HOLD."""
    candles, market_cap = _make_scenario(days_after_peak=5)
    strategy = VolumeBreakoutRetestStrategy(min_days_since_peak=15)
    result = strategy.analyze_candles(candles, market_cap)
    assert result.signal == Signal.HOLD
    assert "days_since" in result.reason


def test_too_far_proximity():
    """현재가가 peak에서 너무 멀음 → HOLD."""
    candles, market_cap = _make_scenario(current_price=11000)  # +10%
    strategy = VolumeBreakoutRetestStrategy(proximity_pct=3.0)
    result = strategy.analyze_candles(candles, market_cap)
    assert result.signal == Signal.HOLD
    assert "proximity" in result.reason


def test_regime_affects_tp_sl():
    """Regime에 따라 TP/SL 배수 달라짐."""
    candles, market_cap = _make_scenario(days_after_peak=20, current_price=10050)
    strategy = VolumeBreakoutRetestStrategy()
    result = strategy.analyze_candles(candles, market_cap)

    if result.signal == Signal.BUY:
        # TP > 현재가, SL < 현재가
        assert result.tp_price > candles[-1].close
        assert result.sl_price < candles[-1].close


def test_strategy_registered():
    from app.strategies.runner import STRATEGY_REGISTRY

    assert "volume_breakout_retest" in STRATEGY_REGISTRY


def test_api_strategy_list_includes_volume_breakout(client):
    response = client.get("/api/strategy/list")
    names = [s["name"] for s in response.json()]
    assert "volume_breakout_retest" in names


def test_insufficient_data():
    """데이터 부족 → HOLD."""
    candles = [_make_candle(100) for _ in range(5)]
    strategy = VolumeBreakoutRetestStrategy()
    result = strategy.analyze_candles(candles, 100_000_000_000)
    assert result.signal == Signal.HOLD
