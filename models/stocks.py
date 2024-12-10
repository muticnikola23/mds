from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    founded = Column(DateTime, nullable=False)
    description = Column(String)

    histories = relationship("StockHistory", back_populates="stock")


class StockHistory(Base):
    __tablename__ = "stock_histories"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    adjusted_close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)

    stock = relationship("Stock", back_populates="histories")
