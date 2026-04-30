from app.strategies.base import BaseStrategy, Signal, StrategyResult


class GoldenCrossStrategy(BaseStrategy):
    """골든크로스 전략: 단기 이동평균이 장기 이동평균을 상향 돌파하면 매수."""

    name = "golden_cross"
    description = "단기(5일)/장기(20일) 이동평균 교차 전략"

    def __init__(self, short_window: int = 5, long_window: int = 20):
        self.short_window = short_window
        self.long_window = long_window

    def analyze(self, prices: list[float]) -> StrategyResult:
        if not self.validate_prices(prices, self.long_window + 1):
            return StrategyResult(signal=Signal.HOLD, reason="데이터 부족")

        # 현재 이동평균
        short_ma = sum(prices[: self.short_window]) / self.short_window
        long_ma = sum(prices[: self.long_window]) / self.long_window

        # 전일 이동평균
        prev_short_ma = sum(prices[1 : self.short_window + 1]) / self.short_window
        prev_long_ma = sum(prices[1 : self.long_window + 1]) / self.long_window

        # 골든크로스: 단기MA가 장기MA를 상향 돌파
        if prev_short_ma <= prev_long_ma and short_ma > long_ma:
            spread = (short_ma - long_ma) / long_ma
            return StrategyResult(
                signal=Signal.BUY,
                reason=f"골든크로스 발생 (단기MA: {short_ma:.0f}, 장기MA: {long_ma:.0f})",
                confidence=min(spread * 10, 1.0),
            )

        # 데드크로스: 단기MA가 장기MA를 하향 돌파
        if prev_short_ma >= prev_long_ma and short_ma < long_ma:
            spread = (long_ma - short_ma) / long_ma
            return StrategyResult(
                signal=Signal.SELL,
                reason=f"데드크로스 발생 (단기MA: {short_ma:.0f}, 장기MA: {long_ma:.0f})",
                confidence=min(spread * 10, 1.0),
            )

        return StrategyResult(signal=Signal.HOLD, reason="교차 신호 없음")
