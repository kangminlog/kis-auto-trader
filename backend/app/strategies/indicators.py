"""기술지표 계산 유틸리티."""

from dataclasses import dataclass
from enum import StrEnum


class MarketRegime(StrEnum):
    BULL = "bull"
    BEAR = "bear"
    SIDE = "side"


@dataclass
class OHLCV:
    """하루치 캔들 데이터."""

    open: float
    high: float
    low: float
    close: float
    volume: int
    turnover: float = 0.0  # 거래대금


def atr(candles: list[OHLCV], period: int = 14) -> float:
    """ATR(Average True Range) 계산.

    Args:
        candles: 과거→현재 순서
        period: ATR 기간 (기본 14)
    """
    if len(candles) < period + 1:
        return 0.0

    true_ranges = []
    for i in range(1, len(candles)):
        high = candles[i].high
        low = candles[i].low
        prev_close = candles[i - 1].close
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)

    # 최근 period개의 TR 평균
    recent = true_ranges[-period:]
    return sum(recent) / len(recent)


def detect_regime(candles: list[OHLCV], ma_period: int = 60) -> MarketRegime:
    """시장 Regime 판별: 60일 이동평균 대비 현재가 위치.

    Args:
        candles: 과거→현재 순서
    """
    if len(candles) < ma_period:
        return MarketRegime.SIDE

    closes = [c.close for c in candles]
    ma = sum(closes[-ma_period:]) / ma_period
    current = closes[-1]

    pct = (current - ma) / ma * 100

    if pct > 5:
        return MarketRegime.BULL
    elif pct < -5:
        return MarketRegime.BEAR
    else:
        return MarketRegime.SIDE


def find_peak_day(candles: list[OHLCV], market_cap: float) -> tuple[int, float]:
    """시총 대비 거래대금이 가장 큰 날(peak day) 찾기.

    Args:
        candles: 과거→현재 순서
        market_cap: 시가총액

    Returns:
        (peak_day_index, turnover_ratio)
    """
    if not candles or market_cap <= 0:
        return -1, 0.0

    peak_idx = -1
    peak_turnover = 0.0

    for i, c in enumerate(candles):
        turnover_ratio = c.turnover / market_cap if c.turnover > 0 else 0.0
        if turnover_ratio > peak_turnover:
            peak_turnover = turnover_ratio
            peak_idx = i

    return peak_idx, peak_turnover


def is_bullish_candle(candle: OHLCV) -> bool:
    """양봉 여부."""
    return candle.close >= candle.open


def calc_volume_multiple(candle: OHLCV, avg_volume: float) -> float:
    """거래량 배수 (현재 거래량 / 평균 거래량)."""
    if avg_volume <= 0:
        return 0.0
    return candle.volume / avg_volume


def calc_sizing(current_price: float, min_amount: float = 300_000, max_amount: float = 500_000) -> int:
    """금액 기반 주문 수량 계산.

    Args:
        current_price: 현재가
        min_amount: 최소 주문 금액 (기본 30만원)
        max_amount: 최대 주문 금액 (기본 50만원)

    Returns:
        주문 수량 (주)
    """
    if current_price <= 0:
        return 0
    target_amount = (min_amount + max_amount) / 2
    qty = int(target_amount / current_price)
    return max(qty, 1)
