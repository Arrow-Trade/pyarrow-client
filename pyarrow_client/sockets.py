# # from typing import Optional, Dict, List, Callable, Any, Union
# # from enum import Enum
# # from dataclasses import dataclass, field
# # import json
# # import time
# # import logging
# # import threading
# # import struct
# # import websocket
# # from urllib.parse import urlencode
# # import ssl
# #
# # # Configure logging
# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger(__name__)
# #
# #
# # class MessageType(Enum):
# #     """WebSocket message types"""
# #     CONNECT = "connect"
# #     SUBSCRIBE = "sub"
# #     UNSUBSCRIBE = "unsub"
# #
# #
# # class DataMode(Enum):
# #     """Market data streaming modes"""
# #     LTPC = "ltpc"
# #     QUOTE = "quote"
# #     FULL = "full"
# #
# #
# # class SocketStatus(Enum):
# #     """Socket connection status"""
# #     CONNECTING = "connecting"
# #     CONNECTED = "connected"
# #     RETRYING = "retrying"
# #     DISCONNECTED = "disconnected"
# #
# #
# # @dataclass
# # class ConnectionConfig:
# #     """WebSocket connection configuration"""
# #     appID: str
# #     token: str
# #     debug: bool = False
# #
# #     # Reconnection settings - matching JS implementation
# #     enable_reconnect: bool = True
# #     max_reconnect_attempts: int = 300
# #     max_reconnect_delay: int = 5  # Reduced from 10 to 5 seconds
# #     immediate_reconnect_attempts: int = 3  # First 3 attempts are immediate
# #
# #     # Connection timeouts - matching JS implementation
# #     read_timeout: int = 5  # Reduced from 30 to 5 seconds
# #     ping_interval: int = 3  # Reduced from 30 to 3 seconds
# #
# #
# # @dataclass
# # class MarketTick:
# #     """Market tick data structure matching JS implementation"""
# #     token: int
# #     ltp: float = 0.0
# #     mode: str = ""
# #
# #     # Price data
# #     open: float = 0.0
# #     high: float = 0.0
# #     low: float = 0.0
# #     close: float = 0.0
# #     volume: int = 0
# #
# #     # Change calculations
# #     net_change: float = 0.0
# #     change_flag: int = 32  # ASCII codes: 43(+), 45(-), 32(no change)
# #
# #     # Quote data
# #     ltq: int = 0  # Last traded quantity
# #     avg_price: float = 0.0
# #     total_buy_quantity: int = 0
# #     total_sell_quantity: int = 0
# #
# #     # Time and OI
# #     ltt: int = 0  # Last trade time
# #     time: int = 0
# #     oi: int = 0  # Open interest
# #     oi_day_high: int = 0
# #     oi_day_low: int = 0
# #
# #     # Limits and depth
# #     upper_limit: float = 0.0
# #     lower_limit: float = 0.0
# #     bids: List[Dict[str, Union[float, int]]] = field(default_factory=list)
# #     asks: List[Dict[str, Union[float, int]]] = field(default_factory=list)
# #
# #
# # class BaseSocket:
# #     """Base WebSocket class with common functionality"""
# #
# #     def __init__(self, config: ConnectionConfig):
# #         self.config = config
# #         self.ws = None
# #         self.is_connected = False
# #         self.current_reconnection_count = 0
# #         self.last_reconnect_interval = 0
# #         self.last_read = 0
# #         self.reconnect_timer = None
# #         self.ping_timer = None
# #         self.read_timer = None
# #         self.is_intentional_disconnect = False
# #
# #         # Event handlers
# #         self.on_connect = None
# #         self.on_disconnect = None
# #         self.on_reconnect = None
# #         self.on_no_reconnect = None
# #         self.on_error = None
# #         self.on_close = None
# #
# #     def connect(self):
# #         """Establish WebSocket connection"""
# #         if self.ws and self.ws.sock and self.ws.sock.connected:
# #             return
# #
# #         url = self._build_url()
# #
# #         try:
# #             self.ws = websocket.WebSocketApp(
# #                 url,
# #                 on_open=self._on_open,
# #                 on_message=self._on_message,
# #                 on_error=self._on_error,
# #                 on_close=self._on_close
# #             )
# #
# #             # Start connection in a thread
# #             self.ws_thread = threading.Thread(
# #                 target=self.ws.run_forever,
# #                 kwargs={
# #                     'sslopt': {"cert_reqs": ssl.CERT_NONE} if url.startswith('wss') else {}
# #                 }
# #             )
# #             self.ws_thread.daemon = True
# #             self.ws_thread.start()
# #
# #         except Exception as e:
# #             logger.error(f"Connection failed: {e}")
# #             if self.config.enable_reconnect:
# #                 self._attempt_reconnection()
# #
# #     def disconnect(self):
# #         """Disconnect WebSocket"""
# #         self.is_intentional_disconnect = True
# #         if self.ws:
# #             self.ws.close()
# #
# #     def connected(self) -> bool:
# #         """Check if WebSocket is connected"""
# #         return self.is_connected and self.ws and self.ws.sock and self.ws.sock.connected
# #
# #     def _build_url(self):
# #         """Build WebSocket URL - to be implemented by subclasses"""
# #         raise NotImplementedError
# #
# #     def _on_open(self, ws):
# #         """Handle WebSocket open event"""
# #         self.is_connected = True
# #         self.last_reconnect_interval = 0
# #         self.current_reconnection_count = 0
# #
# #         # Clear timers
# #         self._clear_timers()
# #
# #         # Start heartbeat
# #         self.last_read = time.time()
# #         self._start_ping_timer()
# #         self._start_read_timer()
# #
# #         if self.on_connect:
# #             self.on_connect()
# #
# #         logger.info(f"{self.__class__.__name__} connected")
# #
# #     def _on_message(self, ws, message):
# #         """Handle WebSocket message - to be implemented by subclasses"""
# #         self.last_read = time.time()
# #
# #     def _on_error(self, ws, error):
# #         """Handle WebSocket error"""
# #         logger.error(f"{self.__class__.__name__} error: {error}")
# #         if self.on_error:
# #             self.on_error(error)
# #
# #         # Force close to avoid ghost connections
# #         if ws and hasattr(ws, 'sock') and ws.sock:
# #             ws.close()
# #
# #     def _on_close(self, ws, close_status_code=None, close_msg=None):
# #         """Handle WebSocket close event"""
# #         self.is_connected = False
# #         self._clear_timers()
# #
# #         if self.on_close:
# #             self.on_close(close_status_code, close_msg)
# #
# #         if self.on_disconnect:
# #             self.on_disconnect()
# #
# #         logger.info(f"{self.__class__.__name__} disconnected")
# #
# #         # Only auto-reconnect if it wasn't intentional
# #         if self.config.enable_reconnect and not self.is_intentional_disconnect:
# #             self._attempt_reconnection()
# #
# #         # Reset flag
# #         self.is_intentional_disconnect = False
# #
# #     def _start_ping_timer(self):
# #         """Start ping timer"""
# #
# #         def send_ping():
# #             if self.connected():
# #                 try:
# #                     self.ws.send('PONG')
# #                     if self.config.debug:
# #                         logger.debug("Sent PONG")
# #                 except Exception as e:
# #                     logger.error(f"Failed to send ping: {e}")
# #
# #             # Schedule next ping
# #             if self.is_connected:
# #                 self.ping_timer = threading.Timer(self.config.ping_interval, send_ping)
# #                 self.ping_timer.start()
# #
# #         self.ping_timer = threading.Timer(self.config.ping_interval, send_ping)
# #         self.ping_timer.start()
# #
# #     def _start_read_timer(self):
# #         """Start read timeout timer"""
# #
# #         def check_read_timeout():
# #             if time.time() - self.last_read >= self.config.read_timeout:
# #                 logger.warning("Read timeout, closing connection")
# #                 if self.ws:
# #                     self.ws.close()
# #                 self._clear_timers()
# #             else:
# #                 # Schedule next check
# #                 if self.is_connected:
# #                     self.read_timer = threading.Timer(self.config.read_timeout, check_read_timeout)
# #                     self.read_timer.start()
# #
# #         self.read_timer = threading.Timer(self.config.read_timeout, check_read_timeout)
# #         self.read_timer.start()
# #
# #     def _clear_timers(self):
# #         """Clear all timers"""
# #         if self.reconnect_timer:
# #             self.reconnect_timer.cancel()
# #         if self.ping_timer:
# #             self.ping_timer.cancel()
# #         if self.read_timer:
# #             self.read_timer.cancel()
# #
# #     def _attempt_reconnection(self):
# #         """Attempt to reconnect with exponential backoff (matching JS implementation)"""
# #         if self.current_reconnection_count > self.config.max_reconnect_attempts:
# #             logger.error("Exhausted reconnect retries")
# #             if self.on_no_reconnect:
# #                 self.on_no_reconnect()
# #             return
# #
# #         reconnect_delay = 0
# #
# #         # First few attempts: immediate reconnection (0 delay)
# #         if self.current_reconnection_count < self.config.immediate_reconnect_attempts:
# #             reconnect_delay = 0
# #         # After immediate attempts: use exponential backoff
# #         else:
# #             backoff_attempt = self.current_reconnection_count - self.config.immediate_reconnect_attempts
# #             reconnect_delay = min(2 ** backoff_attempt, self.config.max_reconnect_delay)
# #
# #         self.current_reconnection_count += 1
# #
# #         if self.on_reconnect:
# #             self.on_reconnect(self.current_reconnection_count, reconnect_delay)
# #
# #         if self.reconnect_timer:
# #             self.reconnect_timer.cancel()
# #
# #         if reconnect_delay == 0:
# #             logger.info(f"reconnecting immediately (attempt {self.current_reconnection_count})...")
# #             self.connect()
# #         else:
# #             logger.info(f"reconnect attempt {self.current_reconnection_count} after {reconnect_delay} seconds")
# #             self.reconnect_timer = threading.Timer(reconnect_delay, self.connect)
# #             self.reconnect_timer.start()
# #
# #
# # class OrderStream(BaseSocket):
# #     """WebSocket stream for order updates"""
# #
# #     def __init__(self, config: ConnectionConfig):
# #         super().__init__(config)
# #         self.on_order_update = None
# #
# #     def _build_url(self) -> str:
# #         """Build order updates WebSocket URL"""
# #         return f"wss://order-updates.arrow.trade?appID={self.config.appID}&token={self.config.token}"
# #
# #     def _on_message(self, ws, message):
# #         """Handle order update message"""
# #         super()._on_message(ws, message)
# #
# #         try:
# #             # Parse text message only (no binary handling for orders)
# #             if isinstance(message, str):
# #                 data = json.loads(message)
# #                 if data.get('id') and self.on_order_update:
# #                     self.on_order_update(data)
# #         except json.JSONDecodeError as e:
# #             logger.error(f"Failed to parse order message: {e}")
# #
# #
# # class DataStream(BaseSocket):
# #     """WebSocket stream for market data with subscription management"""
# #
# #     def __init__(self, config: ConnectionConfig):
# #         super().__init__(config)
# #         self.subscriptions = {
# #             DataMode.LTPC.value: {},
# #             DataMode.QUOTE.value: {},
# #             DataMode.FULL.value: {}
# #         }
# #         self.on_ticks = None
# #
# #     def _build_url(self) -> str:
# #         """Build market data WebSocket URL"""
# #         return f"wss://ds.arrow.trade?appID={self.config.appID}&token={self.config.token}"
# #
# #     def _on_open(self, ws):
# #         """Handle connection open and resubscribe"""
# #         super()._on_open(ws)
# #
# #         # Resubscribe to all existing subscriptions
# #         for mode in [DataMode.LTPC, DataMode.QUOTE, DataMode.FULL]:
# #             tokens = list(self.subscriptions[mode.value].keys())
# #             if tokens:
# #                 self.subscribe(mode, tokens)
# #
# #     def _on_message(self, ws, message):
# #         """Handle market data message"""
# #         super()._on_message(ws, message)
# #
# #         try:
# #             # Handle binary data only (market ticks)
# #             if isinstance(message, bytes) and len(message) > 2:
# #                 tick = self._parse_binary(message)
# #                 if tick and self.on_ticks:
# #                     self.on_ticks(tick)
# #         except Exception as e:
# #             logger.error(f"Failed to parse market data: {e}")
# #
# #     def subscribe(self, mode: DataMode, tokens: List[int]):
# #         """Subscribe to market data"""
# #         # Update local subscriptions
# #         for token in tokens:
# #             self.subscriptions[mode.value][token] = 1
# #
# #         if not self.connected():
# #             return
# #
# #         if tokens:
# #             message = {
# #                 "code": MessageType.SUBSCRIBE.value,
# #                 "mode": mode.value,
# #                 mode.value: tokens
# #             }
# #             self._send_message(message)
# #
# #         logger.info(f"Subscribed to {len(tokens)} tokens in {mode.value} mode")
# #
# #     def unsubscribe(self, mode: DataMode, tokens: List[int]):
# #         """Unsubscribe from market data"""
# #         # Update local subscriptions
# #         for token in tokens:
# #             self.subscriptions[mode.value].pop(token, None)
# #
# #         if not self.connected():
# #             return
# #
# #         if tokens:
# #             message = {
# #                 "code": MessageType.UNSUBSCRIBE.value,
# #                 "mode": mode.value,
# #                 mode.value: tokens
# #             }
# #             self._send_message(message)
# #
# #         logger.info(f"Unsubscribed from {len(tokens)} tokens in {mode.value} mode")
# #
# #     def _send_message(self, message: Dict):
# #         """Send JSON message to WebSocket"""
# #         try:
# #             json_message = json.dumps(message)
# #             if self.config.debug:
# #                 logger.debug(f"Sending: {json_message}")
# #             self.ws.send(json_message)
# #         except Exception as e:
# #             logger.error(f"Failed to send message: {e}")
# #
# #     def _parse_binary(self, data: bytes) -> Optional[MarketTick]:
# #         """Parse binary market data (matching JS implementation exactly)"""
# #         if len(data) < 17:
# #             return None
# #
# #         try:
# #             # Parse basic data
# #             tick = MarketTick(
# #                 token=self._big_endian_to_int(data[0:4]),
# #                 ltp=self._big_endian_to_int(data[4:8])
# #             )
# #
# #             # LTPC mode (17 bytes)
# #             if len(data) >= 17:
# #                 tick.close = self._big_endian_to_int(data[13:17])
# #
# #                 # Calculate net change
# #                 if tick.close != 0:
# #                     tick.net_change = round(((tick.ltp - tick.close) / tick.close) * 100, 2)
# #                 else:
# #                     tick.net_change = 0.0
# #
# #                 # Set change flag
# #                 if tick.ltp > tick.close:
# #                     tick.change_flag = 43  # ASCII '+'
# #                 elif tick.ltp < tick.close:
# #                     tick.change_flag = 45  # ASCII '-'
# #                 else:
# #                     tick.change_flag = 32  # No change
# #
# #                 tick.mode = DataMode.LTPC.value
# #
# #             # Quote mode (93 bytes)
# #             if len(data) >= 93:
# #                 tick.ltq = self._big_endian_to_int(data[13:17])
# #                 tick.avg_price = self._big_endian_to_int(data[17:21])
# #                 tick.total_buy_quantity = self._big_endian_to_int(data[21:29])
# #                 tick.total_sell_quantity = self._big_endian_to_int(data[29:37])
# #                 tick.open = self._big_endian_to_int(data[37:41])
# #                 tick.high = self._big_endian_to_int(data[41:45])
# #                 tick.close = self._big_endian_to_int(data[45:49])
# #                 tick.low = self._big_endian_to_int(data[49:53])
# #                 tick.volume = self._big_endian_to_int(data[53:61])
# #                 tick.ltt = self._big_endian_to_int(data[61:65])
# #                 tick.time = self._big_endian_to_int(data[65:69])
# #                 tick.oi = self._big_endian_to_int(data[69:77])
# #                 tick.oi_day_high = self._big_endian_to_int(data[77:85])
# #                 tick.oi_day_low = self._big_endian_to_int(data[85:93])
# #
# #                 # Recalculate net change with close from quote data
# #                 if tick.close != 0:
# #                     tick.net_change = round(((tick.ltp - tick.close) / tick.close) * 100, 2)
# #                 else:
# #                     tick.net_change = 0.0
# #
# #                 # Recalculate change flag
# #                 if tick.ltp > tick.close:
# #                     tick.change_flag = 43
# #                 elif tick.ltp < tick.close:
# #                     tick.change_flag = 45
# #                 else:
# #                     tick.change_flag = 32
# #
# #                 tick.mode = DataMode.QUOTE.value
# #
# #             # Full mode (241 bytes)
# #             if len(data) == 241:
# #                 tick.lower_limit = self._big_endian_to_int(data[93:97])
# #                 tick.upper_limit = self._big_endian_to_int(data[97:101])
# #
# #                 # Parse bids and asks (10 levels total: 5 bids, 5 asks)
# #                 bids = []
# #                 asks = []
# #
# #                 for i in range(10):
# #                     offset = 101 + i * 14
# #                     quantity = self._big_endian_to_int(data[offset:offset + 8])
# #                     price = self._big_endian_to_int(data[offset + 8:offset + 12])
# #                     orders = self._big_endian_to_int(data[offset + 12:offset + 14])
# #
# #                     level_data = {
# #                         'price': price,
# #                         'quantity': quantity,
# #                         'orders': orders
# #                     }
# #
# #                     if i >= 5:
# #                         asks.append(level_data)
# #                     else:
# #                         bids.append(level_data)
# #
# #                 tick.bids = bids
# #                 tick.asks = asks
# #                 tick.mode = DataMode.FULL.value
# #
# #             # Reset net change if close is 0
# #             if tick.close == 0:
# #                 tick.net_change = 0.0
# #
# #             return tick
# #
# #         except Exception as e:
# #             logger.error(f"Error parsing binary data: {e}")
# #             return None
# #
# #     def _big_endian_to_int(self, buffer: bytes) -> int:
# #         """Convert big-endian bytes to integer (matching JS implementation exactly)"""
# #         value = 0
# #         length = len(buffer)
# #
# #         for i in range(length):
# #             j = length - 1 - i
# #             value += buffer[j] << (i * 8)
# #
# #         return value
# #
# #
# # class ArrowStreams:
# #     """Main client class providing both order and data streams"""
# #
# #     def __init__(self, appID: str, token: str, debug: bool = False):
# #         self.config = ConnectionConfig(appID=appID, token=token, debug=debug)
# #
# #         # Initialize streams
# #         self.order_stream = OrderStream(self.config)
# #         self.data_stream = DataStream(self.config)
# #
# #         # Status tracking
# #         self.status = {
# #             'order_stream': SocketStatus.DISCONNECTED,
# #             'data_stream': SocketStatus.DISCONNECTED
# #         }
# #
# #         # Set up event handlers for status tracking
# #         self._setup_status_handlers()
# #
# #     def connect_order_stream(self):
# #         """Connect to order updates stream"""
# #         self.order_stream.connect()
# #
# #     def connect_data_stream(self):
# #         """Connect to market data stream"""
# #         self.data_stream.connect()
# #
# #     def connect_all(self):
# #         """Connect to both streams"""
# #         self.connect_order_stream()
# #         self.connect_data_stream()
# #
# #     def disconnect_all(self):
# #         """Disconnect from both streams"""
# #         self.order_stream.disconnect()
# #         self.data_stream.disconnect()
# #
# #     def subscribe_market_data(self, mode: DataMode, tokens: List[int]):
# #         """Subscribe to market data"""
# #         self.data_stream.subscribe(mode, tokens)
# #
# #     def unsubscribe_market_data(self, mode: DataMode, tokens: List[int]):
# #         """Unsubscribe from market data"""
# #         self.data_stream.unsubscribe(mode, tokens)
# #
# #     def get_status(self) -> Dict[str, str]:
# #         """Get connection status for both streams"""
# #         return {
# #             'order_stream': self.status['order_stream'].value,
# #             'data_stream': self.status['data_stream'].value
# #         }
# #
# #     def _setup_status_handlers(self):
# #         """Set up status tracking handlers"""
# #         # Order stream handlers
# #         self.order_stream.on_connect = lambda: self._update_status('order_stream', SocketStatus.CONNECTED)
# #         self.order_stream.on_disconnect = lambda: self._update_status('order_stream', SocketStatus.CONNECTING)
# #         self.order_stream.on_reconnect = lambda *args: self._update_status('order_stream', SocketStatus.CONNECTING)
# #
# #         # Data stream handlers
# #         self.data_stream.on_connect = lambda: self._update_status('data_stream', SocketStatus.CONNECTED)
# #         self.data_stream.on_disconnect = lambda: self._update_status('data_stream', SocketStatus.CONNECTING)
# #         self.data_stream.on_reconnect = lambda *args: self._update_status('data_stream', SocketStatus.CONNECTING)
# #
# #     def _update_status(self, stream: str, status: SocketStatus):
# #         """Update stream status"""
# #         self.status[stream] = status
# #         if self.config.debug:
# #             logger.debug(f"{stream} status: {status.value}")
#
#
# from typing import Optional, Dict, List, Callable, Any, Union
# from enum import Enum
# from dataclasses import dataclass, field
# import json
# import time
# import logging
# import threading
# import struct
# import websocket
# from urllib.parse import urlencode
# import ssl
#
# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
#
# class MessageType(Enum):
#     """WebSocket message types"""
#     CONNECT = "connect"
#     SUBSCRIBE = "sub"
#     UNSUBSCRIBE = "unsub"
#
#
# class DataMode(Enum):
#     """Market data streaming modes"""
#     LTPC = "ltpc"
#     QUOTE = "quote"
#     FULL = "full"
#
#
# class SocketStatus(Enum):
#     """Socket connection status"""
#     CONNECTING = "connecting"
#     CONNECTED = "connected"
#     RETRYING = "retrying"
#     DISCONNECTED = "disconnected"
#
#
# @dataclass
# class ConnectionConfig:
#     """WebSocket connection configuration"""
#     appID: str
#     token: str
#     debug: bool = False
#
#     # Reconnection settings - matching JS implementation
#     enable_reconnect: bool = True
#     max_reconnect_attempts: int = 300
#     max_reconnect_delay: int = 5  # Reduced from 10 to 5 seconds
#     immediate_reconnect_attempts: int = 3  # First 3 attempts are immediate
#
#     # Connection timeouts - matching JS implementation
#     read_timeout: int = 5  # Reduced from 30 to 5 seconds
#     ping_interval: int = 3  # Reduced from 30 to 3 seconds
#
#
# @dataclass
# class MarketTick:
#     """Market tick data structure matching JS implementation"""
#     token: int
#     ltp: float = 0.0
#     mode: str = ""
#
#     # Price data
#     open: float = 0.0
#     high: float = 0.0
#     low: float = 0.0
#     close: float = 0.0
#     volume: int = 0
#
#     # Change calculations
#     net_change: float = 0.0
#     change_flag: int = 32  # ASCII codes: 43(+), 45(-), 32(no change)
#
#     # Quote data
#     ltq: int = 0  # Last traded quantity
#     avg_price: float = 0.0
#     total_buy_quantity: int = 0
#     total_sell_quantity: int = 0
#
#     # Time and OI
#     ltt: int = 0  # Last trade time
#     time: int = 0
#     oi: int = 0  # Open interest
#     oi_day_high: int = 0
#     oi_day_low: int = 0
#
#     # Limits and depth
#     upper_limit: float = 0.0
#     lower_limit: float = 0.0
#     bids: List[Dict[str, Union[float, int]]] = field(default_factory=list)
#     asks: List[Dict[str, Union[float, int]]] = field(default_factory=list)
#
#
# class BaseSocket:
#     """Base WebSocket class with common functionality"""
#
#     def __init__(self, config: ConnectionConfig):
#         self.config = config
#         self.ws = None
#         self.is_connected = False
#         self.current_reconnection_count = 0
#         self.last_reconnect_interval = 0
#         self.last_read = 0
#         self.reconnect_timer = None
#         self.ping_timer = None
#         self.read_timer = None
#         self.is_intentional_disconnect = False
#
#         # Event handlers
#         self.on_connect = None
#         self.on_disconnect = None
#         self.on_reconnect = None
#         self.on_no_reconnect = None
#         self.on_error = None
#         self.on_close = None
#
#     def connect(self):
#         """Establish WebSocket connection"""
#         if self.ws and self.ws.sock and self.ws.sock.connected:
#             return
#
#         url = self._build_url()
#
#         try:
#             self.ws = websocket.WebSocketApp(
#                 url,
#                 on_open=self._on_open,
#                 on_message=self._on_message,
#                 on_error=self._on_error,
#                 on_close=self._on_close
#             )
#
#             # Start connection in a thread
#             self.ws_thread = threading.Thread(
#                 target=self.ws.run_forever,
#                 kwargs={
#                     'sslopt': {"cert_reqs": ssl.CERT_NONE} if url.startswith('wss') else {}
#                 }
#             )
#             self.ws_thread.daemon = True
#             self.ws_thread.start()
#
#         except Exception as e:
#             logger.error(f"Connection failed: {e}")
#             if self.config.enable_reconnect:
#                 self._attempt_reconnection()
#
#     def disconnect(self):
#         """Disconnect WebSocket"""
#         self.is_intentional_disconnect = True
#         if self.ws:
#             self.ws.close()
#
#     def connected(self) -> bool:
#         """Check if WebSocket is connected"""
#         return self.is_connected and self.ws and self.ws.sock and self.ws.sock.connected
#
#     def _build_url(self):
#         """Build WebSocket URL - to be implemented by subclasses"""
#         raise NotImplementedError
#
#     def _on_open(self, ws):
#         """Handle WebSocket open event"""
#         self.is_connected = True
#         self.last_reconnect_interval = 0
#         self.current_reconnection_count = 0
#
#         # Clear timers
#         self._clear_timers()
#
#         # Start heartbeat
#         self.last_read = time.time()
#         self._start_ping_timer()
#         self._start_read_timer()
#
#         if self.on_connect:
#             self.on_connect()
#
#         logger.info(f"{self.__class__.__name__} connected")
#
#     def _on_message(self, ws, message):
#         """Handle WebSocket message - to be implemented by subclasses"""
#         self.last_read = time.time()
#
#     def _on_error(self, ws, error):
#         """Handle WebSocket error"""
#         logger.error(f"{self.__class__.__name__} error: {error}")
#         if self.on_error:
#             self.on_error(error)
#
#         # Force close to avoid ghost connections
#         if ws and hasattr(ws, 'sock') and ws.sock:
#             ws.close()
#
#     def _on_close(self, ws, close_status_code=None, close_msg=None):
#         """Handle WebSocket close event"""
#         self.is_connected = False
#         self._clear_timers()
#
#         if self.on_close:
#             self.on_close(close_status_code, close_msg)
#
#         if self.on_disconnect:
#             self.on_disconnect()
#
#         logger.info(f"{self.__class__.__name__} disconnected")
#
#         # Only auto-reconnect if it wasn't intentional
#         if self.config.enable_reconnect and not self.is_intentional_disconnect:
#             self._attempt_reconnection()
#
#         # Reset flag
#         self.is_intentional_disconnect = False
#
#     def _start_ping_timer(self):
#         """Start ping timer"""
#
#         def send_ping():
#             if self.connected():
#                 try:
#                     self.ws.send('PONG')
#                     if self.config.debug:
#                         logger.debug("Sent PONG")
#                 except Exception as e:
#                     logger.error(f"Failed to send ping: {e}")
#
#             # Schedule next ping
#             if self.is_connected:
#                 self.ping_timer = threading.Timer(self.config.ping_interval, send_ping)
#                 self.ping_timer.start()
#
#         self.ping_timer = threading.Timer(self.config.ping_interval, send_ping)
#         self.ping_timer.start()
#
#     def _start_read_timer(self):
#         """Start read timeout timer"""
#
#         def check_read_timeout():
#             if time.time() - self.last_read >= self.config.read_timeout:
#                 logger.warning("Read timeout, closing connection")
#                 if self.ws:
#                     self.ws.close()
#                 self._clear_timers()
#             else:
#                 # Schedule next check
#                 if self.is_connected:
#                     self.read_timer = threading.Timer(self.config.read_timeout, check_read_timeout)
#                     self.read_timer.start()
#
#         self.read_timer = threading.Timer(self.config.read_timeout, check_read_timeout)
#         self.read_timer.start()
#
#     def _clear_timers(self):
#         """Clear all timers"""
#         if self.reconnect_timer:
#             self.reconnect_timer.cancel()
#         if self.ping_timer:
#             self.ping_timer.cancel()
#         if self.read_timer:
#             self.read_timer.cancel()
#
#     def _attempt_reconnection(self):
#         """Attempt to reconnect with exponential backoff (matching JS implementation)"""
#         if self.current_reconnection_count > self.config.max_reconnect_attempts:
#             logger.error("Exhausted reconnect retries")
#             if self.on_no_reconnect:
#                 self.on_no_reconnect()
#             return
#
#         reconnect_delay = 0
#
#         # First few attempts: immediate reconnection (0 delay)
#         if self.current_reconnection_count < self.config.immediate_reconnect_attempts:
#             reconnect_delay = 0
#         # After immediate attempts: use exponential backoff
#         else:
#             backoff_attempt = self.current_reconnection_count - self.config.immediate_reconnect_attempts
#             reconnect_delay = min(2 ** backoff_attempt, self.config.max_reconnect_delay)
#
#         self.current_reconnection_count += 1
#
#         if self.on_reconnect:
#             self.on_reconnect(self.current_reconnection_count, reconnect_delay)
#
#         if self.reconnect_timer:
#             self.reconnect_timer.cancel()
#
#         if reconnect_delay == 0:
#             logger.info(f"reconnecting immediately (attempt {self.current_reconnection_count})...")
#             self.connect()
#         else:
#             logger.info(f"reconnect attempt {self.current_reconnection_count} after {reconnect_delay} seconds")
#             self.reconnect_timer = threading.Timer(reconnect_delay, self.connect)
#             self.reconnect_timer.start()
#
#
# class OrderStream(BaseSocket):
#     """WebSocket stream for order updates"""
#
#     def __init__(self, config: ConnectionConfig):
#         super().__init__(config)
#         self.on_order_update = None
#
#     def _build_url(self) -> str:
#         """Build order updates WebSocket URL"""
#         return f"wss://order-updates.arrow.trade?appID={self.config.appID}&token={self.config.token}"
#
#     def _on_message(self, ws, message):
#         """Handle order update message"""
#         super()._on_message(ws, message)
#
#         try:
#             # Parse text message only (no binary handling for orders)
#             if isinstance(message, str):
#                 data = json.loads(message)
#                 if data.get('id') and self.on_order_update:
#                     self.on_order_update(data)
#         except json.JSONDecodeError as e:
#             logger.error(f"Failed to parse order message: {e}")
#
#
# class DataStream(BaseSocket):
#     """WebSocket stream for market data with subscription management"""
#
#     def __init__(self, config: ConnectionConfig):
#         super().__init__(config)
#         self.subscriptions = {
#             DataMode.LTPC.value: {},
#             DataMode.QUOTE.value: {},
#             DataMode.FULL.value: {}
#         }
#         self.on_ticks = None
#
#     def _build_url(self) -> str:
#         """Build market data WebSocket URL"""
#         return f"wss://ds.arrow.trade?appID={self.config.appID}&token={self.config.token}"
#
#     def _on_open(self, ws):
#         """Handle connection open and resubscribe"""
#         super()._on_open(ws)
#
#         # Resubscribe to all existing subscriptions
#         for mode in [DataMode.LTPC, DataMode.QUOTE, DataMode.FULL]:
#             tokens = list(self.subscriptions[mode.value].keys())
#             if tokens:
#                 self.subscribe(mode, tokens)
#
#     def _on_message(self, ws, message):
#         """Handle market data message"""
#         super()._on_message(ws, message)
#
#         try:
#             # Handle binary data only (market ticks)
#             if isinstance(message, bytes) and len(message) > 2:
#                 tick = self._parse_binary(message)
#                 if tick and self.on_ticks:
#                     self.on_ticks(tick)
#         except Exception as e:
#             logger.error(f"Failed to parse market data: {e}")
#
#     def subscribe(self, mode: DataMode, tokens: List[int]):
#         """Subscribe to market data"""
#         # Update local subscriptions
#         for token in tokens:
#             self.subscriptions[mode.value][token] = 1
#
#         if not self.connected():
#             return
#
#         if tokens:
#             message = {
#                 "code": MessageType.SUBSCRIBE.value,
#                 "mode": mode.value,
#                 mode.value: tokens
#             }
#             self._send_message(message)
#
#         logger.info(f"Subscribed to {len(tokens)} tokens in {mode.value} mode")
#
#     def unsubscribe(self, mode: DataMode, tokens: List[int]):
#         """Unsubscribe from market data"""
#         # Update local subscriptions
#         for token in tokens:
#             self.subscriptions[mode.value].pop(token, None)
#
#         if not self.connected():
#             return
#
#         if tokens:
#             message = {
#                 "code": MessageType.UNSUBSCRIBE.value,
#                 "mode": mode.value,
#                 mode.value: tokens
#             }
#             self._send_message(message)
#
#         logger.info(f"Unsubscribed from {len(tokens)} tokens in {mode.value} mode")
#
#     def _send_message(self, message: Dict):
#         """Send JSON message to WebSocket"""
#         try:
#             json_message = json.dumps(message)
#             if self.config.debug:
#                 logger.debug(f"Sending: {json_message}")
#             self.ws.send(json_message)
#         except Exception as e:
#             logger.error(f"Failed to send message: {e}")
#
#     def _parse_binary(self, data: bytes) -> Optional[MarketTick]:
#         """Parse binary market data (matching JS implementation exactly)"""
#         if len(data) < 17:
#             return None
#
#         try:
#             # Parse basic data
#             tick = MarketTick(
#                 token=self._big_endian_to_int(data[0:4]),
#                 ltp=self._big_endian_to_int(data[4:8])
#             )
#
#             # LTPC mode (17 bytes)
#             if len(data) >= 17:
#                 tick.close = self._big_endian_to_int(data[13:17])
#
#                 # Calculate net change
#                 if tick.close != 0:
#                     tick.net_change = round(((tick.ltp - tick.close) / tick.close) * 100, 2)
#                 else:
#                     tick.net_change = 0.0
#
#                 # Set change flag
#                 if tick.ltp > tick.close:
#                     tick.change_flag = 43  # ASCII '+'
#                 elif tick.ltp < tick.close:
#                     tick.change_flag = 45  # ASCII '-'
#                 else:
#                     tick.change_flag = 32  # No change
#
#                 tick.mode = DataMode.LTPC.value
#
#             # Quote mode (93 bytes)
#             if len(data) >= 93:
#                 tick.ltq = self._big_endian_to_int(data[13:17])
#                 tick.avg_price = self._big_endian_to_int(data[17:21])
#                 tick.total_buy_quantity = self._big_endian_to_int(data[21:29])
#                 tick.total_sell_quantity = self._big_endian_to_int(data[29:37])
#                 tick.open = self._big_endian_to_int(data[37:41])
#                 tick.high = self._big_endian_to_int(data[41:45])
#                 tick.close = self._big_endian_to_int(data[45:49])
#                 tick.low = self._big_endian_to_int(data[49:53])
#                 tick.volume = self._big_endian_to_int(data[53:61])
#                 tick.ltt = self._big_endian_to_int(data[61:65])
#                 tick.time = self._big_endian_to_int(data[65:69])
#                 tick.oi = self._big_endian_to_int(data[69:77])
#                 tick.oi_day_high = self._big_endian_to_int(data[77:85])
#                 tick.oi_day_low = self._big_endian_to_int(data[85:93])
#
#                 # Recalculate net change with close from quote data
#                 if tick.close != 0:
#                     tick.net_change = round(((tick.ltp - tick.close) / tick.close) * 100, 2)
#                 else:
#                     tick.net_change = 0.0
#
#                 # Recalculate change flag
#                 if tick.ltp > tick.close:
#                     tick.change_flag = 43
#                 elif tick.ltp < tick.close:
#                     tick.change_flag = 45
#                 else:
#                     tick.change_flag = 32
#
#                 tick.mode = DataMode.QUOTE.value
#
#             # Full mode (241 bytes)
#             if len(data) == 241:
#                 tick.lower_limit = self._big_endian_to_int(data[93:97])
#                 tick.upper_limit = self._big_endian_to_int(data[97:101])
#
#                 # Parse bids and asks (10 levels total: 5 bids, 5 asks)
#                 bids = []
#                 asks = []
#
#                 for i in range(10):
#                     offset = 101 + i * 14
#                     quantity = self._big_endian_to_int(data[offset:offset + 8])
#                     price = self._big_endian_to_int(data[offset + 8:offset + 12])
#                     orders = self._big_endian_to_int(data[offset + 12:offset + 14])
#
#                     level_data = {
#                         'price': price,
#                         'quantity': quantity,
#                         'orders': orders
#                     }
#
#                     if i >= 5:
#                         asks.append(level_data)
#                     else:
#                         bids.append(level_data)
#
#                 tick.bids = bids
#                 tick.asks = asks
#                 tick.mode = DataMode.FULL.value
#
#             # Reset net change if close is 0
#             if tick.close == 0:
#                 tick.net_change = 0.0
#
#             return tick
#
#         except Exception as e:
#             logger.error(f"Error parsing binary data: {e}")
#             return None
#
#     def _big_endian_to_int(self, buffer: bytes) -> int:
#         """Convert big-endian bytes to integer (matching JS implementation exactly)"""
#         value = 0
#         length = len(buffer)
#
#         for i in range(length):
#             j = length - 1 - i
#             value += buffer[j] << (i * 8)
#
#         return value
#
#
# class HFTDataStream(BaseSocket):
#     """WebSocket stream for high-frequency trading market data with binary protocol"""
#
#     def __init__(self, config: ConnectionConfig):
#         super().__init__(config)
#         self.subscriptions = {
#             'ltpc': {},
#             'quote': {},
#             'full': {}
#         }
#         self.on_ltp_tick = None
#         self.on_quote_tick = None
#         self.on_response = None
#
#     def _build_url(self) -> str:
#         """Build HFT market data WebSocket URL"""
#         return f"wss://socket.arrow.trade?appID={self.config.appID}&token={self.config.token}"
#
#     def _on_open(self, ws):
#         """Handle connection open and resubscribe"""
#         super()._on_open(ws)
#
#         # Resubscribe to all existing subscriptions
#         for mode in ['ltpc', 'quote', 'full']:
#             tokens = list(self.subscriptions[mode].keys())
#             if tokens:
#                 self.subscribe(mode, tokens)
#
#     def _on_message(self, ws, message):
#         """Handle HFT market data message (binary protocol)"""
#         super()._on_message(ws, message)
#
#         try:
#             # Handle binary data only
#             if isinstance(message, bytes) and len(message) >= 2:
#                 # Read packet size and type
#                 size = struct.unpack('<H', message[0:2])[0]
#
#                 if len(message) < size:
#                     logger.warning(f"Incomplete packet: expected {size} bytes, got {len(message)}")
#                     return
#
#                 pkt_type = message[2]
#
#                 # PKT_TYPE_RESPONSE (99)
#                 if pkt_type == 99 and len(message) >= 540:
#                     response = self._parse_response(message)
#                     if response and self.on_response:
#                         self.on_response(response)
#
#                 # PKT_TYPE_LTP (1)
#                 elif pkt_type == 1 and len(message) == 44:
#                     ltp_tick = self._parse_ltp_packet(message)
#                     if ltp_tick and self.on_ltp_tick:
#                         self.on_ltp_tick(ltp_tick)
#
#                 # PKT_TYPE_QUOTE (2)
#                 elif pkt_type == 2 and len(message) == 196:
#                     quote_tick = self._parse_quote_packet(message)
#                     if quote_tick and self.on_quote_tick:
#                         self.on_quote_tick(quote_tick)
#
#         except Exception as e:
#             logger.error(f"Failed to parse HFT market data: {e}")
#
#     def subscribe(self, mode: str, symbols: List[Union[str, int]], latency: int = 1000):
#         """
#         Subscribe to market data
#
#         Args:
#             mode: 'ltpc', 'quote', or 'full' (or short forms 'l', 'q', 'f')
#             symbols: List of symbol names (strings) or token IDs (integers)
#             latency: Time interval between ticks in milliseconds (50-60000, default 1000)
#         """
#         # Normalize mode
#         mode_map = {'l': 'ltpc', 'q': 'quote', 'f': 'full'}
#         normalized_mode = mode_map.get(mode, mode)
#
#         # Update local subscriptions
#         for symbol in symbols:
#             key = symbol if isinstance(symbol, str) else str(symbol)
#             self.subscriptions[normalized_mode][key] = 1
#
#         if not self.connected():
#             return
#
#         if symbols:
#             # Build subscription message
#             message = {
#                 "code": "sub",
#                 "mode": normalized_mode,
#                 "latency": latency
#             }
#
#             # Add symbols based on type
#             if all(isinstance(s, str) for s in symbols):
#                 message["symbols"] = symbols
#             elif all(isinstance(s, int) for s in symbols):
#                 # For token IDs, we need exchange segment info
#                 # This is a simplified version - in production you'd need proper segment mapping
#                 message["symIds"] = [{"exch_seg": 0, "ids": symbols}]
#             else:
#                 logger.error("Mixed symbol types not supported")
#                 return
#
#             self._send_message(message)
#
#         logger.info(f"Subscribed to {len(symbols)} symbols in {normalized_mode} mode with {latency}ms latency")
#
#     def unsubscribe(self, mode: str, symbols: List[Union[str, int]]):
#         """
#         Unsubscribe from market data
#
#         Args:
#             mode: 'ltpc', 'quote', or 'full' (or short forms 'l', 'q', 'f')
#             symbols: List of symbol names (strings) or token IDs (integers)
#         """
#         # Normalize mode
#         mode_map = {'l': 'ltpc', 'q': 'quote', 'f': 'full'}
#         normalized_mode = mode_map.get(mode, mode)
#
#         # Update local subscriptions
#         for symbol in symbols:
#             key = symbol if isinstance(symbol, str) else str(symbol)
#             self.subscriptions[normalized_mode].pop(key, None)
#
#         if not self.connected():
#             return
#
#         if symbols:
#             # Build unsubscription message
#             message = {
#                 "code": "unsub",
#                 "mode": normalized_mode
#             }
#
#             # Add symbols based on type
#             if all(isinstance(s, str) for s in symbols):
#                 message["symbols"] = symbols
#             elif all(isinstance(s, int) for s in symbols):
#                 message["symIds"] = [{"exch_seg": 0, "ids": symbols}]
#             else:
#                 logger.error("Mixed symbol types not supported")
#                 return
#
#             self._send_message(message)
#
#         logger.info(f"Unsubscribed from {len(symbols)} symbols in {normalized_mode} mode")
#
#     def _send_message(self, message: Dict):
#         """Send JSON message to WebSocket"""
#         try:
#             json_message = json.dumps(message)
#             if self.config.debug:
#                 logger.debug(f"Sending: {json_message}")
#             self.ws.send(json_message)
#         except Exception as e:
#             logger.error(f"Failed to send message: {e}")
#
#     def _parse_response(self, data: bytes) -> Optional[Dict]:
#         """Parse binary response packet (540 bytes)"""
#         try:
#             response = {
#                 'size': struct.unpack('<I', data[0:4])[0],
#                 'pkt_type': data[4],
#                 'exch_seg': data[5],
#                 'error_code': data[6:22].decode('utf-8').rstrip('\x00'),
#                 'error_msg': data[22:534].decode('utf-8').rstrip('\x00'),
#                 'request_type': data[534],  # 0=subscribe, 1=unsubscribe
#                 'mode': data[535],  # 0=ltpc, 1=quote, 2=full
#                 'success_count': struct.unpack('<H', data[536:538])[0],
#                 'error_count': struct.unpack('<H', data[538:540])[0]
#             }
#
#             # Convert numeric values to readable strings
#             request_type_map = {0: 'subscribe', 1: 'unsubscribe'}
#             mode_map = {0: 'ltpc', 1: 'quote', 2: 'full'}
#
#             response['request_type_str'] = request_type_map.get(response['request_type'], 'unknown')
#             response['mode_str'] = mode_map.get(response['mode'], 'unknown')
#
#             return response
#         except Exception as e:
#             logger.error(f"Error parsing response packet: {e}")
#             return None
#
#     def _parse_ltp_packet(self, data: bytes) -> Optional[Dict]:
#         """Parse LTP packet (44 bytes)"""
#         try:
#             tick = {
#                 'size': struct.unpack('<H', data[0:2])[0],
#                 'pkt_type': data[2],
#                 'exch_seg': data[3],
#                 'token': struct.unpack('<i', data[4:8])[0],
#                 'ltp': struct.unpack('<i', data[8:12])[0],
#                 'vwap': struct.unpack('<i', data[12:16])[0],
#                 'volume': struct.unpack('<q', data[16:24])[0],
#                 'ltt': struct.unpack('<Q', data[24:32])[0],
#                 'atv': struct.unpack('<I', data[32:36])[0],
#                 'btv': struct.unpack('<I', data[36:40])[0],
#                 'seq_no': struct.unpack('<I', data[40:44])[0]
#             }
#             return tick
#         except Exception as e:
#             logger.error(f"Error parsing LTP packet: {e}")
#             return None
#
#     def _parse_quote_packet(self, data: bytes) -> Optional[Dict]:
#         """Parse Quote packet (196 bytes)"""
#         try:
#             tick = {
#                 'size': struct.unpack('<H', data[0:2])[0],
#                 'pkt_type': data[2],
#                 'exch_seg': data[3],
#                 'token': struct.unpack('<i', data[4:8])[0],
#                 'ltp': struct.unpack('<i', data[8:12])[0],
#                 'ltq': struct.unpack('<i', data[12:16])[0],
#                 'vwap': struct.unpack('<i', data[16:20])[0],
#                 'open': struct.unpack('<i', data[20:24])[0],
#                 'high': struct.unpack('<i', data[24:28])[0],
#                 'close': struct.unpack('<i', data[28:32])[0],
#                 'low': struct.unpack('<i', data[32:36])[0],
#                 'ltt': struct.unpack('<i', data[36:40])[0],
#                 'dpr_l': struct.unpack('<i', data[40:44])[0],
#                 'dpr_h': struct.unpack('<i', data[44:48])[0],
#                 'tbq': struct.unpack('<q', data[48:56])[0],
#                 'tsq': struct.unpack('<q', data[56:64])[0],
#                 'volume': struct.unpack('<q', data[64:72])[0],
#                 'bid_px': list(struct.unpack('<5i', data[72:92])),
#                 'ask_px': list(struct.unpack('<5i', data[92:112])),
#                 'bid_size': list(struct.unpack('<5i', data[112:132])),
#                 'ask_size': list(struct.unpack('<5i', data[132:152])),
#                 'bid_ord': list(struct.unpack('<5H', data[152:162])),
#                 'ask_ord': list(struct.unpack('<5H', data[162:172])),
#                 'oi': struct.unpack('<i', data[172:176])[0],
#                 'ts': struct.unpack('<Q', data[176:184])[0],
#                 'seq_no': struct.unpack('<I', data[184:188])[0],
#                 'atv': struct.unpack('<I', data[188:192])[0],
#                 'btv': struct.unpack('<I', data[192:196])[0]
#             }
#             return tick
#         except Exception as e:
#             logger.error(f"Error parsing Quote packet: {e}")
#             return None
#
#
# class ArrowStreams:
#     """Main client class providing order, data, and HFT streams"""
#
#     def __init__(self, appID: str, token: str, debug: bool = False):
#         self.config = ConnectionConfig(appID=appID, token=token, debug=debug)
#
#         # Initialize streams
#         self.order_stream = OrderStream(self.config)
#         self.data_stream = DataStream(self.config)
#         self.hft_data_stream = HFTDataStream(self.config)
#
#         # Status tracking
#         self.status = {
#             'order_stream': SocketStatus.DISCONNECTED,
#             'data_stream': SocketStatus.DISCONNECTED,
#             'hft_data_stream': SocketStatus.DISCONNECTED
#         }
#
#         # Set up event handlers for status tracking
#         self._setup_status_handlers()
#
#     def connect_order_stream(self):
#         """Connect to order updates stream"""
#         self.order_stream.connect()
#
#     def connect_data_stream(self):
#         """Connect to market data stream"""
#         self.data_stream.connect()
#
#     def connect_hft_data_stream(self):
#         """Connect to HFT market data stream"""
#         self.hft_data_stream.connect()
#
#     def connect_all(self):
#         """Connect to all streams"""
#         self.connect_order_stream()
#         self.connect_data_stream()
#         self.connect_hft_data_stream()
#
#     def disconnect_all(self):
#         """Disconnect from all streams"""
#         self.order_stream.disconnect()
#         self.data_stream.disconnect()
#         self.hft_data_stream.disconnect()
#
#     def subscribe_market_data(self, mode: DataMode, tokens: List[int]):
#         """Subscribe to market data (DataStream)"""
#         self.data_stream.subscribe(mode, tokens)
#
#     def unsubscribe_market_data(self, mode: DataMode, tokens: List[int]):
#         """Unsubscribe from market data (DataStream)"""
#         self.data_stream.unsubscribe(mode, tokens)
#
#     def subscribe_hft_data(self, mode: str, symbols: List[Union[str, int]], latency: int = 1000):
#         """Subscribe to HFT market data (HFTDataStream)"""
#         self.hft_data_stream.subscribe(mode, symbols, latency)
#
#     def unsubscribe_hft_data(self, mode: str, symbols: List[Union[str, int]]):
#         """Unsubscribe from HFT market data (HFTDataStream)"""
#         self.hft_data_stream.unsubscribe(mode, symbols)
#
#     def get_status(self) -> Dict[str, str]:
#         """Get connection status for all streams"""
#         return {
#             'order_stream': self.status['order_stream'].value,
#             'data_stream': self.status['data_stream'].value,
#             'hft_data_stream': self.status['hft_data_stream'].value
#         }
#
#     def _setup_status_handlers(self):
#         """Set up status tracking handlers"""
#         # Order stream handlers
#         self.order_stream.on_connect = lambda: self._update_status('order_stream', SocketStatus.CONNECTED)
#         self.order_stream.on_disconnect = lambda: self._update_status('order_stream', SocketStatus.CONNECTING)
#         self.order_stream.on_reconnect = lambda *args: self._update_status('order_stream', SocketStatus.CONNECTING)
#
#         # Data stream handlers
#         self.data_stream.on_connect = lambda: self._update_status('data_stream', SocketStatus.CONNECTED)
#         self.data_stream.on_disconnect = lambda: self._update_status('data_stream', SocketStatus.CONNECTING)
#         self.data_stream.on_reconnect = lambda *args: self._update_status('data_stream', SocketStatus.CONNECTING)
#
#         # HFT data stream handlers
#         self.hft_data_stream.on_connect = lambda: self._update_status('hft_data_stream', SocketStatus.CONNECTED)
#         self.hft_data_stream.on_disconnect = lambda: self._update_status('hft_data_stream', SocketStatus.CONNECTING)
#         self.hft_data_stream.on_reconnect = lambda *args: self._update_status('hft_data_stream',
#                                                                               SocketStatus.CONNECTING)
#
#     def _update_status(self, stream: str, status: SocketStatus):
#         """Update stream status"""
#         self.status[stream] = status
#         if self.config.debug:
#             logger.debug(f"{stream} status: {status.value}")

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


class HFTDataStream(BaseSocket):
    """WebSocket stream for high-frequency trading market data with binary protocol.

    Protocol Details:
        - Endpoint: wss://socket.arrow.trade?appID=<appID>&token=<token>
        - All multi-byte integers are in little-endian format
        - All prices are in paise (1 rupee = 100 paise)
        - Timestamps are in nanoseconds since Unix epoch

    Packet Types:
        - PKT_TYPE_LTP (1): 40 bytes - Last traded price data
        - PKT_TYPE_FULL (2): 192 bytes - Full market depth data
        - PKT_TYPE_RESPONSE (99): 540 bytes - Server response to requests

    Exchange Segments:
        - 0: NSE_CM (NSE Cash Market)
        - 1: NSE_FO (NSE Futures & Options)
        - 2: BSE_CM (BSE Cash Market)
        - 3: BSE_FO (BSE Futures & Options)

    Symbol Name Formats:
        - NSECM: NSE.<UNDERLYING>-<SERIES> (e.g., NSE.SBIN-EQ)
        - NSEFO Options: <UNDERLYING><DD><MON><YY><C|P><STRIKE> (e.g., NYKAA30DEC25C232.5)
        - NSEFO Futures: <UNDERLYING><DD><MON><YY>F (e.g., BANKNIFTY30DEC25F)
        - BSECM: BSE.<UNDERLYING> (e.g., BSE.SBIN)
        - BSEFO Options: <ASSET_TYPE><DD><MON><YY><C|P><STRIKE> (e.g., SENSEX01JAN26C74900)
        - BSEFO Futures: <ASSET_TYPE><DD><MON><YY>F (e.g., SENSEX01JAN26F)

    Rate Limits:
        - Maximum 100 requests per second per connection
        - Maximum 4096 symbols per subscription
        - Maximum request size: 16KB

    Note: Currently supports LTP only for NSEFO and NSECM, and full for others.
    """

    # Packet type constants
    PKT_TYPE_LTP = 1
    PKT_TYPE_FULL = 2
    PKT_TYPE_RESPONSE = 99

    # Packet sizes (in bytes)
    PKT_SIZE_LTP = 40
    PKT_SIZE_FULL = 192
    PKT_SIZE_RESPONSE = 540

    # Exchange segment constants
    EXCH_NSE_CM = 0
    EXCH_NSE_FO = 1
    EXCH_BSE_CM = 2
    EXCH_BSE_FO = 3

    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.subscriptions = {
            'ltpc': {},
            'full': {}
        }
        self.on_ltp_tick = None
        self.on_full_tick = None
        self.on_response = None

    def _build_url(self) -> str:
        """Build HFT market data WebSocket URL"""
        return f"wss://socket.arrow.trade?appID={self.config.appID}&token={self.config.token}"

    def _on_open(self, ws):
        """Handle connection open and resubscribe"""
        super()._on_open(ws)

        # Resubscribe to all existing subscriptions
        for mode in ['ltpc', 'full']:
            tokens = list(self.subscriptions[mode].keys())
            if tokens:
                self.subscribe(mode, tokens)

    def _on_message(self, ws, message):
        """Handle HFT market data message (binary protocol)"""
        super()._on_message(ws, message)

        try:
            # Handle binary data only
            if isinstance(message, bytes) and len(message) >= 2:
                # Read packet size (first 2 bytes, little-endian int16)
                size = struct.unpack('<h', message[0:2])[0]

                if len(message) < size:
                    logger.warning(f"Incomplete packet: expected {size} bytes, got {len(message)}")
                    return

                pkt_type = message[2]

                # PKT_TYPE_RESPONSE (99) - 540 bytes
                if pkt_type == self.PKT_TYPE_RESPONSE and len(message) >= self.PKT_SIZE_RESPONSE:
                    response = self._parse_response(message)
                    if response and self.on_response:
                        self.on_response(response)

                # PKT_TYPE_LTP (1) - 40 bytes
                elif pkt_type == self.PKT_TYPE_LTP and len(message) >= self.PKT_SIZE_LTP:
                    ltp_tick = self._parse_ltp_packet(message)
                    if ltp_tick and self.on_ltp_tick:
                        self.on_ltp_tick(ltp_tick)

                # PKT_TYPE_FULL (2) - 192 bytes
                elif pkt_type == self.PKT_TYPE_FULL and len(message) >= self.PKT_SIZE_FULL:
                    full_tick = self._parse_full_packet(message)
                    if full_tick and self.on_full_tick:
                        self.on_full_tick(full_tick)

        except Exception as e:
            logger.error(f"Failed to parse HFT market data: {e}")

    def subscribe(self, mode: str, symbols: List[Union[str, int]], latency: int = 1000):
        """Subscribe to market data.

        Args:
            mode: Data mode - 'ltpc' or 'l' for LTP, 'full' or 'f' for full market depth
            symbols: List of symbol names (strings) or token IDs (integers)
                Symbol name formats:
                - NSECM: NSE.<UNDERLYING>-<SERIES> (e.g., "NSE.SBIN-EQ")
                - NSEFO Options: <UNDERLYING><DD><MON><YY><C|P><STRIKE> (e.g., "NYKAA30DEC25C232.5")
                - NSEFO Futures: <UNDERLYING><DD><MON><YY>F (e.g., "BANKNIFTY30DEC25F")
                - BSECM: BSE.<UNDERLYING> (e.g., "BSE.SBIN")
                - BSEFO Options: <ASSET_TYPE><DD><MON><YY><C|P><STRIKE> (e.g., "SENSEX01JAN26C74900")
                - BSEFO Futures: <ASSET_TYPE><DD><MON><YY>F (e.g., "SENSEX01JAN26F")
            latency: Time interval between ticks in milliseconds (50-60000, default 1000)

        Example:
            # Subscribe by symbol names
            stream.subscribe('ltpc', ['NSE.SBIN-EQ', 'BSE.RELIANCE'], latency=100)

            # Subscribe by token IDs
            stream.subscribe('full', [5042, 4449], latency=200)
        """
        # Normalize mode
        mode_map = {'l': 'ltpc', 'f': 'full'}
        normalized_mode = mode_map.get(mode, mode)

        if normalized_mode not in ['ltpc', 'full']:
            logger.error(f"Invalid mode: {mode}. Must be 'ltpc', 'l', 'full', or 'f'")
            return

        # Update local subscriptions
        for symbol in symbols:
            key = symbol if isinstance(symbol, str) else str(symbol)
            self.subscriptions[normalized_mode][key] = 1

        if not self.connected():
            return

        if symbols:
            # Build subscription message
            message = {
                "code": "sub",
                "mode": normalized_mode,
                "latency": latency
            }

            # Add symbols based on type
            if all(isinstance(s, str) for s in symbols):
                message["symbols"] = symbols
            elif all(isinstance(s, int) for s in symbols):
                # Group by exchange segment if provided, otherwise use default
                message["symIds"] = [{"exch_seg": 0, "ids": symbols}]
            else:
                logger.error("Mixed symbol types not supported. Use all strings or all integers.")
                return

            self._send_message(message)

        logger.info(f"Subscribed to {len(symbols)} symbols in {normalized_mode} mode with {latency}ms latency")

    def subscribe_by_segment(self, mode: str, segment_symbols: Dict[int, List[int]], latency: int = 1000):
        """Subscribe to market data with explicit exchange segment mapping.

        Args:
            mode: Data mode - 'ltpc' or 'l' for LTP, 'full' or 'f' for full market depth
            segment_symbols: Dictionary mapping exchange segment to list of token IDs
                Exchange segments:
                - 0: NSE_CM (NSE Cash Market)
                - 1: NSE_FO (NSE Futures & Options)
                - 2: BSE_CM (BSE Cash Market)
                - 3: BSE_FO (BSE Futures & Options)
            latency: Time interval between ticks in milliseconds (50-60000, default 1000)

        Example:
            stream.subscribe_by_segment('full', {
                HFTDataStream.EXCH_NSE_FO: [5042, 4449, 91],
                HFTDataStream.EXCH_BSE_CM: [100, 200]
            }, latency=100)
        """
        # Normalize mode
        mode_map = {'l': 'ltpc', 'f': 'full'}
        normalized_mode = mode_map.get(mode, mode)

        if normalized_mode not in ['ltpc', 'full']:
            logger.error(f"Invalid mode: {mode}. Must be 'ltpc', 'l', 'full', or 'f'")
            return

        # Update local subscriptions
        for segment, ids in segment_symbols.items():
            for token_id in ids:
                key = f"{segment}:{token_id}"
                self.subscriptions[normalized_mode][key] = 1

        if not self.connected():
            return

        # Build subscription message
        sym_ids = [{"exch_seg": seg, "ids": ids} for seg, ids in segment_symbols.items() if ids]

        if sym_ids:
            message = {
                "code": "sub",
                "mode": normalized_mode,
                "latency": latency,
                "symIds": sym_ids
            }
            self._send_message(message)

        total_symbols = sum(len(ids) for ids in segment_symbols.values())
        logger.info(f"Subscribed to {total_symbols} symbols in {normalized_mode} mode with {latency}ms latency")

    def unsubscribe(self, mode: str, symbols: List[Union[str, int]]):
        """Unsubscribe from market data.

        Args:
            mode: Data mode - 'ltpc' or 'l' for LTP, 'full' or 'f' for full market depth
            symbols: List of symbol names (strings) or token IDs (integers)

        Example:
            stream.unsubscribe('ltpc', ['NSE.SBIN-EQ'])
        """
        # Normalize mode
        mode_map = {'l': 'ltpc', 'f': 'full'}
        normalized_mode = mode_map.get(mode, mode)

        if normalized_mode not in ['ltpc', 'full']:
            logger.error(f"Invalid mode: {mode}. Must be 'ltpc', 'l', 'full', or 'f'")
            return

        # Update local subscriptions
        for symbol in symbols:
            key = symbol if isinstance(symbol, str) else str(symbol)
            self.subscriptions[normalized_mode].pop(key, None)

        if not self.connected():
            return

        if symbols:
            # Build unsubscription message
            message = {
                "code": "unsub",
                "mode": normalized_mode
            }

            # Add symbols based on type
            if all(isinstance(s, str) for s in symbols):
                message["symbols"] = symbols
            elif all(isinstance(s, int) for s in symbols):
                message["symIds"] = [{"exch_seg": 0, "ids": symbols}]
            else:
                logger.error("Mixed symbol types not supported. Use all strings or all integers.")
                return

            self._send_message(message)

        logger.info(f"Unsubscribed from {len(symbols)} symbols in {normalized_mode} mode")

    def unsubscribe_by_segment(self, mode: str, segment_symbols: Dict[int, List[int]]):
        """Unsubscribe from market data with explicit exchange segment mapping.

        Args:
            mode: Data mode - 'ltpc' or 'l' for LTP, 'full' or 'f' for full market depth
            segment_symbols: Dictionary mapping exchange segment to list of token IDs

        Example:
            stream.unsubscribe_by_segment('full', {
                HFTDataStream.EXCH_NSE_FO: [5042, 4449]
            })
        """
        # Normalize mode
        mode_map = {'l': 'ltpc', 'f': 'full'}
        normalized_mode = mode_map.get(mode, mode)

        if normalized_mode not in ['ltpc', 'full']:
            logger.error(f"Invalid mode: {mode}. Must be 'ltpc', 'l', 'full', or 'f'")
            return

        # Update local subscriptions
        for segment, ids in segment_symbols.items():
            for token_id in ids:
                key = f"{segment}:{token_id}"
                self.subscriptions[normalized_mode].pop(key, None)

        if not self.connected():
            return

        # Build unsubscription message
        sym_ids = [{"exch_seg": seg, "ids": ids} for seg, ids in segment_symbols.items() if ids]

        if sym_ids:
            message = {
                "code": "unsub",
                "mode": normalized_mode,
                "symIds": sym_ids
            }
            self._send_message(message)

        total_symbols = sum(len(ids) for ids in segment_symbols.values())
        logger.info(f"Unsubscribed from {total_symbols} symbols in {normalized_mode} mode")

    def _send_message(self, message: Dict):
        """Send JSON message to WebSocket"""
        try:
            json_message = json.dumps(message)
            if self.config.debug:
                logger.debug(f"Sending: {json_message}")
            self.ws.send(json_message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def _parse_response(self, data: bytes) -> Optional[Dict]:
        """Parse binary response packet (540 bytes).

        Response Structure:
            Offset  Size  Type      Field         Description
            0       4     uint32    size          Total packet size
            4       1     uint8     pkt_type      99 (PKT_TYPE_RESPONSE)
            5       1     uint8     exch_seg      0 (not used)
            6       16    char[]    error_code    Error code string (null-terminated)
            22      512   char[]    error_msg     Error message (null-terminated)
            534     1     uint8     request_type  0=subscribe, 1=unsubscribe
            535     1     uint8     mode          0=ltpc, 1=full
            536     2     uint16    success_count Number of successful symbols
            538     2     uint16    error_count   Number of failed symbols

        Error Codes:
            - SUCCESS: All symbols processed successfully
            - E_PARTIAL: Some symbols failed
            - E_ALL_INVALID: All symbols failed
            - E_INVALID_JSON: Malformed JSON request
            - E_MISSING_FIELD: Required field missing
            - E_INVALID_PARAM: Invalid parameter value
            - E_PARSE_ERROR: General parsing error
        """
        try:
            response = {
                'size': struct.unpack('<I', data[0:4])[0],
                'pkt_type': data[4],
                'exch_seg': data[5],
                'error_code': data[6:22].decode('utf-8').rstrip('\x00'),
                'error_msg': data[22:534].decode('utf-8').rstrip('\x00'),
                'request_type': data[534],  # 0=subscribe, 1=unsubscribe
                'mode': data[535],  # 0=ltpc, 1=full
                'success_count': struct.unpack('<H', data[536:538])[0],
                'error_count': struct.unpack('<H', data[538:540])[0]
            }

            # Convert numeric values to readable strings
            request_type_map = {0: 'subscribe', 1: 'unsubscribe'}
            mode_map = {0: 'ltpc', 1: 'full'}

            response['request_type_str'] = request_type_map.get(response['request_type'], 'unknown')
            response['mode_str'] = mode_map.get(response['mode'], 'unknown')

            return response
        except Exception as e:
            logger.error(f"Error parsing response packet: {e}")
            return None

    def _parse_ltp_packet(self, data: bytes) -> Optional[Dict]:
        """Parse LTP packet (40 bytes).

        LTP Packet Structure:
            Offset  Size  Type     Field     Description
            0       2     int16    size      Packet size in bytes (40)
            2       1     uint8    pkt_type  1 (PKT_TYPE_LTP)
            3       1     uint8    exch_seg  Exchange segment
            4       4     int32    sym_id    Symbol/Token ID
            8       4     int32    ltp       Last traded price (in paise)
            12      4     int32    vwap      Volume-weighted average price
            16      8     int64    volume    Traded volume (units)
            24      8     uint64   ltt       Last traded time (seconds)
            32      4     uint32   atv       Ask Traded Volume
            36      4     uint32   btv       Buy Traded Volume
        """
        try:
            tick = {
                'size': struct.unpack('<h', data[0:2])[0],
                'pkt_type': data[2],
                'exch_seg': data[3],
                'token': struct.unpack('<i', data[4:8])[0],
                'ltp': struct.unpack('<i', data[8:12])[0],
                'vwap': struct.unpack('<i', data[12:16])[0],
                'volume': struct.unpack('<q', data[16:24])[0],
                'ltt': struct.unpack('<Q', data[24:32])[0],
                'atv': struct.unpack('<I', data[32:36])[0],
                'btv': struct.unpack('<I', data[36:40])[0]
            }
            return tick
        except Exception as e:
            logger.error(f"Error parsing LTP packet: {e}")
            return None

    def _parse_full_packet(self, data: bytes) -> Optional[Dict]:
        """Parse Full market depth packet (192 bytes).

        Full Packet Structure:
            Offset  Size  Type         Field        Description
            0       2     int16        size         Packet size in bytes (192)
            2       1     uint8        pkt_type     2 (PKT_TYPE_FULL)
            3       1     uint8        exch_seg     Exchange segment
            4       4     int32        token        Symbol/Token ID
            8       4     int32        ltp          Last traded price (in paise)
            12      4     int32        ltq          Last traded quantity
            16      4     int32        vwap         Volume-weighted average price
            20      4     int32        open         Open price
            24      4     int32        high         High price
            28      4     int32        close        Close price
            32      4     int32        low          Low price
            36      4     int32        ltt          Last traded time (seconds)
            40      4     int32        dpr_l        Day price range low
            44      4     int32        dpr_h        Day price range high
            48      8     int64        tbq          Total buy quantity
            56      8     int64        tsq          Total sell quantity
            64      8     int64        volume       Total volume
            72      20    int32[5]     bid_px       Best 5 bid prices
            92      20    int32[5]     ask_px       Best 5 ask prices
            112     20    int32[5]     bid_size     Best 5 bid quantities
            132     20    int32[5]     ask_size     Best 5 ask quantities
            152     10    uint16[5]    bid_ord      Bid order counts (levels 1-5)
            162     10    uint16[5]    ask_ord      Ask order counts (levels 1-5)
            172     4     int32        oi           Open interest
            176     8     uint64       ts           Server timestamp (epoch ns)
            184     4     uint32       atv          Ask Traded Volume
            188     4     uint32       btv          Buy Traded Volume
        """
        try:
            tick = {
                'size': struct.unpack('<h', data[0:2])[0],
                'pkt_type': data[2],
                'exch_seg': data[3],
                'token': struct.unpack('<i', data[4:8])[0],
                'ltp': struct.unpack('<i', data[8:12])[0],
                'ltq': struct.unpack('<i', data[12:16])[0],
                'vwap': struct.unpack('<i', data[16:20])[0],
                'open': struct.unpack('<i', data[20:24])[0],
                'high': struct.unpack('<i', data[24:28])[0],
                'close': struct.unpack('<i', data[28:32])[0],
                'low': struct.unpack('<i', data[32:36])[0],
                'ltt': struct.unpack('<i', data[36:40])[0],
                'dpr_l': struct.unpack('<i', data[40:44])[0],
                'dpr_h': struct.unpack('<i', data[44:48])[0],
                'tbq': struct.unpack('<q', data[48:56])[0],
                'tsq': struct.unpack('<q', data[56:64])[0],
                'volume': struct.unpack('<q', data[64:72])[0],
                'bid_px': list(struct.unpack('<5i', data[72:92])),
                'ask_px': list(struct.unpack('<5i', data[92:112])),
                'bid_size': list(struct.unpack('<5i', data[112:132])),
                'ask_size': list(struct.unpack('<5i', data[132:152])),
                'bid_ord': list(struct.unpack('<5H', data[152:162])),
                'ask_ord': list(struct.unpack('<5H', data[162:172])),
                'oi': struct.unpack('<i', data[172:176])[0],
                'ts': struct.unpack('<Q', data[176:184])[0],
                'atv': struct.unpack('<I', data[184:188])[0],
                'btv': struct.unpack('<I', data[188:192])[0]
            }
            return tick
        except Exception as e:
            logger.error(f"Error parsing Full packet: {e}")
            return None


class ArrowStreams:
    """Main client class providing order, data, and HFT streams.

    Example usage:
        # Initialize the client
        client = ArrowStreams(appID="your_app_id", token="your_token", debug=True)

        # Set up event handlers
        client.hft_data_stream.on_ltp_tick = lambda tick: print(f"LTP: {tick}")
        client.hft_data_stream.on_full_tick = lambda tick: print(f"Full: {tick}")
        client.hft_data_stream.on_response = lambda resp: print(f"Response: {resp}")

        # Connect to HFT data stream
        client.connect_hft_data_stream()

        # Subscribe to symbols
        client.subscribe_hft_data('ltpc', ['NSE.SBIN-EQ', 'BSE.RELIANCE'], latency=100)

        # Or subscribe with explicit exchange segments
        client.hft_data_stream.subscribe_by_segment('full', {
            HFTDataStream.EXCH_NSE_FO: [5042, 4449],
            HFTDataStream.EXCH_BSE_CM: [100, 200]
        }, latency=200)
    """

    def __init__(self, appID: str, token: str, debug: bool = False):
        self.config = ConnectionConfig(appID=appID, token=token, debug=debug)

        # Initialize streams
        self.order_stream = OrderStream(self.config)
        self.data_stream = DataStream(self.config)
        self.hft_data_stream = HFTDataStream(self.config)

        # Status tracking
        self.status = {
            'order_stream': SocketStatus.DISCONNECTED,
            'data_stream': SocketStatus.DISCONNECTED,
            'hft_data_stream': SocketStatus.DISCONNECTED
        }

        # Set up event handlers for status tracking
        self._setup_status_handlers()

    def connect_order_stream(self):
        """Connect to order updates stream"""
        self.order_stream.connect()

    def connect_data_stream(self):
        """Connect to market data stream"""
        self.data_stream.connect()

    def connect_hft_data_stream(self):
        """Connect to HFT market data stream"""
        self.hft_data_stream.connect()

    def connect_all(self):
        """Connect to all streams"""
        self.connect_order_stream()
        self.connect_data_stream()
        self.connect_hft_data_stream()

    def disconnect_all(self):
        """Disconnect from all streams"""
        self.order_stream.disconnect()
        self.data_stream.disconnect()
        self.hft_data_stream.disconnect()

    def subscribe_market_data(self, mode: DataMode, tokens: List[int]):
        """Subscribe to market data (DataStream)"""
        self.data_stream.subscribe(mode, tokens)

    def unsubscribe_market_data(self, mode: DataMode, tokens: List[int]):
        """Unsubscribe from market data (DataStream)"""
        self.data_stream.unsubscribe(mode, tokens)

    def subscribe_hft_data(self, mode: str, symbols: List[Union[str, int]], latency: int = 1000):
        """Subscribe to HFT market data (HFTDataStream).

        Args:
            mode: Data mode - 'ltpc' or 'l' for LTP, 'full' or 'f' for full market depth
            symbols: List of symbol names (strings) or token IDs (integers)
            latency: Time interval between ticks in milliseconds (50-60000, default 1000)
        """
        self.hft_data_stream.subscribe(mode, symbols, latency)

    def unsubscribe_hft_data(self, mode: str, symbols: List[Union[str, int]]):
        """Unsubscribe from HFT market data (HFTDataStream)"""
        self.hft_data_stream.unsubscribe(mode, symbols)

    def get_status(self) -> Dict[str, str]:
        """Get connection status for all streams"""
        return {
            'order_stream': self.status['order_stream'].value,
            'data_stream': self.status['data_stream'].value,
            'hft_data_stream': self.status['hft_data_stream'].value
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

        # HFT data stream handlers
        self.hft_data_stream.on_connect = lambda: self._update_status('hft_data_stream', SocketStatus.CONNECTED)
        self.hft_data_stream.on_disconnect = lambda: self._update_status('hft_data_stream', SocketStatus.CONNECTING)
        self.hft_data_stream.on_reconnect = lambda *args: self._update_status('hft_data_stream',
                                                                              SocketStatus.CONNECTING)

    def _update_status(self, stream: str, status: SocketStatus):
        """Update stream status"""
        self.status[stream] = status
        if self.config.debug:
            logger.debug(f"{stream} status: {status.value}")