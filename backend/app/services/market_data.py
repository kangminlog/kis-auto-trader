import random
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PriceInfo:
    code: str
    current_price: float
    high: float
    low: float
    volume: int


class MarketDataProvider(ABC):
    @abstractmethod
    def get_price(self, code: str) -> PriceInfo: ...


class DummyMarketDataProvider(MarketDataProvider):
    """더미 시세 데이터 생성기. 실제 API 없이 랜덤 시세를 반환."""

    DUMMY_STOCKS: dict[str, float] = {
        "005930": 70000,  # 삼성전자
        "000660": 130000,  # SK하이닉스
        "035420": 200000,  # NAVER
        "051910": 450000,  # LG화학
        "006400": 55000,  # 삼성SDI
    }

    def get_price(self, code: str) -> PriceInfo:
        base_price = self.DUMMY_STOCKS.get(code, 50000)
        fluctuation = random.uniform(-0.03, 0.03)
        current = round(base_price * (1 + fluctuation))
        high = round(current * random.uniform(1.0, 1.02))
        low = round(current * random.uniform(0.98, 1.0))
        volume = random.randint(100000, 5000000)
        return PriceInfo(
            code=code,
            current_price=current,
            high=high,
            low=low,
            volume=volume,
        )
