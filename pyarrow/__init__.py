# Import version metadata
from pyarrow.__version__ import (
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
from pyarrow.connect import ArrowClient

# Import streaming classes
from pyarrow.sockets import ArrowStreams, DataMode, OrderStream, DataStream

# Import enums and constants
from pyarrow.constants import (
    Exchange,
    OrderType,
    ProductType,
    Retention,
    TransactionType,
    Variety,
)

# Define what's available when someone does "from pyarrow import *"
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