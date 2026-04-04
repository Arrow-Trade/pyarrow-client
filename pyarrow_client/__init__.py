# Import version metadata
from pyarrow_client.__version__ import (
    __title__,
    __version__,
    __description__,
    __url__,
    __download_url__,
    __license__,
    __author__,
    __author_email__,
    __maintainer__,
    __maintainer_email__,
)

# Import main client class
from pyarrow_client.connect import ArrowClient

# Import streaming classes
from pyarrow_client.sockets import ArrowStreams, DataMode, OrderStream, DataStream

# Import enums and constants
from pyarrow_client.constants import (
    Exchange,
    OrderType,
    ProductType,
    Retention,
    TransactionType,
    Variety,
    QuoteMode
)

# Define what's available when someone does "from pyarrow_client import *"
__all__ = [
    'ArrowClient',
    'ArrowStreams',
    'DataMode',
    'OrderStream',
    'DataStream',
    'Exchange',
    'OrderType',
    'ProductType',
    'Retention',
    'TransactionType',
    'Variety',
    '__version__',
    '__title__',
    '__author__',
]