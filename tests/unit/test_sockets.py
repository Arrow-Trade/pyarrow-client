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

def _build_full_packet(depth_offset: int) -> bytes:
    """Build a FULL-mode wire packet (241 or 249 bytes)."""
    buf = bytearray(depth_offset + 10 * 14)
    struct.pack_into(">I", buf, 0, 3045)
    struct.pack_into(">I", buf, 4, 97780)
    struct.pack_into(">I", buf, 13, 10)
    struct.pack_into(">I", buf, 17, 14950)
    struct.pack_into(">Q", buf, 21, 1000)
    struct.pack_into(">Q", buf, 29, 2000)
    struct.pack_into(">I", buf, 37, 14800)
    struct.pack_into(">I", buf, 41, 15200)
    struct.pack_into(">I", buf, 45, 14700)
    struct.pack_into(">I", buf, 49, 14600)
    struct.pack_into(">Q", buf, 53, 50000)
    struct.pack_into(">I", buf, 61, 123456)
    struct.pack_into(">I", buf, 65, 123457)
    struct.pack_into(">Q", buf, 69, 100000)
    struct.pack_into(">Q", buf, 77, 110000)
    struct.pack_into(">Q", buf, 85, 90000)
    struct.pack_into(">I", buf, 93, 87345)
    struct.pack_into(">I", buf, 97, 106745)
    for i in range(10):
        off = depth_offset + i * 14
        struct.pack_into(">Q", buf, off, 100 + i)
        struct.pack_into(">I", buf, off + 8, 97750 + i)
        struct.pack_into(">H", buf, off + 12, 5)
    return bytes(buf)


def test_data_stream_parse_full_241_byte():
    config = ConnectionConfig(appID="test", token="token")
    stream = DataStream(config)
    payload = _build_full_packet(depth_offset=101)
    assert len(payload) == 241
    tick = stream._parse_binary(payload)
    assert tick is not None
    assert tick.mode == DataMode.FULL.value
    assert len(tick.bids) == 5
    assert len(tick.asks) == 5
    assert tick.bids[0]["price"] == 97750
    assert tick.lower_limit == 87345
    assert tick.upper_limit == 106745


def test_data_stream_parse_full_249_byte():
    """Live ds.arrow.trade FULL ticks are 249 bytes (8 reserved bytes before depth)."""
    config = ConnectionConfig(appID="test", token="token")
    stream = DataStream(config)
    payload = _build_full_packet(depth_offset=109)
    assert len(payload) == 249
    tick = stream._parse_binary(payload)
    assert tick is not None
    assert tick.mode == DataMode.FULL.value
    assert len(tick.bids) == 5
    assert tick.bids[0]["price"] == 97750
    assert tick.asks[0]["price"] == 97755


def test_data_stream_parse_ltp_13_byte():
    """LTP mode uses 13-byte binary ticks; must not be rejected (e.g. index tokens)."""
    config = ConnectionConfig(appID="test", token="token")
    stream = DataStream(config)
    token, ltp = 26000, 19_500_00  # example values in wire format (often paise)
    payload = struct.pack(">II", token, ltp) + b"\x00" * 5
    assert len(payload) == 13
    tick = stream._parse_binary(payload)
    assert tick is not None
    assert tick.token == token
    assert tick.ltp == ltp
    assert tick.mode == DataMode.LTP.value


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
    assert "zstd=1" in url
    assert stream._zstd is True
    assert stream._zdec is not None
    assert stream._uses_text_pong() is False
    run_kwargs = stream._run_forever_kwargs(url)
    assert run_kwargs["ping_interval"] == config.ping_interval
    assert run_kwargs["ping_timeout"] < run_kwargs["ping_interval"]


def test_order_stream_uses_text_pong():
    config = ConnectionConfig(appID="test", token="token")
    stream = OrderStream(config)
    assert stream._uses_text_pong() is True

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


def _make_ltp_frame(token=5042, ltp=10000):
    data = bytearray(HFTDataStream.PKT_SIZE_LTP)
    struct.pack_into('<h', data, 0, HFTDataStream.PKT_SIZE_LTP)
    data[2] = HFTDataStream.PKT_TYPE_LTP
    data[3] = HFTDataStream.EXCH_NSE_CM
    struct.pack_into('<i', data, 4, token)
    struct.pack_into('<i', data, 8, ltp)
    return bytes(data)


def test_hft_packet_meta():
    ltp = _make_ltp_frame()
    n, pkt, ok = HFTDataStream._hft_packet_meta(ltp)
    assert ok
    assert n == HFTDataStream.PKT_SIZE_LTP
    assert pkt == HFTDataStream.PKT_TYPE_LTP


def test_hft_dispatch_multiple_packets():
    config = ConnectionConfig(appID="test", token="token")
    stream = HFTDataStream(config)
    ticks = []
    stream.on_ltp_tick = ticks.append
    stream._dispatch_hft_payload(_make_ltp_frame(token=1) + _make_ltp_frame(token=2))
    assert len(ticks) == 2
    assert ticks[0]["token"] == 1
    assert ticks[1]["token"] == 2


def test_hft_zstd_decompress_roundtrip():
    import zstandard as zstd

    config = ConnectionConfig(appID="test", token="token")
    stream = HFTDataStream(config)
    raw = _make_ltp_frame(token=99, ltp=12345)
    compressed = zstd.ZstdCompressor().compress(raw)
    ticks = []
    stream.on_ltp_tick = ticks.append
    stream._on_message(None, compressed)
    assert len(ticks) == 1
    assert ticks[0]["token"] == 99
    assert ticks[0]["ltp"] == 12345
