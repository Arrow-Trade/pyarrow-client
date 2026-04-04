from enum import Enum
from typing import Optional


# -------------------------
# Constants
# -------------------------
STATUS = "status"
ERROR_CODE = "errorCode"
ERROR_MESSAGE = "message"
ERROR = "error"


# -------------------------
# Base Enum with String Representation
# -------------------------
class BaseEnum(str, Enum):
    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


# -------------------------
# API Paths Enum
# -------------------------
class _PATHS(BaseEnum):
    """API endpoint paths."""

    # Authentication
    WEB_LOGIN_URL = ""
    AUTHENTICATE_TOKEN = "/auth/app/authenticate-token"

    # Market Data
    ALL_INSTRUMENTS = "/all"
    HOLIDAYS_LIST = "/info/holidays"
    INDEX_LIST = "/info/index-list"
    OPTION_CHAIN = "/info/option-chain"
    OPTION_CHAIN_SYMBOLS = "/info/option-chain-symbols/all"
    GREEKS = "/info/greeks"
    QUOTE_DATA = "/info/quote/{mode}"
    QUOTES_DATA = "/info/quotes/{mode}"
    GET_HISTORICAL_DATA = "/candle"

    # User Data
    USER_DETAILS = "/user/details"
    GET_USER_ORDERS = "/user/orders"
    GET_USER_TRADES = "/user/trades"
    GET_USER_LIMITS = "/user/limits"
    GET_USER_POSITIONS = "/user/positions"
    GET_USER_HOLDINGS = "/user/holdings"


    # Orders
    GET_ORDER_BY_ID = "/order/{order_id}"
    PLACE_ORDER = "/order/{variety}"
    UPDATE_ORDER_BY_ID = "/order/regular/{order_id}"
    DELETE_ORDER = "/order/regular/{order_id}"

    # Margin
    ORDER_MARGIN = "/margin/order"
    BASKET_MARGIN = "/margin/basket"


# -------------------------
# API Route Generator
# -------------------------
class Routes:
    """Helper class to construct API routes."""

    # _home_url: str = "https://app.arrow.trade/app/login"
    # _root_url: str = "https://api.arrow.trade"

    _home_url: str = "https://app.arrow.trade/app/login"
    _root_url: str = "https://edge.arrow.trade"
    _candle_url: str = "https://historical-api.arrow.trade"

    def __init__(self, root_url: Optional[str] = None) -> None:
        if root_url:
            self._root_url = root_url.strip()

    def get_home_url(self) -> str:
        return self._home_url

    def get_candle_url(self) -> str:
        return self._candle_url

    def __getattr__(self, name: str) -> str:
        if name in _PATHS.__members__:
            endpoint_path = _PATHS[name].value
            return f"{self._root_url}{endpoint_path}"
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


# -------------------------
# Trading Enums
# -------------------------
class Variety(BaseEnum):
    REGULAR = "regular"
    COVER = "cover"


class Exchange(BaseEnum):
    NSE = "NSE"
    NFO = "NFO"
    BSE = "BSE"
    BFO = "BFO"
    MCX = "MCX"
    INDEX = "INDEX"


class TransactionType(BaseEnum):
    BUY = "B"
    SELL = "S"


class OrderType(BaseEnum):
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP_LOSS_LIMIT = "SL-LMT"
    STOP_LOSS_MARKET = "SL-MKT"


class Retention(BaseEnum):
    DAY = "DAY"
    IOC = "IOC"

class QuoteMode(BaseEnum):
    FULL = "full"
    OHLCV = "ohlcv"
    LTP = "ltp"


class ProductType(BaseEnum):
    MIS = "I"
    CNC = "C"
    NRML = "M"