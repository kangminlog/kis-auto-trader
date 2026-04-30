from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_code: Mapped[str] = mapped_column(String(20), ForeignKey("stocks.code"), unique=True)
    quantity: Mapped[int] = mapped_column(default=0)
    avg_price: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
