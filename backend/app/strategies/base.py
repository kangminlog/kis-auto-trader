from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class Signal(StrEnum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class StrategyResult:
    signal: Signal
    reason: str
    confidence: float = 0.0  # 0.0 ~ 1.0


class BaseStrategy(ABC):
    """매매 전략 베이스 클래스. 모든 전략은 이 클래스를 상속."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    def analyze(self, prices: list[float]) -> StrategyResult:
        """가격 데이터를 분석하여 매매 시그널 반환.

        Args:
            prices: 최신 순으로 정렬된 종가 리스트 (prices[0]이 최신)
        """
        ...

    def validate_prices(self, prices: list[float], min_length: int) -> bool:
        return len(prices) >= min_length
