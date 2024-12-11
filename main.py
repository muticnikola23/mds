from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.params import Path
from sqlalchemy import delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from dependencies.database import get_db
from models.stocks import Stock, StockHistory

app = FastAPI()

stock_not_found = "stock_not_found"


@app.get("/stock/")
async def read_stocks(
    skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)
):
    """
    @param skip:
    @param limit:
    @param db:
    @return:
    """
    result = await db.execute(select(Stock).offset(skip).limit(limit))
    stocks = result.scalars().all()
    return stocks


@app.delete("/{stock_id}", status_code=204)
async def delete_stock(stock_id: int, db: AsyncSession = Depends(get_db)):
    """
    @param stock_id:
    @param db:
    @return:
    """

    stock = await db.get(Stock, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail=stock_not_found)

    await db.execute(
        delete(StockHistory).where(StockHistory.stock_id == stock_id)
    )

    await db.delete(stock)
    await db.commit()

    return {
        "message": f"Stock with id {stock_id} and related histories deleted successfully"
    }


@app.put("/{stock_id}", response_model=dict)
async def update_stock(
    stock_id: int,
    stock_data: dict,  # Accept raw dictionary for update
    db: AsyncSession = Depends(get_db),
) -> object:
    """
    @param stock_id:
    @param stock_data:
    @param db:
    @return:
    """

    stock = await db.get(Stock, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail=stock_not_found)

    for key, value in stock_data.items():
        if key == "founded":
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid date format for field '{key}'. Expected ISO 8601 format.",
                )
        if hasattr(stock, key):
            setattr(stock, key, value)

    try:
        await db.commit()
        await db.refresh(stock)
        return {"message": f"Stock with ID {stock_id} updated successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@app.get("/{stock_id}")
async def read_stock(stock_id: int, db: AsyncSession = Depends(get_db)):
    """

    @param stock_id:
    @param db:
    @return:
    """

    stock = await db.get(Stock, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail=stock_not_found)

    stock_data = {
        "id": stock.id,
        "name": stock.name,
        "symbol": stock.symbol,
        "founded": stock.founded.isoformat() if stock.founded else None,
        "description": stock.description,
    }

    return stock_data


@app.post("/create-stock/", status_code=status.HTTP_201_CREATED)
async def create_stock(
    stock_data: dict = Body(...), db: AsyncSession = Depends(get_db)
):
    """
    Create a new stock using raw JSON input without schemas.
    @param stock_data:
    @param db:
    @return:
    """

    required_fields = ["name", "symbol", "founded"]
    missing_fields = [
        field for field in required_fields if field not in stock_data
    ]
    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing_fields)}",
        )

    try:
        stock_data["founded"] = datetime.fromisoformat(stock_data["founded"])
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=400,
            detail="Invalid 'founded' date format. Expected ISO 8601 format (e.g., '2023-01-01T00:00:00').",
        )

    try:
        new_stock = Stock(
            name=stock_data["name"],
            symbol=stock_data["symbol"],
            founded=stock_data["founded"],
            description=stock_data.get("description"),  # Optional field
        )
        db.add(new_stock)
        await db.commit()
        await db.refresh(new_stock)
        return {
            "id": new_stock.id,
            "name": new_stock.name,
            "symbol": new_stock.symbol,
            "founded": (
                new_stock.founded.isoformat() if new_stock.founded else None
            ),
            "description": new_stock.description,
        }
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Stock with the same symbol already exists.",
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {e}",
        )


@app.get("/stock-history/")
async def read_stock_history(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    @param skip:
    @param limit:
    @param db:
    @return:
    """
    try:

        result = await db.execute(
            select(
                StockHistory.date,
                StockHistory.open,
                StockHistory.high,
                StockHistory.low,
                StockHistory.close,
                StockHistory.adjusted_close,
                StockHistory.volume,
            )
            .order_by(StockHistory.date.desc())
            .offset(skip)
            .limit(limit)
        )
        stock_history_records = result.fetchall()

        stock_history_list = [
            {
                "date": (
                    record.date.strftime("%Y-%m-%d") if record.date else None
                ),
                "open": record.open,
                "high": record.high,
                "low": record.low,
                "close": record.close,
                "adjusted_close": record.adjusted_close,
                "volume": record.volume,
            }
            for record in stock_history_records
        ]

        return stock_history_list

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving stock history: {e}",
        )


@app.get("/{symbol}/{start_date}/{end_date}")
async def stock_history_analysis(
    symbol: str = Path(..., description="Stock symbol"),
    start_date: str = Path(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Path(..., description="End date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
):
    """
    @param symbol:
    @param start_date:
    @param end_date:
    @param db:
    @return:
    """

    stock_exists = await db.execute(
        select(Stock.id).filter(func.lower(Stock.symbol) == func.lower(symbol))
    )
    if not stock_exists.scalar():
        raise HTTPException(
            status_code=404, detail=f"Stock with symbol '{symbol}' not found"
        )

    try:
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Dates must be in YYYY-MM-DD format"
        )

    if start_date_dt >= end_date_dt:
        raise HTTPException(
            status_code=400, detail="start_date must be before end_date"
        )

    try:
        interval = end_date_dt - start_date_dt
        prev_start_date = start_date_dt - interval
        prev_end_date = start_date_dt - timedelta(days=1)
        next_start_date = end_date_dt + timedelta(days=1)
        next_end_date = end_date_dt + interval
    except OverflowError:
        raise HTTPException(
            status_code=400, detail="date older than the record"
        )

    async def query_best_prices(start_date, end_date):

        query = (
            select(
                StockHistory.date,
                func.min(StockHistory.low).label("min_low"),
                func.max(StockHistory.high).label("max_high"),
                func.first_value(StockHistory.close)
                .over(order_by=StockHistory.low.asc())
                .label("min_low_closing_price"),
                func.first_value(StockHistory.close)
                .over(order_by=StockHistory.high.desc())
                .label("max_high_closing_price"),
            )
            .join(Stock, Stock.id == StockHistory.stock_id)
            .filter(
                func.lower(Stock.symbol) == func.lower(symbol),
                StockHistory.date.between(start_date, end_date),
            )
            .group_by(StockHistory.date)
        )

        result = await db.execute(query)
        rows = result.fetchall()

        min_low_row = min(rows, key=lambda row: row.min_low, default=None)
        max_high_row = max(rows, key=lambda row: row.max_high, default=None)

        if not min_low_row or not max_high_row:
            return None

        profit = (
            max_high_row.max_high_closing_price
            - min_low_row.min_low_closing_price
            if max_high_row.max_high_closing_price
            and min_low_row.min_low_closing_price
            else None
        )

        return {
            "best_buying_price": {
                "date": min_low_row.date.isoformat() if min_low_row else None,
                "closing_price": (
                    min_low_row.min_low_closing_price if min_low_row else None
                ),
            },
            "best_selling_price": {
                "date": (
                    max_high_row.date.isoformat() if max_high_row else None
                ),
                "closing_price": (
                    max_high_row.max_high_closing_price
                    if max_high_row
                    else None
                ),
            },
            "profit": profit,
        }

    async def calculate_max_profit(start_date, end_date, target_symbol=None):
        query = (
            select(
                StockHistory.date,
                StockHistory.close.label("closing_price"),
                func.lower(Stock.symbol).label("symbol"),
            )
            .join(Stock, Stock.id == StockHistory.stock_id)
            .filter(StockHistory.date.between(start_date, end_date))
            .order_by(Stock.symbol, StockHistory.date)
        )

        results = await db.execute(query)
        rows = results.fetchall()

        profits = {}
        for row in rows:
            symbol, closing_price = row[2], row[1]
            if symbol not in profits:
                profits[symbol] = {"profit": 0, "last_price": closing_price}
            else:
                profit_diff = closing_price - profits[symbol]["last_price"]
                if profit_diff > 0:
                    profits[symbol]["profit"] += profit_diff
                profits[symbol]["last_price"] = closing_price

        if target_symbol:
            return profits.get(target_symbol.lower(), {}).get("profit", 0)

        return profits

    current_period = await query_best_prices(start_date_dt, end_date_dt)
    prev_period = await query_best_prices(prev_start_date, prev_end_date)
    next_period = await query_best_prices(next_start_date, next_end_date)

    if not current_period:
        raise HTTPException(
            status_code=404,
            detail="There is no record for the selected period",
        )

    current_max_profit = await calculate_max_profit(
        start_date_dt, end_date_dt, target_symbol=symbol
    )
    prev_max_profit = await calculate_max_profit(
        prev_start_date, prev_end_date, target_symbol=symbol
    )
    next_max_profit = await calculate_max_profit(
        next_start_date, next_end_date, target_symbol=symbol
    )

    all_profits = await calculate_max_profit(start_date_dt, end_date_dt)
    higher_profit_symbols = [
        sym
        for sym, data in all_profits.items()
        if data["profit"] > current_max_profit
    ]

    response = {
        "analysis": {
            "current_period": {
                **current_period,
                "multy_trade_max_profit": current_max_profit,
            }
        },
        "higher_profit_symbols": higher_profit_symbols,
        "metadata": {
            "symbol": symbol.upper(),
            "start_date": start_date_dt.isoformat(),
            "end_date": end_date_dt.isoformat(),
        },
    }
    if prev_period:
        response["analysis"].update(
            {
                "previous_period": {
                    **prev_period,
                    "multy_trade_max_profit": prev_max_profit,
                }
            }
        )

    if next_period:
        response["analysis"].update(
            {
                "next_period": {
                    **next_period,
                    "multy_trade_max_profit": next_max_profit,
                }
            }
        )

    return response
