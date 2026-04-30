"""KIS 잔고 동기화: 실제 증권사 잔고와 로컬 DB 동기화."""

import logging

from sqlalchemy.orm import Session

from app.models.portfolio import PortfolioItem
from app.services.kis_client import KisClient
from app.services.kis_order import KisOrderService

logger = logging.getLogger(__name__)


def sync_balance(db: Session, kis_client: KisClient) -> dict:
    """KIS 실제 잔고를 로컬 DB에 동기화.

    Returns:
        {"synced": int, "added": int, "removed": int}
    """
    order_service = KisOrderService(kis_client)
    result = order_service.get_balance()

    kis_holdings = {}
    for item in result.get("output1", []):
        code = item.get("pdno", "")
        qty = int(item.get("hldg_qty", "0"))
        avg_price = float(item.get("pchs_avg_pric", "0"))
        if qty > 0:
            kis_holdings[code] = {"quantity": qty, "avg_price": avg_price}

    # 로컬 포트폴리오 조회
    local_items = db.query(PortfolioItem).all()
    local_codes = {item.stock_code for item in local_items}

    added = 0
    removed = 0
    synced = 0

    # KIS에 있지만 로컬에 없는 종목 추가
    for code, data in kis_holdings.items():
        if code not in local_codes:
            db.add(PortfolioItem(stock_code=code, quantity=data["quantity"], avg_price=data["avg_price"]))
            added += 1
        else:
            # 기존 종목 수량/가격 업데이트
            item = db.query(PortfolioItem).filter_by(stock_code=code).first()
            item.quantity = data["quantity"]
            item.avg_price = data["avg_price"]
            synced += 1

    # 로컬에 있지만 KIS에 없는 종목 제거
    for item in local_items:
        if item.stock_code not in kis_holdings:
            db.delete(item)
            removed += 1

    db.commit()
    logger.info("Balance sync: %d synced, %d added, %d removed", synced, added, removed)
    return {"synced": synced, "added": added, "removed": removed}
