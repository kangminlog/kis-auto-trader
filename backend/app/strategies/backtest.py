from dataclasses import dataclass, field

from app.strategies.base import BaseStrategy, Signal


@dataclass
class Trade:
    day: int
    signal: Signal
    price: float
    reason: str


@dataclass
class BacktestMetrics:
    total_return: float  # 총 수익률 (%)
    max_drawdown: float  # 최대 낙폭 (%)
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float  # 승률 (%)


@dataclass
class BacktestResult:
    strategy_name: str
    stock_code: str
    initial_capital: float
    final_capital: float
    metrics: BacktestMetrics
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)


def run_backtest(
    strategy: BaseStrategy,
    stock_code: str,
    prices: list[float],
    initial_capital: float = 10_000_000,
) -> BacktestResult:
    """과거 데이터로 전략을 백테스트.

    Args:
        prices: 과거→현재 순서 (prices[0]이 가장 오래된 데이터)
    """
    capital = initial_capital
    position = 0  # 보유 수량
    buy_price = 0.0
    trades: list[Trade] = []
    equity_curve: list[float] = [capital]
    wins = 0
    losses = 0

    for i in range(len(prices)):
        # 전략에 전달할 데이터: 현재 시점까지의 가격 (최신순)
        window = list(reversed(prices[: i + 1]))
        result = strategy.analyze(window)

        if result.signal == Signal.BUY and position == 0:
            # 전액 매수
            position = int(capital / prices[i])
            if position > 0:
                buy_price = prices[i]
                capital -= position * buy_price
                trades.append(Trade(day=i, signal=Signal.BUY, price=buy_price, reason=result.reason))

        elif result.signal == Signal.SELL and position > 0:
            # 전량 매도
            sell_price = prices[i]
            capital += position * sell_price
            if sell_price > buy_price:
                wins += 1
            else:
                losses += 1
            trades.append(Trade(day=i, signal=Signal.SELL, price=sell_price, reason=result.reason))
            position = 0

        # 현재 자산 = 현금 + 보유주식 평가
        equity = capital + position * prices[i]
        equity_curve.append(equity)

    # 마지막에 미청산 포지션 정리
    if position > 0:
        capital += position * prices[-1]
        if prices[-1] > buy_price:
            wins += 1
        else:
            losses += 1
        trades.append(Trade(day=len(prices) - 1, signal=Signal.SELL, price=prices[-1], reason="백테스트 종료 청산"))
        equity_curve.append(capital)

    total_trades = wins + losses
    metrics = BacktestMetrics(
        total_return=(capital - initial_capital) / initial_capital * 100,
        max_drawdown=_calculate_mdd(equity_curve),
        total_trades=total_trades,
        winning_trades=wins,
        losing_trades=losses,
        win_rate=(wins / total_trades * 100) if total_trades > 0 else 0,
    )

    return BacktestResult(
        strategy_name=strategy.name,
        stock_code=stock_code,
        initial_capital=initial_capital,
        final_capital=capital,
        metrics=metrics,
        trades=trades,
        equity_curve=equity_curve,
    )


def _calculate_mdd(equity_curve: list[float]) -> float:
    """최대 낙폭(MDD) 계산."""
    if not equity_curve:
        return 0.0

    peak = equity_curve[0]
    max_dd = 0.0

    for value in equity_curve:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak * 100
        if drawdown > max_dd:
            max_dd = drawdown

    return max_dd
