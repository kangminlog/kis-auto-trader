from dataclasses import dataclass

from app.strategies.base import BaseStrategy, StrategyResult


@dataclass
class StrategyRunResult:
    stock_code: str
    strategy_name: str
    result: StrategyResult


STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {}


def register_strategy(cls: type[BaseStrategy]) -> type[BaseStrategy]:
    STRATEGY_REGISTRY[cls.name] = cls
    return cls


def get_strategy(name: str, **kwargs) -> BaseStrategy:
    if name not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy: {name}. Available: {list(STRATEGY_REGISTRY.keys())}")
    return STRATEGY_REGISTRY[name](**kwargs)


def run_strategy(strategy: BaseStrategy, stock_code: str, prices: list[float]) -> StrategyRunResult:
    result = strategy.analyze(prices)
    return StrategyRunResult(stock_code=stock_code, strategy_name=strategy.name, result=result)


def run_all_strategies(stock_code: str, prices: list[float]) -> list[StrategyRunResult]:
    results = []
    for name, cls in STRATEGY_REGISTRY.items():
        strategy = cls()
        results.append(run_strategy(strategy, stock_code, prices))
    return results


# 전략 등록
from app.strategies.golden_cross import GoldenCrossStrategy  # noqa: E402
from app.strategies.momentum import MomentumStrategy  # noqa: E402

register_strategy(GoldenCrossStrategy)
register_strategy(MomentumStrategy)
