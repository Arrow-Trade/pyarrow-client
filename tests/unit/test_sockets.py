import pytest
import json
import struct
from pyarrow_client.sockets import ConnectionConfig, DataStream, DataMode, OrderStream, HFTDataStream, ArrowStreams, MarketTick
from pyarrow_client.constants import Exchange

def test_connection_config():
    config = ConnectionConfig(
        appID="test_app_id",
        token="test_token",
        debug=True,
        enable_reconnect=False
    )
    
    assert config.appID == "test_app_id"
    assert config.token == "test_token"
    assert config.debug is True
    assert config.enable_reconnect is False
    assert config.max_reconnect_delay == 5

def test_data_stream_init():
    config = ConnectionConfig(appID="test", token="token")
    stream = DataStream(config)
    
    assert stream.config == config
    url = stream._build_url()
    assert "wss://ds.arrow.trade" in url
    assert "appID=test" in url
    assert "token=token" in url

def test_data_stream_subscribe():
    config = ConnectionConfig(appID="test", token="token")
    stream = DataStream(config)
    
    messages_sent = []
    
    def mock_send(msg):
        messages_sent.append(msg)
        
    stream._send_message = mock_send
    # Mock connected property for test
    stream.connected = lambda: True
    
    stream.subscribe(DataMode.LTPC, [12345, 67890])
    
    assert len(messages_sent) == 1
    msg = messages_sent[0]
    
    assert msg["code"] == "sub"
    assert msg["mode"] == "ltpc"
    assert msg["ltpc"] == [12345, 67890]

def test_order_stream_init():
    config = ConnectionConfig(appID="test", token="token")
    stream = OrderStream(config)
    url = stream._build_url()
    assert "wss://order-updates.arrow.trade" in url

def test_order_stream_on_message():
    config = ConnectionConfig(appID="test", token="token")
    stream = OrderStream(config)
    
    received_orders = []
    def mock_on_order_update(order):
        received_orders.append(order)
        
    stream.on_order_update = mock_on_order_update
    
    mock_order_msg = json.dumps({"id": "12345", "status": "COMPLETED"})
    stream._on_message(None, mock_order_msg)
    
    assert len(received_orders) == 1
    assert received_orders[0]["id"] == "12345"
    assert received_orders[0]["status"] == "COMPLETED"

def test_hft_data_stream_init():
    config = ConnectionConfig(appID="test", token="token")
    stream = HFTDataStream(config)
    url = stream._build_url()
    assert "wss://socket.arrow.trade" in url

def test_hft_data_stream_subscribe():
    config = ConnectionConfig(appID="test", token="token")
    stream = HFTDataStream(config)
    
    messages_sent = []
    def mock_send(msg):
        messages_sent.append(msg)
        
    stream._send_message = mock_send
    stream.connected = lambda: True
    
    stream.subscribe("ltpc", ["NSE:RELIANCE-EQ"], 500)
    
    assert len(messages_sent) == 1
    msg = messages_sent[0]
    assert msg["code"] == "sub"
    assert msg["mode"] == "ltpc"
    assert msg["symbols"] == ["NSE:RELIANCE-EQ"]
    assert msg["latency"] == 500

def test_arrow_streams_manager():
    streams = ArrowStreams("app_id", "token")
    
    status = streams.get_status()
    assert status["order_stream"] == "disconnected"
    assert status["data_stream"] == "disconnected"
    assert status["hft_data_stream"] == "disconnected"
