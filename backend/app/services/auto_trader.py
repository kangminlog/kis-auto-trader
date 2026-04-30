import logging

from sqlalchemy.orm import Session

from app.models.auto_trade import AutoTradeConfig, AutoTradeLog
from app.models.order import OrderSide, OrderType
from app.services.market_data import MarketDataProvider
from app.services.order_service import submit_order
from app.strategies.base import Signal
from app.strategies.runner import get_strategy, run_strategy

logger = logging.getLogger(__name__)


def run_auto_trade_cycle(db: Session, market: MarketDataProvider) -> list[AutoTradeLog]:
    """활성화된 모든 자동매매 설정에 대해 전략 실행 → 시그널 발생 시 주문."""
    configs = db.query(AutoTradeConfig).filter_by(is_active=True).all()
    logs = []

    for config in configs:
        log = _process_config(db, market, config)
        logs.append(log)

    db.commit()
    return logs


def _process_config(db: Session, market: MarketDataProvider, config: AutoTradeConfig) -> AutoTradeLog:
    try:
        # 시세 데이터 수집 (최근 30개)
        prices = [market.get_price(config.stock_code).current_price for _ in range(30)]

        # 전략 실행
        strategy = get_strategy(config.strategy_name)
        result = run_strategy(strategy, config.stock_code, prices)
        signal = result.result.signal
        reason = result.result.reason

        # 시그널에 따라 주문
        action = "skipped"
        order_id = None

        if signal == Signal.BUY:
            current_price = prices[0]
            affordable_qty = min(config.quantity, int(config.max_invest_amount / current_price))
            if affordable_qty > 0:
                order = submit_order(
                    db,
                    stock_code=config.stock_code,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=affordable_qty,
                )
                action = "order_placed"
                order_id = order.id
                logger.info("BUY %s x%d (전략: %s)", config.stock_code, affordable_qty, config.strategy_name)

        elif signal == Signal.SELL:
            order = submit_order(
                db,
                stock_code=config.stock_code,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=config.quantity,
            )
            action = "order_placed"
            order_id = order.id
            logger.info("SELL %s x%d (전략: %s)", config.stock_code, config.quantity, config.strategy_name)

    except Exception as e:
        signal = Signal.HOLD
        reason = str(e)
        action = "error"
        order_id = None
        logger.error("Auto trade error for %s: %s", config.stock_code, e)

    log = AutoTradeLog(
        config_id=config.id,
        stock_code=config.stock_code,
        strategy_name=config.strategy_name,
        signal=signal,
        reason=reason,
        action_taken=action,
        order_id=order_id,
    )
    db.add(log)
    return log
