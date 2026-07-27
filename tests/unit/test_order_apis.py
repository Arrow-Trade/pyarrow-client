import pytest
import responses
from pyarrow_client.connect import ArrowClient
from pyarrow_client.constants import Exchange, OrderType, ProductType, Retention, TransactionType, Variety

@pytest.fixture
def arrow_client():
    client = ArrowClient(app_id="test_app_id")
    client.set_token("test_token")
    return client

@responses.activate
def test_modify_order(arrow_client):
    url = f"{arrow_client.root_url}/order/regular/12345"
    mock_response = {
        "status": "success",
        "message": "Order modified"
    }
    responses.add(responses.PATCH, url, json=mock_response, status=200)
    
    msg = arrow_client.modify_order(
        order_id="12345",
        exchange=Exchange.NSE,
        quantity=20,
        symbol="RELIANCE-EQ",
        price=105.5,
        disclosed_qty=0,
        product=ProductType.CNC,
        transaction_type=TransactionType.BUY,
        order_type=OrderType.LIMIT,
        validity=Retention.DAY
    )
    assert msg == "Order modified"

@responses.activate
def test_cancel_order(arrow_client):
    url = f"{arrow_client.root_url}/order/regular/12345"
    mock_response = {
        "status": "success",
        "message": "Order cancelled"
    }
    responses.add(responses.DELETE, url, json=mock_response, status=200)
    
    msg = arrow_client.cancel_order("12345")
    assert msg == "Order cancelled"

@responses.activate
def test_get_order_details(arrow_client):
    url = f"{arrow_client.root_url}/order/12345"
    mock_response = {
        "status": "success",
        "data": [{"orderNo": "12345", "status": "OPEN", "price": 100.0}]
    }
    responses.add(responses.GET, url, json=mock_response, status=200)
    
    details = arrow_client.get_order_details("12345")
    assert len(details) == 1
    assert details[0]["orderNo"] == "12345"
    assert details[0]["status"] == "OPEN"

@responses.activate
def test_order_margin(arrow_client):
    url = f"{arrow_client.root_url}/margin/order"
    mock_response = {
        "status": "success",
        "data": {"marginRequired": 5000.0}
    }
    responses.add(responses.POST, url, json=mock_response, status=200)
    
    margin = arrow_client.order_margin(
        exchange=Exchange.NSE,
        symbol="RELIANCE-EQ",
        quantity=10,
        product=ProductType.CNC,
        order_type=OrderType.MARKET,
        transaction_type=TransactionType.BUY,
        price=0.0
    )
    assert margin["marginRequired"] == 5000.0

@responses.activate
def test_basket_margin(arrow_client):
    url = f"{arrow_client.root_url}/margin/basket"
    mock_response = {
        "status": "success",
        "data": {"marginRequired": 10000.0}
    }
    responses.add(responses.POST, url, json=mock_response, status=200)
    
    orders = [{
        "exchange": Exchange.NSE,
        "symbol": "RELIANCE-EQ",
        "quantity": 10,
        "product": ProductType.CNC,
        "order_type": OrderType.MARKET,
        "transaction_type": TransactionType.BUY,
        "price": 0.0
    }]
    
    margin = arrow_client.basket_margin(orders)
    assert margin["marginRequired"] == 10000.0

@responses.activate
def test_modify_order_mcxfo(arrow_client):
    url = f"{arrow_client.root_url}/order/regular/26072701000257"
    mock_response = {
        "status": "success",
        "message": "Order modified"
    }
    responses.add(responses.PATCH, url, json=mock_response, status=200)

    msg = arrow_client.modify_order(
        order_id="26072701000257",
        exchange=Exchange.MCXFO,
        quantity=1,
        symbol="GOLDPETAL31JUL26F",
        price=14320.0,
        disclosed_qty=0,
        product=ProductType.MIS,
        transaction_type=TransactionType.BUY,
        order_type=OrderType.LIMIT,
        validity=Retention.DAY,
        trigger_price=0.0,
    )
    assert msg == "Order modified"
    import json
    payload = json.loads(responses.calls[0].request.body)
    assert payload["exchange"] == "MCXFO"
    assert payload["price"] == "14320.0"
    assert payload["symbol"] == "GOLDPETAL31JUL26F"

@responses.activate
def test_basket_margin_mcxfo(arrow_client):
    url = f"{arrow_client.root_url}/margin/basket"
    mock_response = {
        "status": "success",
        "data": {"marginRequired": 15000.0}
    }
    responses.add(responses.POST, url, json=mock_response, status=200)

    orders = [{
        "exchange": "MCXFO",
        "quantity": "1",
        "disclosedQty": "0",
        "product": "M",
        "symbol": "GOLDPETAL31JUL26F",
        "transactionType": "B",
        "order": "LMT",
        "price": "14300.0",
        "validity": "DAY",
    }]

    margin = arrow_client.basket_margin(orders, include_positions=False)
    assert margin["marginRequired"] == 15000.0
    import json
    payload = json.loads(responses.calls[0].request.body)
    assert payload["orders"][0]["exchange"] == "MCXFO"
    assert payload["includePositions"] is False

@responses.activate
def test_order_margin_mcxfo(arrow_client):
    url = f"{arrow_client.root_url}/margin/order"
    mock_response = {
        "status": "success",
        "data": {"marginRequired": 12000.0}
    }
    responses.add(responses.POST, url, json=mock_response, status=200)

    margin = arrow_client.order_margin(
        exchange=Exchange.MCXFO,
        symbol="GOLDPETAL31JUL26F",
        quantity=1,
        product=ProductType.NRML,
        order_type=OrderType.LIMIT,
        transaction_type=TransactionType.BUY,
        price=14300.0,
    )
    assert margin["marginRequired"] == 12000.0
    import json
    payload = json.loads(responses.calls[0].request.body)
    assert payload["exchange"] == "MCXFO"
