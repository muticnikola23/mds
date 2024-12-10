import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_stocks():
    response = client.get("/stock/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_stock():
    stock_data = {
        "name": "TestStock",
        "symbol": "TS",
        "founded": "2023-01-01T00:00:00",
        "description": "A test stock.",
    }
    response = client.post("/create-stock/", json=stock_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "TestStock"
    assert data["symbol"] == "TS"


def test_read_stock():
    stock_id = 1  # Replace with an actual ID from your DB setup
    response = client.get(f"/{stock_id}")
    if response.status_code == 200:
        data = response.json()
        assert "name" in data
        assert "symbol" in data
    elif response.status_code == 404:
        assert response.json()["detail"] == "stock_not_found"


def test_update_stock():
    stock_id = 1  # Replace with an actual ID from your DB setup
    update_data = {
        "name": "UpdatedStockName",
        "description": "Updated description.",
    }
    response = client.put(f"/{stock_id}", json=update_data)
    if response.status_code == 200:
        assert (
            response.json()["message"]
            == f"Stock with ID {stock_id} updated successfully"
        )
    elif response.status_code == 404:
        assert response.json()["detail"] == "stock_not_found"


def test_delete_stock():
    stock_id = 1  # Replace with an actual ID from your DB setup
    response = client.delete(f"/{stock_id}")
    if response.status_code == 204:
        assert response.text == ""
    elif response.status_code == 404:
        assert response.json()["detail"] == "stock_not_found"


def test_stock_history():
    response = client.get("/stock-history/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_stock_history_analysis():
    symbol = "fbc"  # Replace with a valid stock symbol
    start_date = "2020-01-01"
    end_date = "2020-12-31"
    response = client.get(f"/{symbol}/{start_date}/{end_date}")
    if response.status_code == 200:
        data = response.json()
        assert "analysis" in data
        assert "metadata" in data
    elif response.status_code == 404:
        assert (
            response.json()["detail"]
            == f"Stock with symbol '{symbol}' not found"
        )
