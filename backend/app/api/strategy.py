from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.services.market_data import DummyMarketDataProvider
from app.strategies.backtest import BacktestMetrics, run_backtest
from app.strategies.base import Signal
from app.strategies.runner import STRATEGY_REGISTRY, get_strategy, run_all_strategies

router = APIRouter(prefix="/api/strategy", tags=["strategy"], dependencies=[Depends(get_current_user)])


class StrategyInfo(BaseModel):
    name: str
    description: str


@router.get("/list", response_model=list[StrategyInfo])
def list_strategies():
    return [StrategyInfo(name=cls.name, description=cls.description) for cls in STRATEGY_REGISTRY.values()]


class AnalyzeRequest(BaseModel):
    stock_code: str
    strategy_name: str | None = None
    params: dict | None = None


class AnalyzeResult(BaseModel):
    stock_code: str
    strategy_name: str
    signal: Signal
    reason: str
    confidence: float


@router.post("/analyze", response_model=list[AnalyzeResult])
def analyze(req: AnalyzeRequest):
    # 더미 시세로 가격 데이터 생성
    market = DummyMarketDataProvider()
    prices = [market.get_price(req.stock_code).current_price for _ in range(30)]

    if req.strategy_name:
        strategy = get_strategy(req.strategy_name, **(req.params or {}))
        from app.strategies.runner import run_strategy

        run_result = run_strategy(strategy, req.stock_code, prices)
        return [
            AnalyzeResult(
                stock_code=run_result.stock_code,
                strategy_name=run_result.strategy_name,
                signal=run_result.result.signal,
                reason=run_result.result.reason,
                confidence=run_result.result.confidence,
            )
        ]

    results = run_all_strategies(req.stock_code, prices)
    return [
        AnalyzeResult(
            stock_code=r.stock_code,
            strategy_name=r.strategy_name,
            signal=r.result.signal,
            reason=r.result.reason,
            confidence=r.result.confidence,
        )
        for r in results
    ]


class BacktestRequest(BaseModel):
    stock_code: str
    strategy_name: str
    days: int = 100
    initial_capital: float = 10_000_000
    params: dict | None = None


class TradeInfo(BaseModel):
    day: int
    signal: Signal
    price: float
    reason: str


class BacktestResponse(BaseModel):
    strategy_name: str
    stock_code: str
    initial_capital: float
    final_capital: float
    metrics: BacktestMetrics
    trades: list[TradeInfo]


@router.post("/backtest", response_model=BacktestResponse)
def backtest(req: BacktestRequest):
    strategy = get_strategy(req.strategy_name, **(req.params or {}))

    # 더미 가격 생성 (과거→현재 순서)
    market = DummyMarketDataProvider()
    prices = [market.get_price(req.stock_code).current_price for _ in range(req.days)]

    result = run_backtest(strategy, req.stock_code, prices, req.initial_capital)

    return BacktestResponse(
        strategy_name=result.strategy_name,
        stock_code=result.stock_code,
        initial_capital=result.initial_capital,
        final_capital=result.final_capital,
        metrics=result.metrics,
        trades=[TradeInfo(day=t.day, signal=t.signal, price=t.price, reason=t.reason) for t in result.trades],
    )
