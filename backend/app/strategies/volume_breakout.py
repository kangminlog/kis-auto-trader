"""Volume Breakout Retest 전략.

핵심: 과거 N일 중 거래대금이 폭발한 날(peak day)을 찾고,
충분히 횡보한 뒤 다시 그 가격대에 접근하면 매수.
"""

from dataclasses import dataclass

from app.strategies.base import BaseStrategy, Signal, StrategyResult
from app.strategies.indicators import (
    OHLCV,
    MarketRegime,
    atr,
    calc_sizing,
    detect_regime,
    find_peak_day,
    is_bullish_candle,
)

# Regime별 TP/SL ATR 배수
REGIME_PARAMS: dict[MarketRegime, tuple[float, float]] = {
    MarketRegime.BULL: (5.0, 2.0),
    MarketRegime.BEAR: (4.0, 2.5),
    MarketRegime.SIDE: (3.0, 1.8),
}


@dataclass
class VolumeBreakoutResult:
    """전략 분석 결과 상세."""

    signal: Signal
    reason: str
    confidence: float = 0.0
    tp_price: float = 0.0  # Take Profit 가격
    sl_price: float = 0.0  # Stop Loss 가격
    suggested_qty: int = 0  # 추천 주문 수량
    regime: MarketRegime = MarketRegime.SIDE


class VolumeBreakoutRetestStrategy(BaseStrategy):
    """Volume Breakout Retest 전략."""

    name = "volume_breakout_retest"
    description = "거래대금 폭발일 앵커 → 횡보 → 재접근 시 매수 (6단계 필터)"

    def __init__(
        self,
        lookback: int = 132,
        min_turnover_pct: float = 10.0,
        fomo_gain_pct: float = 5.0,
        fomo_vol_multiple: float = 3.0,
        min_days_since_peak: int = 15,
        max_breakthrough_pct: float = 15.0,
        proximity_pct: float = 3.0,
        min_amount_krw: float = 300_000,
        max_amount_krw: float = 500_000,
    ):
        self.lookback = lookback
        self.min_turnover_pct = min_turnover_pct
        self.fomo_gain_pct = fomo_gain_pct
        self.fomo_vol_multiple = fomo_vol_multiple
        self.min_days_since_peak = min_days_since_peak
        self.max_breakthrough_pct = max_breakthrough_pct
        self.proximity_pct = proximity_pct
        self.min_amount_krw = min_amount_krw
        self.max_amount_krw = max_amount_krw

    def analyze(self, prices: list[float]) -> StrategyResult:
        """BaseStrategy 인터페이스 호환. 단순 가격 리스트만으로는 제한적."""
        if len(prices) < self.min_days_since_peak + 5:
            return StrategyResult(signal=Signal.HOLD, reason="데이터 부족")
        return StrategyResult(signal=Signal.HOLD, reason="OHLCV 데이터 필요 (analyze_candles 사용)")

    def analyze_candles(self, candles: list[OHLCV], market_cap: float) -> VolumeBreakoutResult:
        """OHLCV 캔들 데이터 기반 전략 분석.

        Args:
            candles: 과거→현재 순서
            market_cap: 시가총액
        """
        if len(candles) < self.min_days_since_peak + 5:
            return VolumeBreakoutResult(signal=Signal.HOLD, reason="데이터 부족")

        # lookback 범위 제한
        window = candles[-self.lookback :] if len(candles) > self.lookback else candles

        # Step 1: Peak day 찾기 + turnover 체크
        peak_idx, turnover_ratio = find_peak_day(window, market_cap)
        if peak_idx < 0:
            return VolumeBreakoutResult(signal=Signal.HOLD, reason="peak day 없음")

        turnover_pct = turnover_ratio * 100
        if turnover_pct < self.min_turnover_pct:
            return VolumeBreakoutResult(
                signal=Signal.HOLD,
                reason=f"turnover {turnover_pct:.1f}% < {self.min_turnover_pct}%",
            )

        peak_candle = window[peak_idx]

        # Step 2: 양봉 체크
        if not is_bullish_candle(peak_candle):
            return VolumeBreakoutResult(signal=Signal.HOLD, reason="peak day 음봉, 투매")

        # Step 3: FOMO 제외 (오늘 기준)
        today = window[-1]
        today_gain = (today.close - today.open) / today.open * 100 if today.open > 0 else 0
        avg_vol = sum(c.volume for c in window) / len(window) if window else 1
        vol_multiple = today.volume / avg_vol if avg_vol > 0 else 0

        if today_gain >= self.fomo_gain_pct and vol_multiple < self.fomo_vol_multiple:
            return VolumeBreakoutResult(
                signal=Signal.HOLD,
                reason=f"FOMO: +{today_gain:.1f}% vol x{vol_multiple:.1f}",
            )

        # Step 4: 횡보 충분 체크
        days_since_peak = len(window) - 1 - peak_idx
        if days_since_peak < self.min_days_since_peak:
            return VolumeBreakoutResult(
                signal=Signal.HOLD,
                reason=f"days_since={days_since_peak} < {self.min_days_since_peak}",
            )

        # Step 5: 추격 금지 (peak 이후 최고가 체크)
        post_peak = window[peak_idx + 1 :]
        if post_peak:
            max_after_peak = max(c.high for c in post_peak)
            breakthrough_pct = (max_after_peak - peak_candle.close) / peak_candle.close * 100
            if breakthrough_pct >= self.max_breakthrough_pct:
                return VolumeBreakoutResult(
                    signal=Signal.HOLD,
                    reason=f"breakthrough {breakthrough_pct:.1f}% >= {self.max_breakthrough_pct}%",
                )

        # Step 6: 근접도 체크
        current_price = today.close
        proximity = (current_price - peak_candle.close) / peak_candle.close * 100
        if abs(proximity) > self.proximity_pct:
            return VolumeBreakoutResult(
                signal=Signal.HOLD,
                reason=f"proximity {proximity:+.1f}% too far (±{self.proximity_pct}%)",
            )

        # 모든 조건 통과 → BUY
        regime = detect_regime(candles)
        k_tp, k_sl = REGIME_PARAMS[regime]
        current_atr = atr(candles)

        tp_price = current_price + k_tp * current_atr
        sl_price = current_price - k_sl * current_atr
        suggested_qty = calc_sizing(current_price, self.min_amount_krw, self.max_amount_krw)

        return VolumeBreakoutResult(
            signal=Signal.BUY,
            reason=(
                f"재접근 매수 (peak turnover {turnover_pct:.1f}%, "
                f"{days_since_peak}일 횡보, proximity {proximity:+.1f}%)"
            ),
            confidence=min(turnover_pct / 20, 1.0),
            tp_price=round(tp_price),
            sl_price=round(sl_price),
            suggested_qty=suggested_qty,
            regime=regime,
        )
