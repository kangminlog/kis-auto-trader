from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.order import OrderSide, OrderStatus, OrderType
from app.services import order_service
from app.services.execution_engine import process_pending_orders
from app.services.market_data import DummyMarketDataProvider

router = APIRouter(prefix="/api", tags=["trading"], dependencies=[Depends(get_current_user)])


class OrderRequest(BaseModel):
    stock_code: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: float | None = None


class OrderResponse(BaseModel):
    id: int
    stock_code: str
    side: str
    order_type: str
    status: str
    quantity: int
    price: float | None

    model_config = {"from_attributes": True}


@router.post("/orders", response_model=OrderResponse)
def create_order(req: OrderRequest, db: Session = Depends(get_db)):
    try:
        order = order_service.submit_order(
            db,
            stock_code=req.stock_code,
            side=req.side,
            order_type=req.order_type,
            quantity=req.quantity,
            price=req.price,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return order


@router.delete("/orders/{order_id}", response_model=OrderResponse)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    try:
        order = order_service.cancel_order(db, order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return order


@router.get("/orders", response_model=list[OrderResponse])
def list_orders(status: OrderStatus | None = None, db: Session = Depends(get_db)):
    return order_service.get_orders(db, status=status)


@router.post("/execute")
def execute_pending_orders(db: Session = Depends(get_db)):
    market = DummyMarketDataProvider()
    executions = process_pending_orders(db, market)
    return {"executed": len(executions)}


class PriceResponse(BaseModel):
    code: str
    current_price: float
    high: float
    low: float
    volume: int


@router.get("/price/{stock_code}", response_model=PriceResponse)
def get_price(stock_code: str):
    market = DummyMarketDataProvider()
    return market.get_price(stock_code)


class PortfolioResponse(BaseModel):
    stock_code: str
    quantity: int
    avg_price: float

    model_config = {"from_attributes": True}


@router.get("/portfolio", response_model=list[PortfolioResponse])
def get_portfolio(db: Session = Depends(get_db)):
    from app.models.portfolio import PortfolioItem

    return db.query(PortfolioItem).all()
