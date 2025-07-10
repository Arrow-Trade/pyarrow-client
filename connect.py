import datetime
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse, parse_qs

import pyotp

from pyarrow.__version__ import __title__, __version__
from pyarrow.constants import Exchange, OrderType, ProductType, Retention, TransactionType, Variety

import dateutil.parser
import requests
import urllib3

import pyarrow.constants as constants

log = logging.getLogger(__name__)

class ArrowClient(object):
    DEFAULT_TIMEOUT = 10
    DEFAULT_ROOT_URL = "https://api.arrow.trade"
    DEFAULT_LOGIN_URL = "https://app.arrow.trade/auth/app/login"
    VALIDATE_2FA_URL = "https://api.arrow.trade/auth/validate-2fa"

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

    # Order Routes
    def get_order(self, order_id: str) -> List[Dict[str, Any]]:
        data = self._get(self._routes.GET_ORDER_BY_ID, url_args={"orderId": order_id})
        return self._format_order_response(data)

    def get_orders(self) -> List[Dict[str, Any]]:
        """Get all user orders."""
        data = self._get(self._routes.GET_USER_ORDERS)
        return self._format_orders_response(data)

    def get_trades(self) -> List[Dict[str, Any]]:
        """Get all user trades."""
        data = self._get(self._routes.GET_USER_TRADES)
        return self._format_trades_response(data)

    def modify_order(
            self,
            order_id: str,
            exchange: Exchange,
            token: str,
            quantity: int,
            price: float,
            disclosed_qty: int,
            product: ProductType,
            transaction_type: TransactionType,
            order_type: OrderType,
            validity: Retention,
            amo: bool = False,
            trigger_price: Optional[float] = None,
            tags: Optional[str] = None,
            book_loss_price: Optional[float] = None,
            book_profit_price: Optional[float] = None
    ) -> str:
        """Modify an existing order."""
        params = {
            "exchange": str(exchange),
            "token": token,
            "quantity": str(quantity),
            "disclosedQty": str(disclosed_qty),
            "product": str(product),
            "transactionType": str(transaction_type),
            "order": str(order_type),
            "price": str(price),
            "validity": str(validity),
            "triggerPrice": str(trigger_price or "0"),
            "bookLossPrice": str(book_loss_price or ""),
            "bookProfitPrice": str(book_profit_price or ""),
            "tags": tags or "",
            "amo": amo
        }

        response = self._patch(
            self._routes.UPDATE_ORDER_BY_ID,
            url_args={"order_id": order_id},
            params=params
        )
        return response["message"]

    def cancel_order(self, order_id: str) -> str:
        """Cancel an existing order."""
        response = self._delete(
            self._routes.DELETE_ORDER,
            url_args={"order_id": order_id}
        )
        return response["message"]

    # Margin Routes
    def get_order_margin(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._post(self._routes.ORDER_MARGIN, params)

    def get_basket_margin(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._post(self._routes.BASKET_MARGIN, params=orders)


    def _authenticate(self, checksum: str, request_token: str) -> Dict[str, str]:
        response = self._post(
            self._routes.AUTHENTICATE_TOKEN, {
                "appId": self.app_id,
                "token": request_token,
                "checkSum": checksum,
            }
        )

        if "token" in response:
            self._token = response["token"]
            if self.debug:
                log.debug(f"Token: {self._token}")

        return response


    def login(self, request_token: str, api_secret: str) -> Dict[str, str]:
        checksum = self._generate_checksum(request_token, api_secret)
        response = self._authenticate(checksum, request_token)
        return response

    def auto_login(self, user_id: str, password: str, api_secret: str, totp_secret: str) -> Dict[str, str]:
        login_url = self.DEFAULT_LOGIN_URL

        login_payload = {
            "userId": user_id,
            "password": password,
            "captchaValue": "",
            "captchaId": None,
            "appId": self.app_id,
            "isAppLogin": True
        }

        # Generate the request ID
        try:
            login_resp = self._post(login_url, params=login_payload)
            request_id = login_resp["data"]["requestId"]
        except Exception as e:
            log.error("Failed to generate Request id: {}".format(e))
            raise

        # Generate the totp
        try:
            passcode = pyotp.TOTP(totp_secret).now()
        except Exception as e:
            log.error("Failed to Generate TOTP: {}".format(e))
            raise

        # Validate 2FA
        totp_payload = {
            "code": request_id,
            "requestId": request_id,
            "userId": user_id,
        }

        try:
            totp_resp = self._post(self.VALIDATE_2FA_URL, params=totp_payload)
            redirect_url = totp_resp["data"]["redirectUrl"]
        except Exception as e:
            log.error("Failed to Generate 2FA URL: {}".format(e))
            raise

        try:
            parsed_url = urlparse(redirect_url)
            request_token = parse_qs(parsed_url.query)["request-token"][0]
        except Exception as e:
            log.error("Failed to generate request token: {}".format(e))
            raise

        try:
            response = self.login(request_token=request_token, api_secret=api_secret)
            return response
        except Exception as e:
            log.error("Failed to generate 2FA URL: {}".format(e))
            raise



    def _generate_checksum(self, request_token: str, api_secret: str) -> str:
        input_str = f"{self.app_id}:{api_secret}:{request_token}"
        return hashlib.sha256(input_str.encode("utf-8")).hexdigest()


    # HTTP Route Methods
    def _get(self, route: str, url_args: Optional[Dict[str, str]] = None, params: Any = None) -> Any:
        return self._request("GET", route, url_args, params)

    def _post(self, route: str, url_args: Optional[Dict[str, str]] = None, params: Any = None) -> Any:
        return self._request("POST", route, url_args, params)

    def _patch(self, route: str, url_args: Optional[Dict[str, str]] = None, params: Any = None) -> Any:
        return self._request("PATCH", route, url_args, params)

    def _delete(self, route: str, url_args: Optional[Dict[str, str]] = None, params: Any = None) -> Any:
        return self._request("DELETE", route, url_args, params)


    def _request(self, method: str, route: str, url_args: Optional[Dict[str, str]] = None, params: Any = None):
        url = route.format(**url_args) if url_args else route

        headers = {
            "User-agent": f"{__title__}-pythin/{__version__}",
            "appId": self.app_id
        }

        if self._token:
            headers["token"] = self._token

        if self.debug:
            log.debug(f"Request: {method} {url} {json.dumps(params)} {json.dumps(headers)}")

    # Data Parsing Methods
    def _format_order_response(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Format order response data."""
        order_list = [data] if isinstance(data, dict) else data
        return self._format_datetime_fields(self, order_list, ["timeStamp", "exchangeUpdateTime", "requestTime"])

    def _format_orders_response(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format orders response data."""
        return self._format_datetime_fields(self, data, ["timeStamp", "exchangeUpdateTime"])


    def _format_trades_response(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format trades response data."""
        return self._format_datetime_fields(self, data, ["fillTime", "timeStamp", "exchangeUpdateTime", "requestTime"])

    @staticmethod
    def _format_datetime_fields(self, data: List[Dict[str, Any]], datetime_fields: List[str]) -> List[Dict[str, Any]]:
        """Convert datetime strings and epoch times in response data."""
        for item in data:
            # Convert datetime strings
            for field in datetime_fields:
                if item.get(field) and len(str(item[field])) == 19:
                    item[field] = dateutil.parser.parse(item[field])

            # Convert epoch time to int
            if item.get("orderTime"):
                item["orderTime"] = int(item["orderTime"])

        return data

    def get_holidays(self) -> Dict[str, Any]:
        return self._get(self._routes.HOLIDAYS_LIST)

    def get_index_list(self) -> List[Dict[str, Any]]:
        return self._get(self._routes.INDEX_LIST)

    #Properties
    @property
    def token(self) ->str:
        return self._token or ""

Arrow = ArrowClient
