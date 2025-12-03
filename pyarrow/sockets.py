from typing import Optional, Dict, List, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass, field
import json
import time
import logging
import threading
import struct
import websocket
from urllib.parse import urlencode
import ssl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types"""
    CONNECT = "connect"
    SUBSCRIBE = "sub"
    UNSUBSCRIBE = "unsub"


class DataMode(Enum):
    """Market data streaming modes"""
    LTPC = "ltpc"
    QUOTE = "quote"
    FULL = "full"


class SocketStatus(Enum):
    """Socket connection status"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RETRYING = "retrying"
    DISCONNECTED = "disconnected"


@dataclass
class ConnectionConfig:
    """WebSocket connection configuration"""
    appID: str
    token: str
    debug: bool = False

    # Reconnection settings - matching JS implementation
    enable_reconnect: bool = True
    max_reconnect_attempts: int = 300
    max_reconnect_delay: int = 5  # Reduced from 10 to 5 seconds
    immediate_reconnect_attempts: int = 3  # First 3 attempts are immediate

    # Connection timeouts - matching JS implementation
    read_timeout: int = 5  # Reduced from 30 to 5 seconds
    ping_interval: int = 3  # Reduced from 30 to 3 seconds


@dataclass
class MarketTick:
    """Market tick data structure matching JS implementation"""
    token: int
    ltp: float = 0.0
    mode: str = ""

    # Price data
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0

    # Change calculations
    net_change: float = 0.0
    change_flag: int = 32  # ASCII codes: 43(+), 45(-), 32(no change)

    # Quote data
    ltq: int = 0  # Last traded quantity
    avg_price: float = 0.0
    total_buy_quantity: int = 0
    total_sell_quantity: int = 0

    # Time and OI
    ltt: int = 0  # Last trade time
    time: int = 0
    oi: int = 0  # Open interest
    oi_day_high: int = 0
    oi_day_low: int = 0

    # Limits and depth
    upper_limit: float = 0.0
    lower_limit: float = 0.0
    bids: List[Dict[str, Union[float, int]]] = field(default_factory=list)
    asks: List[Dict[str, Union[float, int]]] = field(default_factory=list)


class BaseSocket:
    """Base WebSocket class with common functionality"""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.ws = None
        self.is_connected = False
        self.current_reconnection_count = 0
        self.last_reconnect_interval = 0
        self.last_read = 0
        self.reconnect_timer = None
        self.ping_timer = None
        self.read_timer = None
        self.is_intentional_disconnect = False

        # Event handlers
        self.on_connect = None
        self.on_disconnect = None
        self.on_reconnect = None
        self.on_no_reconnect = None
        self.on_error = None
        self.on_close = None

    def connect(self):
        """Establish WebSocket connection"""
        if self.ws and self.ws.sock and self.ws.sock.connected:
            return

        url = self._build_url()

        try:
            self.ws = websocket.WebSocketApp(
                url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )

            # Start connection in a thread
            self.ws_thread = threading.Thread(
                target=self.ws.run_forever,
                kwargs={
                    'sslopt': {"cert_reqs": ssl.CERT_NONE} if url.startswith('wss') else {}
                }
            )
            self.ws_thread.daemon = True
            self.ws_thread.start()

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            if self.config.enable_reconnect:
                self._attempt_reconnection()

    def disconnect(self):
        """Disconnect WebSocket"""
        self.is_intentional_disconnect = True
        if self.ws:
            self.ws.close()

    def connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.is_connected and self.ws and self.ws.sock and self.ws.sock.connected

    def _build_url(self):
        """Build WebSocket URL - to be implemented by subclasses"""
        raise NotImplementedError

    def _on_open(self, ws):
        """Handle WebSocket open event"""
        self.is_connected = True
        self.last_reconnect_interval = 0
        self.current_reconnection_count = 0

        # Clear timers
        self._clear_timers()

        # Start heartbeat
        self.last_read = time.time()
        self._start_ping_timer()
        self._start_read_timer()

        if self.on_connect:
            self.on_connect()

        logger.info(f"{self.__class__.__name__} connected")

    def _on_message(self, ws, message):
        """Handle WebSocket message - to be implemented by subclasses"""
        self.last_read = time.time()

    def _on_error(self, ws, error):
        """Handle WebSocket error"""
        logger.error(f"{self.__class__.__name__} error: {error}")
        if self.on_error:
            self.on_error(error)

        # Force close to avoid ghost connections
        if ws and hasattr(ws, 'sock') and ws.sock:
            ws.close()

    def _on_close(self, ws, close_status_code=None, close_msg=None):
        """Handle WebSocket close event"""
        self.is_connected = False
        self._clear_timers()

        if self.on_close:
            self.on_close(close_status_code, close_msg)

        if self.on_disconnect:
            self.on_disconnect()

        logger.info(f"{self.__class__.__name__} disconnected")

        # Only auto-reconnect if it wasn't intentional
        if self.config.enable_reconnect and not self.is_intentional_disconnect:
            self._attempt_reconnection()

        # Reset flag
        self.is_intentional_disconnect = False

    def _start_ping_timer(self):
        """Start ping timer"""

        def send_ping():
            if self.connected():
                try:
                    self.ws.send('PONG')
                    if self.config.debug:
                        logger.debug("Sent PONG")
                except Exception as e:
                    logger.error(f"Failed to send ping: {e}")

            # Schedule next ping
            if self.is_connected:
                self.ping_timer = threading.Timer(self.config.ping_interval, send_ping)
                self.ping_timer.start()

        self.ping_timer = threading.Timer(self.config.ping_interval, send_ping)
        self.ping_timer.start()

    def _start_read_timer(self):
        """Start read timeout timer"""

        def check_read_timeout():
            if time.time() - self.last_read >= self.config.read_timeout:
                logger.warning("Read timeout, closing connection")
                if self.ws:
                    self.ws.close()
                self._clear_timers()
            else:
                # Schedule next check
                if self.is_connected:
                    self.read_timer = threading.Timer(self.config.read_timeout, check_read_timeout)
                    self.read_timer.start()

        self.read_timer = threading.Timer(self.config.read_timeout, check_read_timeout)
        self.read_timer.start()

    def _clear_timers(self):
        """Clear all timers"""
        if self.reconnect_timer:
            self.reconnect_timer.cancel()
        if self.ping_timer:
            self.ping_timer.cancel()
        if self.read_timer:
            self.read_timer.cancel()

    def _attempt_reconnection(self):
        """Attempt to reconnect with exponential backoff (matching JS implementation)"""
        if self.current_reconnection_count > self.config.max_reconnect_attempts:
            logger.error("Exhausted reconnect retries")
            if self.on_no_reconnect:
                self.on_no_reconnect()
            return

        reconnect_delay = 0

        # First few attempts: immediate reconnection (0 delay)
        if self.current_reconnection_count < self.config.immediate_reconnect_attempts:
            reconnect_delay = 0
        # After immediate attempts: use exponential backoff
        else:
            backoff_attempt = self.current_reconnection_count - self.config.immediate_reconnect_attempts
            reconnect_delay = min(2 ** backoff_attempt, self.config.max_reconnect_delay)

        self.current_reconnection_count += 1

        if self.on_reconnect:
            self.on_reconnect(self.current_reconnection_count, reconnect_delay)

        if self.reconnect_timer:
            self.reconnect_timer.cancel()

        if reconnect_delay == 0:
            logger.info(f"reconnecting immediately (attempt {self.current_reconnection_count})...")
            self.connect()
        else:
            logger.info(f"reconnect attempt {self.current_reconnection_count} after {reconnect_delay} seconds")
            self.reconnect_timer = threading.Timer(reconnect_delay, self.connect)
            self.reconnect_timer.start()


class OrderStream(BaseSocket):
    """WebSocket stream for order updates"""

    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.on_order_update = None

    def _build_url(self) -> str:
        """Build order updates WebSocket URL"""
        return f"wss://order-updates.arrow.trade?appID={self.config.appID}&token={self.config.token}"

    def _on_message(self, ws, message):
        """Handle order update message"""
        super()._on_message(ws, message)

        try:
            # Parse text message only (no binary handling for orders)
            if isinstance(message, str):
                data = json.loads(message)
                if data.get('id') and self.on_order_update:
                    self.on_order_update(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse order message: {e}")


class DataStream(BaseSocket):
    """WebSocket stream for market data with subscription management"""

    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.subscriptions = {
            DataMode.LTPC.value: {},
            DataMode.QUOTE.value: {},
            DataMode.FULL.value: {}
        }
        self.on_ticks = None

    def _build_url(self) -> str:
        """Build market data WebSocket URL"""
        return f"wss://ds.arrow.trade?appID={self.config.appID}&token={self.config.token}"

    def _on_open(self, ws):
        """Handle connection open and resubscribe"""
        super()._on_open(ws)

        # Resubscribe to all existing subscriptions
        for mode in [DataMode.LTPC, DataMode.QUOTE, DataMode.FULL]:
            tokens = list(self.subscriptions[mode.value].keys())
            if tokens:
                self.subscribe(mode, tokens)

    def _on_message(self, ws, message):
        """Handle market data message"""
        super()._on_message(ws, message)

        try:
            # Handle binary data only (market ticks)
            if isinstance(message, bytes) and len(message) > 2:
                tick = self._parse_binary(message)
                if tick and self.on_ticks:
                    self.on_ticks(tick)
        except Exception as e:
            logger.error(f"Failed to parse market data: {e}")

    def subscribe(self, mode: DataMode, tokens: List[int]):
        """Subscribe to market data"""
        # Update local subscriptions
        for token in tokens:
            self.subscriptions[mode.value][token] = 1

        if not self.connected():
            return

        if tokens:
            message = {
                "code": MessageType.SUBSCRIBE.value,
                "mode": mode.value,
                mode.value: tokens
            }
            self._send_message(message)

        logger.info(f"Subscribed to {len(tokens)} tokens in {mode.value} mode")

    def unsubscribe(self, mode: DataMode, tokens: List[int]):
        """Unsubscribe from market data"""
        # Update local subscriptions
        for token in tokens:
            self.subscriptions[mode.value].pop(token, None)

        if not self.connected():
            return

        if tokens:
            message = {
                "code": MessageType.UNSUBSCRIBE.value,
                "mode": mode.value,
                mode.value: tokens
            }
            self._send_message(message)

        logger.info(f"Unsubscribed from {len(tokens)} tokens in {mode.value} mode")

    def _send_message(self, message: Dict):
        """Send JSON message to WebSocket"""
        try:
            json_message = json.dumps(message)
            if self.config.debug:
                logger.debug(f"Sending: {json_message}")
            self.ws.send(json_message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def _parse_binary(self, data: bytes) -> Optional[MarketTick]:
        """Parse binary market data (matching JS implementation exactly)"""
        if len(data) < 17:
            return None

        try:
            # Parse basic data
            tick = MarketTick(
                token=self._big_endian_to_int(data[0:4]),
                ltp=self._big_endian_to_int(data[4:8])
            )

            # LTPC mode (17 bytes)
            if len(data) >= 17:
                tick.close = self._big_endian_to_int(data[13:17])

                # Calculate net change
                if tick.close != 0:
                    tick.net_change = round(((tick.ltp - tick.close) / tick.close) * 100, 2)
                else:
                    tick.net_change = 0.0

                # Set change flag
                if tick.ltp > tick.close:
                    tick.change_flag = 43  # ASCII '+'
                elif tick.ltp < tick.close:
                    tick.change_flag = 45  # ASCII '-'
                else:
                    tick.change_flag = 32  # No change

                tick.mode = DataMode.LTPC.value

            # Quote mode (93 bytes)
            if len(data) >= 93:
                tick.ltq = self._big_endian_to_int(data[13:17])
                tick.avg_price = self._big_endian_to_int(data[17:21])
                tick.total_buy_quantity = self._big_endian_to_int(data[21:29])
                tick.total_sell_quantity = self._big_endian_to_int(data[29:37])
                tick.open = self._big_endian_to_int(data[37:41])
                tick.high = self._big_endian_to_int(data[41:45])
                tick.close = self._big_endian_to_int(data[45:49])
                tick.low = self._big_endian_to_int(data[49:53])
                tick.volume = self._big_endian_to_int(data[53:61])
                tick.ltt = self._big_endian_to_int(data[61:65])
                tick.time = self._big_endian_to_int(data[65:69])
                tick.oi = self._big_endian_to_int(data[69:77])
                tick.oi_day_high = self._big_endian_to_int(data[77:85])
                tick.oi_day_low = self._big_endian_to_int(data[85:93])

                # Recalculate net change with close from quote data
                if tick.close != 0:
                    tick.net_change = round(((tick.ltp - tick.close) / tick.close) * 100, 2)
                else:
                    tick.net_change = 0.0

                # Recalculate change flag
                if tick.ltp > tick.close:
                    tick.change_flag = 43
                elif tick.ltp < tick.close:
                    tick.change_flag = 45
                else:
                    tick.change_flag = 32

                tick.mode = DataMode.QUOTE.value

            # Full mode (241 bytes)
            if len(data) == 241:
                tick.lower_limit = self._big_endian_to_int(data[93:97])
                tick.upper_limit = self._big_endian_to_int(data[97:101])

                # Parse bids and asks (10 levels total: 5 bids, 5 asks)
                bids = []
                asks = []

                for i in range(10):
                    offset = 101 + i * 14
                    quantity = self._big_endian_to_int(data[offset:offset + 8])
                    price = self._big_endian_to_int(data[offset + 8:offset + 12])
                    orders = self._big_endian_to_int(data[offset + 12:offset + 14])

                    level_data = {
                        'price': price,
                        'quantity': quantity,
                        'orders': orders
                    }

                    if i >= 5:
                        asks.append(level_data)
                    else:
                        bids.append(level_data)

                tick.bids = bids
                tick.asks = asks
                tick.mode = DataMode.FULL.value

            # Reset net change if close is 0
            if tick.close == 0:
                tick.net_change = 0.0

            return tick

        except Exception as e:
            logger.error(f"Error parsing binary data: {e}")
            return None

    def _big_endian_to_int(self, buffer: bytes) -> int:
        """Convert big-endian bytes to integer (matching JS implementation exactly)"""
        value = 0
        length = len(buffer)

        for i in range(length):
            j = length - 1 - i
            value += buffer[j] << (i * 8)

        return value


class ArrowStreams:
    """Main client class providing both order and data streams"""

    def __init__(self, appID: str, token: str, debug: bool = False):
        self.config = ConnectionConfig(appID=appID, token=token, debug=debug)

        # Initialize streams
        self.order_stream = OrderStream(self.config)
        self.data_stream = DataStream(self.config)

        # Status tracking
        self.status = {
            'order_stream': SocketStatus.DISCONNECTED,
            'data_stream': SocketStatus.DISCONNECTED
        }

        # Set up event handlers for status tracking
        self._setup_status_handlers()

    def connect_order_stream(self):
        """Connect to order updates stream"""
        self.order_stream.connect()

    def connect_data_stream(self):
        """Connect to market data stream"""
        self.data_stream.connect()

    def connect_all(self):
        """Connect to both streams"""
        self.connect_order_stream()
        self.connect_data_stream()

    def disconnect_all(self):
        """Disconnect from both streams"""
        self.order_stream.disconnect()
        self.data_stream.disconnect()

    def subscribe_market_data(self, mode: DataMode, tokens: List[int]):
        """Subscribe to market data"""
        self.data_stream.subscribe(mode, tokens)

    def unsubscribe_market_data(self, mode: DataMode, tokens: List[int]):
        """Unsubscribe from market data"""
        self.data_stream.unsubscribe(mode, tokens)

    def get_status(self) -> Dict[str, str]:
        """Get connection status for both streams"""
        return {
            'order_stream': self.status['order_stream'].value,
            'data_stream': self.status['data_stream'].value
        }

    def _setup_status_handlers(self):
        """Set up status tracking handlers"""
        # Order stream handlers
        self.order_stream.on_connect = lambda: self._update_status('order_stream', SocketStatus.CONNECTED)
        self.order_stream.on_disconnect = lambda: self._update_status('order_stream', SocketStatus.CONNECTING)
        self.order_stream.on_reconnect = lambda *args: self._update_status('order_stream', SocketStatus.CONNECTING)

        # Data stream handlers
        self.data_stream.on_connect = lambda: self._update_status('data_stream', SocketStatus.CONNECTED)
        self.data_stream.on_disconnect = lambda: self._update_status('data_stream', SocketStatus.CONNECTING)
        self.data_stream.on_reconnect = lambda *args: self._update_status('data_stream', SocketStatus.CONNECTING)

    def _update_status(self, stream: str, status: SocketStatus):
        """Update stream status"""
        self.status[stream] = status
        if self.config.debug:
            logger.debug(f"{stream} status: {status.value}")