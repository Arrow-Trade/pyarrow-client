import pytest
import responses
from pyarrow_client.connect import ArrowClient
from pyarrow_client.exceptions import GeneralException

@pytest.fixture
def arrow_client():
    client = ArrowClient(app_id="test_app_id")
    client.set_token("test_token")
    return client

@responses.activate
def test_get_user_details(arrow_client):
    url = f"{arrow_client.root_url}/user/details"
    mock_response = {
        "status": "success",
        "data": {"userId": "TEST1234", "email": "test@example.com", "name": "Test User"}
    }
    responses.add(responses.GET, url, json=mock_response, status=200)
    
    details = arrow_client.get_user_details()
    assert details["userId"] == "TEST1234"
    assert details["name"] == "Test User"
    assert len(responses.calls) == 1

@responses.activate
def test_get_holdings(arrow_client):
    url = f"{arrow_client.root_url}/user/holdings"
    mock_response = {
        "status": "success",
        "data": [{"tradingSymbol": "RELIANCE-EQ", "quantity": 10, "averagePrice": 2500.5}]
    }
    responses.add(responses.GET, url, json=mock_response, status=200)
    
    holdings = arrow_client.get_holdings()
    assert len(holdings) == 1
    assert holdings[0]["tradingSymbol"] == "RELIANCE-EQ"

@responses.activate
def test_get_user_limits(arrow_client):
    url = f"{arrow_client.root_url}/user/limits"
    mock_response = {
        "status": "success",
        "data": {"allocations": [], "margin": {"allocated": "100000.0"}}
    }
    responses.add(responses.GET, url, json=mock_response, status=200)
    
    limits = arrow_client.get_user_limits()
    assert limits["margin"]["allocated"] == "100000.0"

@responses.activate
def test_get_positions(arrow_client):
    url = f"{arrow_client.root_url}/user/positions"
    mock_response = {
        "status": "success",
        "data": [{
            "userID": "TEST",
            "token": "1398464",
            "exchange": "MCXFO",
            "symbol": "GOLDPETAL30JUN26F",
            "segment": "FO",
            "product": "M",
            "qty": "0",
            "avgPrice": "0",
            "dayBuyQty": "1",
            "daySellQty": "1",
            "ltp": "0",
        }]
    }
    responses.add(responses.GET, url, json=mock_response, status=200)
    
    positions = arrow_client.get_positions()
    assert len(positions) == 1
    assert positions[0]["symbol"] == "GOLDPETAL30JUN26F"
    assert positions[0]["exchange"] == "MCXFO"

@responses.activate
def test_get_trade_book(arrow_client):
    url = f"{arrow_client.root_url}/user/trades"
    mock_response = {
        "status": "success",
        "data": [{"tradeId": "T123", "orderNo": "O123", "price": 100.5, "quantity": 10}]
    }
    responses.add(responses.GET, url, json=mock_response, status=200)
    
    trades = arrow_client.get_trade_book()
    assert len(trades) == 1
    assert trades[0]["tradeId"] == "T123"
