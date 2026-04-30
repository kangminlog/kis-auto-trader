import logging

from sqlalchemy.orm import Session

from app.models.auto_trade import AutoTradeConfig, AutoTradeLog
from app.models.order import OrderSide, OrderType
from app.models.portfolio import PortfolioItem
from app.services.market_data import MarketDataProvider
from app.services.notifier import notify
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
    """보유 종목 손절/익절 자동 매도. 종목별 가격 설정 우선, 없으면 글로벌 % 적용."""
    items = db.query(PortfolioItem).all()
    for item in items:
        if item.quantity <= 0:
            continue
        price_info = market.get_price(item.stock_code)
        current_price = price_info.current_price

        # 종목별 절대 가격 체크 (AutoTradeConfig에 설정된 경우)
        trigger = _check_per_stock_price(db, item.stock_code, current_price)

        # 종목별 설정 없으면 글로벌 % 체크
        if trigger is None:
            trigger = check_stop_loss_take_profit(
                db, item.stock_code, current_price, float(item.avg_price), item.quantity
            )

        if trigger:
            can_trade, reason = check_can_trade(current_price, item.quantity)
            if can_trade:
                order = submit_order(
                    db,
                    stock_code=item.stock_code,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=item.quantity,
                )
                safety.record_trade(current_price * item.quantity)
                logger.warning(
                    "%s %s x%d @ %s (order #%d)",
                    trigger.upper(),
                    item.stock_code,
                    item.quantity,
                    price_info.current_price,
                    order.id,
                )


def _check_per_stock_price(db: Session, stock_code: str, current_price: float) -> str | None:
    """종목별 절대 가격 손절/익절 체크."""
    config = db.query(AutoTradeConfig).filter_by(stock_code=stock_code, is_active=True).first()
    if config is None:
        return None

    if config.stop_loss_price and current_price <= config.stop_loss_price:
        logger.warning("STOP LOSS: %s @ %.0f (limit: %.0f)", stock_code, current_price, config.stop_loss_price)
        return "stop_loss"

    if config.take_profit_price and current_price >= config.take_profit_price:
        logger.info("TAKE PROFIT: %s @ %.0f (limit: %.0f)", stock_code, current_price, config.take_profit_price)
        return "take_profit"

    return None


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
                    notify(f"🔴 매수 {config.stock_code} x{affordable_qty} ({config.strategy_name})")
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
                notify(f"🔵 매도 {config.stock_code} x{config.quantity} ({config.strategy_name})")
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
