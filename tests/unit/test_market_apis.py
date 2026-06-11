import pytest
import responses
import urllib.parse
from pyarrow_client.connect import ArrowClient
from pyarrow_client.constants import Exchange, QuoteMode

@pytest.fixture
def arrow_client():
    client = ArrowClient(app_id="test_app_id")
    client.set_token("test_token")
    return client

@responses.activate
def test_get_instruments(arrow_client):
    url = f"{arrow_client.root_url}/all"
    mock_response = {
        "status": "success",
        "data": [{"instrument_token": 12345, "tradingsymbol": "RELIANCE"}]
    }
    responses.add(responses.GET, url, json=mock_response, status=200)
    
    data = arrow_client.get_instruments()
    assert len(data) == 1
    assert data[0]["instrument_token"] == 12345

@responses.activate
def test_get_quote(arrow_client):
    url = f"{arrow_client.root_url}/info/quote/{QuoteMode.LTP.value}"
    mock_response = {
        "status": "success",
        "data": {"price": 2500.5}
    }
    responses.add(responses.POST, url, json=mock_response, status=200)
    
    data = arrow_client.get_quote(QuoteMode.LTP, "RELIANCE-EQ", Exchange.NSE)
    assert data["price"] == 2500.5

@responses.activate
def test_get_quotes(arrow_client):
    url = f"{arrow_client.root_url}/info/quotes/{QuoteMode.FULL.value}"
    mock_response = {
        "status": "success",
        "data": [{"symbol": "RELIANCE-EQ", "price": 2500.5}]
    }
    # Using POST method for get_quotes as implemented in connect.py
    responses.add(responses.POST, url, json=mock_response, status=200)
    
    symbols = [("RELIANCE-EQ", Exchange.NSE), ("TCS-EQ", Exchange.NSE)]
    data = arrow_client.get_quotes(QuoteMode.FULL, symbols)
    assert len(data) == 1
    assert data[0]["symbol"] == "RELIANCE-EQ"

@responses.activate
def test_candle_data(arrow_client):
    # Notice candle_url is different from root_url
    url = f"{arrow_client._routes.get_candle_url()}/candle/NSE/12345/1?from=2023-01-01&to=2023-01-02&oi=0"
    mock_response = {
        "status": "success",
        "data": [{"t": 1672531200, "o": 2500, "h": 2510, "l": 2490, "c": 2505, "v": 1000}]
    }
    responses.add(responses.GET, url, json=mock_response, status=200)
    
    data = arrow_client.candle_data(
        exchange=Exchange.NSE,
        token="12345",
        interval="1",
        from_timestamp="2023-01-01",
        to_timestamp="2023-01-02"
    )
    assert len(data) == 1
    assert data[0]["c"] == 2505

@responses.activate
def test_get_holidays(arrow_client):
    url = f"{arrow_client.root_url}/info/holidays"
    mock_response = {
        "status": "success",
        "data": {"2023-01-26": "Republic Day"}
    }
    responses.add(responses.GET, url, json=mock_response, status=200)
    
    data = arrow_client.get_holidays()
    assert "2023-01-26" in data

@responses.activate
def test_get_index_list(arrow_client):
    url = f"{arrow_client.root_url}/info/index-list"
    mock_response = {
        "status": "success",
        "data": [{"indexName": "NIFTY 50", "token": 256265}]
    }
    responses.add(responses.GET, url, json=mock_response, status=200)
    
    data = arrow_client.get_index_list()
    assert len(data) == 1
    assert data[0]["indexName"] == "NIFTY 50"

@responses.activate
def test_get_option_chain_symbols(arrow_client):
    url = f"{arrow_client.root_url}/info/option-chain-symbols/all"
    mock_response = {
        "status": "success",
        "data": ["NIFTY", "BANKNIFTY"]
    }
    responses.add(responses.GET, url, json=mock_response, status=200)
    
    data = arrow_client.get_option_chain_symbols()
    assert "NIFTY" in data

@responses.activate
def test_get_option_chain(arrow_client):
    url = f"{arrow_client.root_url}/info/option-chain"
    mock_response = {
        "status": "success",
        "data": [{"strikePrice": 18000, "callToken": 123, "putToken": 124}]
    }
    responses.add(responses.POST, url, json=mock_response, status=200)
    
    data = arrow_client.get_option_chain("NIFTY", Exchange.INDEX, 10, "03-APR-2024")
    assert len(data) == 1
    assert data[0]["strikePrice"] == 18000

@responses.activate
def test_get_stock_option_symbols(arrow_client):
    # This might use local data instead of an API, but we'll test the output
    data = arrow_client.get_stock_option_symbols()
    assert isinstance(data, list)
    from pyarrow_client.arrow_utils import stock_options
    if "RELIANCE" in stock_options:
         pass # Handled locally without network request
