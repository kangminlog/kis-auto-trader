import logging

from sqlalchemy.orm import Session

from app.models.auto_trade import AutoTradeConfig, AutoTradeLog
from app.models.order import OrderSide, OrderType
from app.models.portfolio import PortfolioItem
from app.services.market_data import MarketDataProvider
from app.services.order_service import submit_order
from app.services.safety import check_can_trade, check_stop_loss_take_profit, safety
from app.strategies.base import Signal
from app.strategies.runner import get_strategy, run_strategy

logger = logging.getLogger(__name__)


def run_auto_trade_cycle(db: Session, market: MarketDataProvider) -> list[AutoTradeLog]:
    """활성화된 모든 자동매매 설정에 대해 전략 실행 → 시그널 발생 시 주문."""
    if safety.kill_switch:
        logger.warning("Kill switch active — skipping all auto trades")
        return []

    configs = db.query(AutoTradeConfig).filter_by(is_active=True).all()
    logs = []

    # 1. 손절/익절 체크
    _check_portfolio_safety(db, market)

    # 2. 전략 실행
    for config in configs:
        log = _process_config(db, market, config)
        logs.append(log)

    db.commit()
    return logs


def _check_portfolio_safety(db: Session, market: MarketDataProvider):
    """보유 종목 손절/익절 자동 매도."""
    items = db.query(PortfolioItem).all()
    for item in items:
        if item.quantity <= 0:
            continue
        price_info = market.get_price(item.stock_code)
        trigger = check_stop_loss_take_profit(
            db, item.stock_code, price_info.current_price, float(item.avg_price), item.quantity
        )
        if trigger:
            can_trade, reason = check_can_trade(price_info.current_price, item.quantity)
            if can_trade:
                order = submit_order(
                    db,
                    stock_code=item.stock_code,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=item.quantity,
                )
                safety.record_trade(price_info.current_price * item.quantity)
                logger.warning(
                    "%s %s x%d @ %s (order #%d)",
                    trigger.upper(),
                    item.stock_code,
                    item.quantity,
                    price_info.current_price,
                    order.id,
                )


def _process_config(db: Session, market: MarketDataProvider, config: AutoTradeConfig) -> AutoTradeLog:
    try:
        prices = [market.get_price(config.stock_code).current_price for _ in range(30)]

        strategy = get_strategy(config.strategy_name)
        result = run_strategy(strategy, config.stock_code, prices)
        signal = result.result.signal
        reason = result.result.reason

        action = "skipped"
        order_id = None

        if signal == Signal.BUY:
            current_price = prices[0]
            affordable_qty = min(config.quantity, int(config.max_invest_amount / current_price))
            if affordable_qty > 0:
                can_trade, block_reason = check_can_trade(current_price, affordable_qty)
                if can_trade:
                    order = submit_order(
                        db,
                        stock_code=config.stock_code,
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=affordable_qty,
                    )
                    safety.record_trade(current_price * affordable_qty)
                    action = "order_placed"
                    order_id = order.id
                else:
                    action = "blocked"
                    reason = block_reason

        elif signal == Signal.SELL:
            current_price = prices[0]
            can_trade, block_reason = check_can_trade(current_price, config.quantity)
            if can_trade:
                order = submit_order(
                    db,
                    stock_code=config.stock_code,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=config.quantity,
                )
                safety.record_trade(current_price * config.quantity)
                action = "order_placed"
                order_id = order.id
            else:
                action = "blocked"
                reason = block_reason

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
