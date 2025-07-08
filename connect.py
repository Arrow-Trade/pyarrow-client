import datetime
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Union
from pyarrow.__version__ import __title__, __version__
from pyarrow.constants import Exchange, OrderType, ProductType, Retention, TransactionType, Variety

import dateutil.parser
import requests
import urllib3

import pyarrow.constants as constants

class ArrowClient(object):
    DEFAULT_TIMEOUT = 10
    DEFAULT_ROOT_URL = "https://api.arrow.trade"


    def __init__(
            self, app_id: str,
            timeout: Optional[int] = None,
            debug: bool = False,
            root_url: Optional[str] = None,
            pool_config: Optional[Dict[str, Any]] = None) -> None:
        self.app_id = app_id
        self.timeout = timeout
        self.debug = debug
        self.root_url = root_url or self.DEFAULT_ROOT_URL
        self.disable_ssl = False
        self.proxies: Dict[str, str] = {}

        self._token: Optional[str] = None
        self._routes = constants.Routes(root_url=self.root_url)

    def place_order(self, exchange: Exchange, symbol: str, token: str, quantity: int, price: float):
        pass

    def set_token(self, token: str) -> None:
        self._token = token

    def get_token(self) -> str:
        return self._token or ""

    def invalidate_session(self) -> None:
        self._token = None

    def get_instruments(self) -> List[Dict[str, Any]]:
        data = self._get(self._routes.ALL_INSTRUMENTS)

    def _get(self, route: str, url_args: Optional[Dict[str, str]] = None, params: Any = None) -> Any:
        return self._request("GET", route, url_args, params)

    def _request(self, method: str, route: str, url_args: Optional[Dict[str, str]] = None, params: Any = None):
        url = route.format(**url_args) if url_args else route

        headers = {
            "User-agent": f"{__title__}-pythin/{__version__}",
            "appId": self.app_id
        }

        if self._token:
            headers["token"] = self._token
