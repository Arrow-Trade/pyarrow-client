from enum import Enum

class BaseEnum(Enum):
    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

class ErrorCode(BaseEnum):
    BAD_REQUEST_ERROR = "BadRequestError"
    INTERNAL_SERVER_ERROR = "InternalServerError"
    NETWORK_ERROR = "NetworkError"
    NOT_FOUND_ERROR = "NotFoundError"
    SOMETHING_WENT_WRONG_ERROR = "SomethingWentWrongError"
    TOO_MANY_REQUESTS_ERROR = "TooManyRequestsError"
    INTERNAL_ERROR = "InternalError"

class Endpoints(BaseEnum):
    WEB_LOGIN_URL = ""
    AUTHENTICATE_TOKEN = "/auth/app/authenticate-token"

    ALL_INSTRUMENTS = "/all"
    HOLIDAYS_LIST = "/info/holidays"
    INDEX_LIST = "/info/index-list"
    OPTION_CHAIN = "info/option-chain"
    OPTION_CHAIN_SYMBOLS = "info/option-chain-symbols"
    GREEKS = "info/greeks"
    QUOTE_DATA = "info/quote/{mode}"
    QUOTES_DATA = "info/quotes/{mode}"
    GET_HISTORICAL_DATA = "candle/{exchange}/{token}/{interval}"

class Variety(BaseEnum):
    REGULAR = "regular"
    COVER = "cover"

class EXCHANGE(BaseEnum):
    NSE = "NSE"
    NFO = "NFO"
    BSE = "BSE"
    BFO = "BFO"
    MCX = "MCX"

class TransactionType(BaseEnum):
    BUY = "B"
    SELL = "S"

class OrderType(BaseEnum):
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP_LOSS_LIMIT = "SL-LMT"
    STOP_LOSS_MARKET = "SL-MKT"

class RetentionType(BaseEnum):
    DAY = "DAY"
    IOC = "IOC"
    MINUTES = "MINUTES"

class ProductType(BaseEnum):
    MIS = "I"
    CNC = "C"
    NRML = "M"


