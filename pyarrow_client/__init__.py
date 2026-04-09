import logging

_library_logger = logging.getLogger(__name__)
_library_logger.addHandler(logging.NullHandler())


def enable_logging(level: int = logging.DEBUG, handler: logging.Handler | None = None) -> None:
    """Enable logging for the pyarrow_client library.

    By default the library is silent. Call this once at startup to surface
    library logs into your application.

    Args:
        level:   Logging level, e.g. logging.DEBUG, logging.INFO (default: DEBUG).
        handler: A logging.Handler to attach. Defaults to a StreamHandler
                 writing to stderr with a simple timestamp format.

    Example::

        import pyarrow_client
        pyarrow_client.enable_logging()                        # DEBUG to stderr
        pyarrow_client.enable_logging(logging.INFO)            # INFO+ to stderr
        pyarrow_client.enable_logging(handler=my_file_handler) # custom handler
    """
    if handler is None:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        )
    _library_logger.setLevel(level)
    _library_logger.addHandler(handler)

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
    'enable_logging',
]