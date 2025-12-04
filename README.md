# PyArrow – Official Python Client for Arrow Trading API

[![PyPI version](https://badge.fury.io/py/pyarrow-client.svg)](https://badge.fury.io/py/pyarrow-client)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/pyarrow-client.svg)](https://pypi.org/project/pyarrow-client/)
[![Downloads](https://pepy.tech/badge/pyarrow-client)](https://pepy.tech/project/pyarrow-client)

**PyArrow** is the official Python SDK for the Arrow Trading Platform, providing comprehensive access to trading APIs, real-time market data, and order management capabilities. Built for traders, quants, and fintech developers who need reliable, high-performance access to Indian financial markets.

## 🚀 Key Features

### 📊 **Market Data & Analytics**
- Real-time quotes, OHLC, LTP, and market depth
- Historical candle data retrieval
- Option chain data and expiry information
- Market holidays and trading calendars
- Index listings and sector data

### 💼 **Order Management**
- Place, modify, and cancel orders across exchanges
- Support for all order types (Market, Limit, SL, SL-M)
- Bulk cancel all orders functionality
- Real-time order status tracking
- Trade book and order book access

### 📡 **Real-time Streaming**
- WebSocket-based live market data feeds
- Order and position update streams
- Multiple subscription modes (LTPC, Quote, Full)
- Automatic reconnection with exponential backoff
- Thread-safe event handling

### 🔐 **Authentication & Security**
- OAuth-based authentication flow
- TOTP (Time-based OTP) integration
- Automatic session management
- Token refresh and validation

---

## 📦 Installation

```bash
pip install pyarrow-client
```

**Requirements:**
- Python 3.7+
- `requests`, `websocket-client`, `pyotp`, `pyarrow`, `dateutil`

---

## 🏃‍♂️ Quick Start

### Authentication

```python
from pyarrow import ArrowClient

# Initialize client
client = ArrowClient(app_id="your_app_id")

# Method 1: Manual login (web-based)
login_url = client.login_url()
print(f"Visit: {login_url}")
# After authorization, get request_token from callback
client.login(request_token="token_from_callback", api_secret="your_secret")

# Method 2: Automated login
client.auto_login(
    user_id="your_user_id",
    password="your_password", 
    api_secret="your_api_secret",
    totp_secret="REDACTED"
)
```

### Basic Trading Operations

```python
from pyarrow import Exchange, OrderType, ProductType, TransactionType, Variety, Retention

# Place a buy order
order_id = client.place_order(
    exchange=Exchange.NSE,
    symbol="RELIANCE-EQ",
    quantity=1,
    disclosed_quantity=0,
    product=ProductType.CNC,
    order_type=OrderType.LIMIT,
    variety=Variety.REGULAR,
    transaction_type=TransactionType.BUY,
    price=1450.0,
    validity=Retention.DAY
)

print(f"Order placed: {order_id}")

# Get order book
orders = client.get_order_book()
for order in orders:
    print(f"Order {order['id']}: {order['orderStatus']}")

# Get specific order details
order_details = client.get_order_details(order_id)
print(f"Order details: {order_details}")

# Get trade book
trades = client.get_trade_book()
print(f"Trades: {trades}")

# Get positions
positions = client.get_positions()
print(f"Positions: {positions}")

# Get user holdings
holdings = client.get_holdings()
print(f"Current holdings: {holdings}")
```

---

## 📡 Real-time Market Data

### WebSocket Streaming

```python
# from pyarrow import ArrowClient
# from pyarrow.sockets import ArrowStreams
# from pyarrow import Exchange, ProductType, OrderType, Variety, TransactionType, Retention
# # Initialize client
# client = ArrowClient(app_id="REDACTED")
#
# # # Method 1: Manual login (web-based)
# # login_url = client.login_url()
# # print(f"Visit: {login_url}")
# # # After authorization, get request_token from callback
# # client.login(request_token="token_from_callback", api_secret="your_secret")
#
# # Method 2: Automated login
# # client.auto_login(
# #     user_id="REDACTED",
# #     password="REDACTED",
# #     api_secret="REDACTED",
# #     totp_secret="REDACTED"
# # )
#
# client.set_token("REDACTED_JWT")
# order_id = client.place_order(
#     exchange=Exchange.NSE,
#     symbol="RELIANCE-EQ",
#     quantity=1,
#     disclosed_quantity=0,
#     product=ProductType.CNC,
#     order_type=OrderType.LIMIT,
#     variety=Variety.REGULAR,
#     transaction_type=TransactionType.BUY,
#     price=1450.0,
#     validity=Retention.DAY
# )
#
# print(order_id)
#
# orders = client.get_order_book()
# for order in orders:
#     print(f"Order {order['id']}: {order['orderStatus']}")
#
# # Get specific order details
# order_details = client.get_order_details(order_id)
# print(f"Order details: {order_details}")
#
# # Get trade book
# trades = client.get_trade_book()
# print(f"Trades: {trades}")
#
# # Get positions
# positions = client.get_positions()
# print(f"Positions: {positions}")
#
# # Get user holdings
# holdings = client.get_holdings()
# print(f"Current holdings: {holdings}")


from pyarrow import ArrowStreams, DataMode

# Initialize streams
streams = ArrowStreams(
    appID="your_app_id",
    token="your_access_token",
    debug=True
)

# Set up event handlers
def on_tick(tick):
    print(f"Token: {tick.token} LTP: {tick.ltp} Change: {tick.net_change}%")

def on_order_update(order):
    print(f"Order Update: {order}")

def on_connect():
    print("Connected to data stream")

def on_disconnect():
    print("Disconnected from data stream")

# Connect handlers
streams.data_stream.on_ticks = on_tick
streams.data_stream.on_connect = on_connect
streams.data_stream.on_disconnect = on_disconnect

streams.order_stream.on_order_update = on_order_update

# Connect to streams
streams.connect_all()

# Subscribe to market data
token_list = [3045, 1594]  # NSE tokens for RELIANCE, INFY
streams.subscribe_market_data(DataMode.QUOTE, token_list)

# Keep connection alive
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    streams.disconnect_all()
```

### Market Data Modes

```python
# LTPC Mode - Last Trade Price & Change (17 bytes)
# Includes: token, ltp, close, net_change, change_flag
streams.subscribe_market_data(DataMode.LTPC, [3045])

# Quote Mode - Detailed quotes (93 bytes)
# Includes: LTPC + volume, OHLC, OI, buy/sell quantities, timestamps
streams.subscribe_market_data(DataMode.QUOTE, [3045])

# Full Mode - Complete market depth (241 bytes)
# Includes: Quote + upper/lower limits, 5 levels of bids/asks
streams.subscribe_market_data(DataMode.FULL, [3045])

# Unsubscribe from tokens
streams.unsubscribe_market_data(DataMode.LTPC, [3045])
```

### Market Tick Data Structure

```python
# MarketTick attributes
tick.token           # Instrument token
tick.ltp             # Last traded price
tick.mode            # Data mode (ltpc/quote/full)

# Price data
tick.open            # Open price
tick.high            # High price
tick.low             # Low price
tick.close           # Close price
tick.volume          # Volume

# Change calculations
tick.net_change      # Percentage change
tick.change_flag     # 43(+), 45(-), 32(no change)

# Quote data
tick.ltq             # Last traded quantity
tick.avg_price       # Average price
tick.total_buy_quantity
tick.total_sell_quantity

# Time and OI
tick.ltt             # Last trade time
tick.time            # Timestamp
tick.oi              # Open interest
tick.oi_day_high     # OI day high
tick.oi_day_low      # OI day low

# Limits and depth (Full mode only)
tick.upper_limit
tick.lower_limit
tick.bids            # List of 5 bid levels
tick.asks            # List of 5 ask levels
```

---

## 💹 Advanced Trading Features

### Order Modification

```python
# Modify existing order
message = client.modify_order(
    order_id=order_id,
    exchange=Exchange.NSE,
    quantity=2,  # Changed quantity
    symbol="RELIANCE",
    price=1500.0,  # New price
    disclosed_qty=0,
    product=ProductType.CNC,
    transaction_type=TransactionType.BUY,
    order_type=OrderType.LIMIT,
    validity=Retention.DAY,
    remarks="Modified order"
)
print(message)
```

### Cancel Orders

```python
# Cancel single order
message = client.cancel_order(order_id="order_id_here")
print(message)

# Cancel all open orders (bulk cancel with threading)
results = client.cancel_all_orders()
for order_id, status, result in results:
    print(f"Order {order_id}: {status} - {result}")
```

### Margin Calculation

```python
# Calculate margin for single order
margin_info = client.order_margin(
    exchange=Exchange.NSE,
    symbol="RELIANCE-EQ",
    quantity=100,
    product=ProductType.CNC,
    order_type=OrderType.LIMIT,
    transaction_type=TransactionType.BUY,
    price=1500.0,
    include_positions=False
)
print(f"Required margin: {margin_info}")

# Calculate basket margin for multiple orders
orders = [
    {
        "exchange": "NSE",
        "symbol": "RELIANCE-EQ",
        "quantity": "100",
        "product": ProductType.CNC,
        "order": OrderType.LIMIT,
        "transactionType": TransactionType.BUY,
        "price": "1500.00",
    },
    {
        "exchange": "NSE",
        "symbol": "INFY-EQ",
        "quantity": "50",
        "product": ProductType.CNC,
        "order": OrderType.LIMIT,
        "transactionType": TransactionType.BUY,
        "price": "1500.00",
    }
]
basket_margin = client.basket_margin(orders, include_positions=False)
print(f"Basket margin: {basket_margin}")
```

---

## 📊 Market Data & Analytics

### Historical Candle Data

```python
from pyarrow.constants import Exchange

# Get historical candle data
candles = client.candle_data(
    exchange=Exchange.NSE,
    token="3045",  # RELIANCE token
    interval="5minute",  # Options: 1minute, 3minute, 5minute, 15minute, 30minute, 1hour, 1day
    from_timestamp="2024-01-01T09:15:00",
    to_timestamp="2024-01-01T15:30:00",
    oi=False  # Set to True for OI data
)
print(f"Candle data: {candles}")
```

### Instruments & Market Info

```python
# Get all tradable instruments
instruments = client.get_instruments()

# Get option chain symbols
option_symbols = client.get_option_chain_symbols()

# Get option chain data (method signature exists but not implemented)
# option_chain = client.get_option_chain(params)

# Get market holidays
holidays = client.get_holidays()

# Get index listings
indices = client.get_index_list()

# Get user limits (margin, available funds)
limits = client.get_user_limits()

# Get user details
user_details = client.get_user_details()
```

### Expiry Information

```python
from pyarrow import ArrowClient

# Get expiry dates for instruments
nifty_expiries = ArrowClient.get_expiry_dates("NIFTY", "2024")
print(f"NIFTY expiries: {nifty_expiries}")

banknifty_expiries = ArrowClient.get_expiry_dates("BANKNIFTY", "2024")
print(f"BANKNIFTY expiries: {banknifty_expiries}")
```

---

## 🔧 Configuration & Error Handling

### Client Configuration

```python
client = ArrowClient(
    app_id="your_app_id",
    timeout=10,  # Request timeout in seconds (default: 10)
    debug=True,  # Enable debug logging
    root_url="https://edge.arrow.trade",  # Custom API endpoint (default)
    pool_config=None  # Connection pool configuration (optional)
)

# Configure proxy
client.proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080'
}

# Disable SSL verification (not recommended for production)
client.disable_ssl = True
```

### WebSocket Configuration

```python
from pyarrow.streams import ConnectionConfig, ArrowStreams

# Create custom configuration
config = ConnectionConfig(
    appID="your_app_id",
    token="your_token",
    debug=True,
    
    # Reconnection settings
    enable_reconnect=True,
    max_reconnect_attempts=300,
    max_reconnect_delay=5,  # Maximum delay between reconnection attempts (seconds)
    immediate_reconnect_attempts=3,  # First 3 attempts are immediate
    
    # Connection timeouts
    read_timeout=5,  # Read timeout (seconds)
    ping_interval=3  # Ping interval (seconds)
)

# Initialize streams with custom config
streams = ArrowStreams(
    appID=config.appID,
    token=config.token,
    debug=config.debug
)
```

### WebSocket Event Handlers

```python
# Data stream event handlers
streams.data_stream.on_connect = lambda: print("Data stream connected")
streams.data_stream.on_disconnect = lambda: print("Data stream disconnected")
streams.data_stream.on_error = lambda error: print(f"Data stream error: {error}")
streams.data_stream.on_close = lambda code, msg: print(f"Data stream closed: {code} - {msg}")
streams.data_stream.on_reconnect = lambda attempt, delay: print(f"Reconnecting (attempt {attempt}) in {delay}s")
streams.data_stream.on_no_reconnect = lambda: print("Max reconnection attempts exhausted")

# Order stream event handlers
streams.order_stream.on_connect = lambda: print("Order stream connected")
streams.order_stream.on_disconnect = lambda: print("Order stream disconnected")
streams.order_stream.on_error = lambda error: print(f"Order stream error: {error}")

# Check connection status
status = streams.get_status()
print(f"Data stream: {status['data_stream']}")
print(f"Order stream: {status['order_stream']}")

# Check if connected
if streams.data_stream.connected():
    print("Data stream is connected")
```

### Error Handling

```python
import pyarrow.exceptions as ex

try:
    order_id = client.place_order(
        exchange=Exchange.NSE,
        symbol="RELIANCE",
        quantity=10,
        disclosed_quantity=0,
        product=ProductType.DELIVERY,
        order_type=OrderType.MARKET,
        variety=Variety.NORMAL,
        transaction_type=TransactionType.BUY,
        price=0.0,
        validity=Retention.DAY
    )
except ex.DataException as e:
    print(f"Data error: {e}")
except ex.GeneralException as e:
    print(f"General error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## 📈 Sample Trading Strategy

```python
import time
from pyarrow import ArrowClient
from pyarrow.streams import ArrowStreams, DataMode
from pyarrow.constants import *

class SimpleStrategy:
    def __init__(self, app_id, token):
        self.client = ArrowClient(app_id)
        self.client.set_token(token)
        
        self.streams = ArrowStreams(app_id, token, debug=True)
        self.streams.data_stream.on_ticks = self.on_market_tick
        self.streams.data_stream.on_connect = self.on_connect
        
        self.position = 0
        self.target_symbol = "RELIANCE"
        self.target_token = 3045
        
    def on_connect(self):
        print("Connected! Subscribing to market data...")
        self.streams.subscribe_market_data(DataMode.QUOTE, [self.target_token])
        
    def start(self):
        # Connect to real-time feeds
        self.streams.connect_data_stream()
        print("Strategy started. Monitoring market data...")
        
    def on_market_tick(self, tick):
        if tick.token == self.target_token:
            print(f"Tick: {tick.token} LTP: {tick.ltp} Change: {tick.net_change}% Volume: {tick.volume}")
            
            # Simple momentum strategy
            if tick.net_change > 2.0 and self.position == 0:
                self.buy_signal(tick)
            elif tick.net_change < -1.0 and self.position > 0:
                self.sell_signal(tick)
                
    def buy_signal(self, tick):
        try:
            order_id = self.client.place_order(
                exchange=Exchange.NSE,
                symbol=self.target_symbol,
                quantity=10,
                disclosed_quantity=0,
                product=ProductType.INTRADAY,
                order_type=OrderType.MARKET,
                variety=Variety.NORMAL,
                transaction_type=TransactionType.BUY,
                price=0.0,
                validity=Retention.DAY
            )
            self.position = 10
            print(f"BUY order placed: {order_id} at LTP: {tick.ltp}")
        except Exception as e:
            print(f"Buy order failed: {e}")
            
    def sell_signal(self, tick):
        try:
            order_id = self.client.place_order(
                exchange=Exchange.NSE,
                symbol=self.target_symbol,
                quantity=self.position,
                disclosed_quantity=0,
                product=ProductType.INTRADAY,
                order_type=OrderType.MARKET,
                variety=Variety.NORMAL,
                transaction_type=TransactionType.SELL,
                price=0.0,
                validity=Retention.DAY
            )
            self.position = 0
            print(f"SELL order placed: {order_id} at LTP: {tick.ltp}")
        except Exception as e:
            print(f"Sell order failed: {e}")

# Usage
if __name__ == "__main__":
    strategy = SimpleStrategy("your_app_id", "your_token")
    strategy.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Strategy stopped")
        strategy.streams.disconnect_all()
```

---

## 🔍 API Reference

### ArrowClient Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `login(request_token, api_secret)` | Authenticate using request token | `Dict[str, str]` |
| `auto_login(user_id, password, api_secret, totp_secret)` | Automated login with credentials | `Dict[str, str]` |
| `login_url()` | Get login URL for manual authentication | `str` |
| `set_token(token)` | Set access token manually | `None` |
| `get_token()` | Get current access token | `str` |
| `invalidate_session()` | Clear current session token | `None` |
| `place_order(**params)` | Place new order | `str` (order_id) |
| `modify_order(order_id, **params)` | Modify existing order | `str` (message) |
| `cancel_order(order_id)` | Cancel single order | `str` (message) |
| `cancel_all_orders()` | Cancel all open/pending orders | `List[Tuple]` |
| `get_order_details(order_id)` | Get specific order details | `List[Dict]` |
| `get_order_book()` | Get all user orders | `List[Dict]` |
| `get_trade_book()` | Get all user trades | `List[Dict]` |
| `get_positions()` | Get user positions | `List[Dict]` |
| `get_holdings()` | Get user holdings | `Dict` |
| `get_user_details()` | Get user profile | `Dict` |
| `get_user_limits()` | Get user margin limits | `List[Dict]` |
| `order_margin(**params)` | Calculate single order margin | `Dict` |
| `basket_margin(orders, include_positions)` | Calculate basket margin | `Dict` |
| `candle_data(**params)` | Get historical candle data | `Dict` |
| `get_instruments()` | Get all tradable instruments | `Any` |
| `get_holidays()` | Get market holidays | `Dict` |
| `get_index_list()` | Get index listings | `List[Dict]` |
| `get_option_chain_symbols()` | Get option chain symbols | `Any` |
| `get_expiry_dates(symbol, year)` | Get expiry dates (static method) | `Any` |

### ArrowStreams Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `connect_order_stream()` | Connect to order updates | `None` |
| `connect_data_stream()` | Connect to market data | `None` |
| `connect_all()` | Connect to both streams | `None` |
| `disconnect_all()` | Disconnect from both streams | `None` |
| `subscribe_market_data(mode, tokens)` | Subscribe to market data | `None` |
| `unsubscribe_market_data(mode, tokens)` | Unsubscribe from market data | `None` |
| `get_status()` | Get connection status | `Dict[str, str]` |

### WebSocket Events

| Event | Trigger | Parameters |
|-------|---------|------------|
| `on_connect` | Connection established | `None` |
| `on_disconnect` | Connection lost | `None` |
| `on_ticks` | Market data received | `MarketTick` |
| `on_order_update` | Order status changed | `Dict` |
| `on_error` | Error occurred | `error: Exception` |
| `on_close` | Connection closed | `close_status_code: int, close_msg: str` |
| `on_reconnect` | Reconnection attempt | `attempt: int, delay: int` |
| `on_no_reconnect` | Max reconnection attempts reached | `None` |

### Constants

```python
from pyarrow.constants import (
    Exchange,          # NSE, BSE, NFO, BFO, MCX, etc.
    OrderType,         # MARKET, LIMIT, SL, SLM
    ProductType,       # DELIVERY, INTRADAY, MTF, etc.
    TransactionType,   # BUY, SELL
    Variety,           # NORMAL, AMO, BRACKET, COVER
    Retention          # DAY, IOC, EOS
)
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/arrowtech/pyarrow-client-python.git
cd pyarrow-client-python
pip install -e .[dev]
pytest tests/
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **Documentation**: [https://docs.arrow.trade](https://docs.arrow.trade)
- **API Reference**: [https://api.arrow.trade/docs](https://api.arrow.trade/docs)
- **Issues**: [GitHub Issues](https://github.com/arrowtech/pyarrow-client-python/issues)
- **Support Email**: support@arrow.trade

---

## ⚠️ Disclaimer

This software is for educational and informational purposes only. Trading in financial markets involves substantial risk and may not be suitable for all investors. Past performance is not indicative of future results. Please trade responsibly and consult with financial advisors before making investment decisions.

---

## 🔄 Recent Changes

### Key Updates in Latest Version:
- Enhanced WebSocket reconnection logic with immediate reconnection for first 3 attempts
- Improved timeout configurations (reduced read_timeout to 5s, ping_interval to 3s)
- Added `cancel_all_orders()` method with multi-threaded bulk cancellation
- Better error handling and logging throughout
- MarketTick data structure now includes all fields from binary parsing
- Thread-safe WebSocket implementation with proper timer management

---

**Built with ❤️ by the Arrow Trading Team**