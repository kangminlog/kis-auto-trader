from app.strategies.base import BaseStrategy, Signal, StrategyResult


class MomentumStrategy(BaseStrategy):
    """모멘텀 전략: N일간 수익률이 임계값을 넘으면 매수/매도."""

    name = "momentum"
    description = "N일 수익률 기반 모멘텀 전략"

    def __init__(self, lookback: int = 10, buy_threshold: float = 0.05, sell_threshold: float = -0.05):
        self.lookback = lookback
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def analyze(self, prices: list[float]) -> StrategyResult:
        if not self.validate_prices(prices, self.lookback + 1):
            return StrategyResult(signal=Signal.HOLD, reason="데이터 부족")

        current = prices[0]
        past = prices[self.lookback]
        returns = (current - past) / past

        if returns >= self.buy_threshold:
            return StrategyResult(
                signal=Signal.BUY,
                reason=f"{self.lookback}일 수익률 {returns:.1%} (매수 임계: {self.buy_threshold:.1%})",
                confidence=min(returns / self.buy_threshold * 0.5, 1.0),
            )

        if returns <= self.sell_threshold:
            return StrategyResult(
                signal=Signal.SELL,
                reason=f"{self.lookback}일 수익률 {returns:.1%} (매도 임계: {self.sell_threshold:.1%})",
                confidence=min(abs(returns) / abs(self.sell_threshold) * 0.5, 1.0),
            )

        return StrategyResult(signal=Signal.HOLD, reason=f"{self.lookback}일 수익률 {returns:.1%} (임계 미달)")
