import pytest
import responses
from pyarrow_client.connect import ArrowClient
from pyarrow_client.constants import Exchange, OrderType, ProductType, Retention, TransactionType, Variety
from pyarrow_client.exceptions import DataException, GeneralException

@pytest.fixture
def arrow_client():
    client = ArrowClient(app_id="test_app_id")
    client.set_token("test_token")
    return client

def test_client_init():
    client = ArrowClient(app_id="test_app", timeout=20, debug=True)
    assert client.app_id == "test_app"
    assert client.timeout == 20
    assert client.debug is True
    assert client.get_token() == ""
    
    client.set_token("new_token")
    assert client.get_token() == "new_token"

@responses.activate
def test_place_order(arrow_client):
    url = f"{arrow_client.root_url}/order/regular"
    
    mock_response = {
        "status": "success",
        "data": {
            "orderNo": "123456789"
        }
    }
    
    responses.add(
        responses.POST,
        url,
        json=mock_response,
        status=200
    )
    
    order_id = arrow_client.place_order(
        exchange=Exchange.NSE,
        symbol="RELIANCE-EQ",
        quantity=10,
        disclosed_quantity=0,
        product=ProductType.CNC,
        order_type=OrderType.MARKET,
        variety=Variety.REGULAR,
        transaction_type=TransactionType.BUY,
        price=0.0,
        validity=Retention.DAY
    )
    
    assert order_id == "123456789"
    assert len(responses.calls) == 1

@responses.activate
def test_place_order_mcxfo(arrow_client):
    url = f"{arrow_client.root_url}/order/regular"
    mock_response = {
        "status": "success",
        "data": {"orderNo": "26072701000257"}
    }
    responses.add(responses.POST, url, json=mock_response, status=200)

    order_id = arrow_client.place_order(
        exchange=Exchange.MCXFO,
        symbol="GOLDPETAL31JUL26F",
        quantity=1,
        disclosed_quantity=0,
        product=ProductType.MIS,
        order_type=OrderType.LIMIT,
        variety=Variety.REGULAR,
        transaction_type=TransactionType.BUY,
        price=14300.0,
        validity=Retention.DAY,
        trigger_price=0.0,
    )

    assert order_id == "26072701000257"
    assert len(responses.calls) == 1
    body = responses.calls[0].request.body
    import json
    payload = json.loads(body)
    assert payload["exchange"] == "MCXFO"
    assert payload["symbol"] == "GOLDPETAL31JUL26F"
    assert payload["product"] == "I"
    assert payload["order"] == "LMT"
    assert payload["triggerPrice"] == "0.0"

@responses.activate
def test_get_order_book(arrow_client):
    url = f"{arrow_client.root_url}/user/orders"
    
    mock_response = {
        "status": "success",
        "data": [
            {
                "orderNo": "12345",
                "status": "COMPLETED",
                "tradingSymbol": "RELIANCE-EQ",
                "price": 2500.50
            }
        ]
    }
    
    responses.add(
        responses.GET,
        url,
        json=mock_response,
        status=200
    )
    
    orders = arrow_client.get_order_book()
    assert len(orders) == 1
    assert orders[0]["orderNo"] == "12345"

@responses.activate
def test_api_error_handling(arrow_client):
    url = f"{arrow_client.root_url}/user/orders"
    
    mock_response = {
        "status": "error",
        "message": "Invalid token",
        "errorCode": "401"
    }
    
    responses.add(
        responses.GET,
        url,
        json=mock_response,
        status=401
    )
    
    with pytest.raises(GeneralException) as excinfo:
        arrow_client.get_order_book()
        
    assert excinfo.value.code == 401
    assert "Invalid token" in str(excinfo.value)
