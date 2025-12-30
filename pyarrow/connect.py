from datetime import datetime
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse, parse_qs
import pyarrow.exceptions as ex
import pyotp

from pyarrow.constants import QuoteMode
from pyarrow.arrow_utils import expiry_dates
from concurrent.futures import ThreadPoolExecutor, as_completed



from pyarrow.__version__ import __title__, __version__
from pyarrow.constants import Exchange, OrderType, ProductType, Retention, TransactionType, Variety

import dateutil.parser
import requests
import urllib3

import pyarrow.constants as constants

log = logging.getLogger(__name__)


class ArrowClient(object):
    DEFAULT_TIMEOUT = 10
    DEFAULT_ROOT_URL = "https://edge.arrow.trade"
    DEFAULT_LOGIN_URL = "https://api.arrow.trade/auth/app/login"
    VALIDATE_2FA_URL = "https://api.arrow.trade/auth/validate-2fa"

    def __init__(
            self, app_id: str,
            timeout: Optional[int] = None,
            debug: bool = False,
            root_url: Optional[str] = None,
            pool_config: Optional[Dict[str, Any]] = None) -> None:
        self.app_id = app_id
        self.req_session = requests.Session()
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.debug = debug
        self.root_url = root_url or self.DEFAULT_ROOT_URL
        self.disable_ssl = False
        self.proxies: Dict[str, str] = {}

        self._token: Optional[str] = None
        self._routes = constants.Routes(root_url=self.root_url)

    def place_order(self,
            exchange: Exchange,
            symbol: str,
            quantity: int,
            disclosed_quantity: int,
            product: ProductType,
            order_type: OrderType,
            variety: Variety,
            transaction_type: TransactionType,
            price: float,
            validity: Retention,
            remarks: Optional[str] = None) -> str:
        params = dict(
            exchange=str(exchange),
            symbol=symbol,
            quantity="{qty}".format(qty=quantity),
            disclosedQty="{disclosed_qty}".format(disclosed_qty=disclosed_quantity),
            product=str(product),
            order=str(order_type),
            transactionType=str(transaction_type),
            price="{price}".format(price=price),
            validity=str(validity),
            remarks=remarks or ""
        )  # type: Dict[str, Any]
        response = self._post(
            self._routes.PLACE_ORDER,
            url_args={"variety": str(variety)},
            params=params
        )
        return response["orderNo"]

    def set_token(self, token: str) -> None:
        self._token = token

    def get_token(self) -> str:
        return self._token or ""

    def invalidate_session(self) -> None:
        self._token = None

    # TODO
    def get_instruments(self) -> Any:
        return self._get(self._routes.ALL_INSTRUMENTS)

    # Order Routes
    def get_order_details(self, order_id: str) -> List[Dict[str, Any]]:
        data = self._get(self._routes.GET_ORDER_BY_ID, url_args={"order_id": order_id})
        return self._format_order_response(data)

    def get_order_book(self) -> List[Dict[str, Any]]:
        """Get all user orders."""
        data = self._get(self._routes.GET_USER_ORDERS)
        return self._format_orders_response(data)

    def get_trade_book(self) -> List[Dict[str, Any]]:
        """Get all user trades."""
        data = self._get(self._routes.GET_USER_TRADES)
        return self._format_trades_response(data)


    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all user trades."""
        data = self._get(self._routes.GET_USER_POSITIONS)
        return self._format_trades_response(data)

    def modify_order(
            self,
            order_id: str,
            exchange: Exchange,
            quantity: int,
            symbol: str,
            price: float,
            disclosed_qty: int,
            product: ProductType,
            transaction_type: TransactionType,
            order_type: OrderType,
            validity: Retention,
            remarks: Optional[str] = None,
    ) -> str:
        """Modify an existing order."""
        params = {
            "exchange": str(exchange),
            "quantity": str(quantity),
            "disclosedQty": str(disclosed_qty),
            "product": str(product),
            "symbol": symbol,
            "transactionType": str(transaction_type),
            "order": str(order_type),
            "price": str(price),
            "validity": str(validity),
            "remarks": remarks or "",
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

    def cancel_all_orders(self):
        data = self._get(self._routes.GET_USER_ORDERS)

        # Filter only open orders
        pending_orders = [
            order for order in data
            if order["orderStatus"] in ("OPEN", "TRIGGER_PENDING", "PARTIALLY_FILLED")
        ]

        # If nothing to cancel, return
        if not pending_orders:
            return []

        results = []

        # Set worker count (tweak based on your API rate limits)
        MAX_WORKERS = 9

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_order = {
                executor.submit(self.cancel_order, order["id"]): order["id"]
                for order in pending_orders
            }

            for future in as_completed(future_to_order):
                oid = future_to_order[future]
                try:
                    result = future.result()
                    results.append((oid, "SUCCESS", result))
                except Exception as e:
                    results.append((oid, "FAILED", str(e)))

        return results

    # User Details Routes
    def get_user_details(self) -> Dict[str, Any]:
        return self._get(self._routes.USER_DETAILS)

    # User Holdings
    def get_holdings(self) -> Dict[str, Any]:
        return self._get(self._routes.GET_USER_HOLDINGS)

    @staticmethod
    def get_expiry_dates(symbol: str, year: str):
        return expiry_dates[symbol][year]

    def get_user_limits(self) -> List[Dict[str, Any]]:
        return self._get(self._routes.GET_USER_LIMITS)

    # Margin Routes
    def order_margin(self,
                     exchange: Exchange,
                     symbol: str,
                     quantity: int,
                     product: ProductType,
                     order_type: OrderType,
                     transaction_type: TransactionType,
                     price: float,
                     include_positions: bool = False) -> Dict[str, Any]:
        params = dict(
            exchange=str(exchange),
            symbol=symbol,
            quantity="{qty}".format(qty=quantity),
            product=str(product),
            order=str(order_type),
            transactionType=str(transaction_type),
            price="{price}".format(price=price),
            includePositions=include_positions
        )  # type: Dict[str, Any]

        return self._post(self._routes.ORDER_MARGIN, params=params)

    def basket_margin(self,
                      orders: List[Dict[str, Any]],
                      include_positions: bool = False) -> Dict[str, Any]:
        params = dict(
            orders=orders,
            includePositions=include_positions
        )  # type: Dict[str, Any]

        return self._post(self._routes.BASKET_MARGIN, params=params)


    # Market Data
    def get_quote(self, mode: QuoteMode, symbol: str, exchange: Exchange):
        data = dict(symbol=symbol, exchange=str(exchange))
        return self._post(self._routes.QUOTE_DATA, url_args=dict(mode=str(mode)),params=data)

    def get_quotes(self, mode: QuoteMode, symbols: list[tuple[str, Exchange]]):
        data = [
            dict(symbol=symbol, exchange=str(exchange))
            for symbol, exchange in symbols
        ]

        return self._post(
            self._routes.QUOTES_DATA,
            url_args=dict(mode=str(mode)),
            params=data  # <-- correct for your wrapper
        )

    # Historical Data
    def candle_data(self,
                    exchange: Exchange,
                    token: str,
                    interval: str,
                    from_timestamp: str,
                    to_timestamp: str,
                    oi: bool = False
                    ) -> Dict[str, Any]:


        url = f"{self._routes.get_candle_url()}/candle/{str(exchange)}/{token}/{interval}"

        params = {
            'from': from_timestamp,
            'to': to_timestamp,
            'oi': int(oi),
        }

        # Pass None for url_args, then params
        return self._get(url, None, params)

    def _authenticate(self, checksum: str, request_token: str) -> Dict[str, str]:
        params = {
            "appID": self.app_id,
            "token": request_token,
            "checksum": checksum,
        }
        response = self._post("https://api.arrow.trade/auth/app/authenticate-token", params=params)
        if "token" in response:
            self._token = response["token"]
            if self.debug:
                log.debug(f"Token: {self._token}")

        return response

    def login_url(self) -> str:
        return f"{self._routes.get_home_url()}?appID={self.app_id}"

    def login(self, request_token: str, api_secret: str) -> Dict[str, str]:
        checksum = self._generate_checksum(request_token, api_secret)
        response = self._authenticate(checksum, request_token)
        return response

    def auto_login(self, user_id: str, password: str, api_secret: str, totp_secret: str) -> Dict[str, str]:
        login_url = self.DEFAULT_LOGIN_URL
        login_payload = {
            "userID": user_id,
            "password": password,
            "captchaValue": "",
            "captchaID": None,
            "appID": self.app_id,
            "isAppLogin": True
        }

        # Generate the request ID
        try:
            login_resp = self._post(login_url, params=login_payload)
            request_id = login_resp["requestId"]
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
            "code": passcode,  # Fixed: use passcode instead of request_id
            "requestId": request_id,
            "userID": user_id,
        }

        try:
            totp_resp = self._post(self.VALIDATE_2FA_URL, params=totp_payload)
            redirect_url = totp_resp["redirectUrl"]
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
            self.set_token(response["token"])
            return response
        except Exception as e:
            log.error("Failed to complete login: {}".format(e))
            raise

    def _generate_checksum(self, request_token: str, api_secret: str) -> str:
        input_str = f"{self.app_id}:{api_secret}:{request_token}"
        return hashlib.sha256(input_str.encode("utf-8")).hexdigest()

    # HTTP Route Methods
    def _get(self, route: str, url_args: Optional[Dict[str, str]] = None, params: Any = None) -> Any:
        return self._request("GET", route, url_args, params)

    def _post(self, route: str, url_args: Optional[Dict[str, str]] = None, params: Any = None,
              query_params: Any = None) -> Any:
        return self._request("POST", route, url_args, params, query_params)

    def _patch(self, route: str, url_args: Optional[Dict[str, str]] = None, params: Any = None,
               query_params: Any = None) -> Any:
        return self._request("PATCH", route, url_args, params, query_params)

    def _delete(self, route: str, url_args: Optional[Dict[str, str]] = None, params: Any = None) -> Any:
        return self._request("DELETE", route, url_args, params)

    def _request(self, method: str, route: str,
                 url_args: Optional[Dict[str, str]] = None,
                 params: Any = None, query_params: Any = None) -> Any:
        # Build URL
        url = route.format(**url_args) if url_args else route

        # Headers
        headers = {
            "User-Agent": f"pyarrow/{__version__}",
            "appID": self.app_id,
            "Content-Type": "application/json"  # Add explicit content type
        }

        # Only add token header if we actually have a token (not empty string)
        if self._token:
            headers["token"] = self._token

        if self.debug:
            log.debug(f"Request: {method} {url} params={json.dumps(params)} headers={json.dumps(headers)}")

        # Handle parameters correctly
        json_data = None
        query_params_final = query_params

        if method in ["POST", "PUT", "PATCH"]:
            json_data = params
        elif method in ["GET", "DELETE"] and params:
            query_params_final = params
        try:
            r = self.req_session.request(
                method=method,
                url=url,
                json=json_data,
                params=query_params_final,
                headers=headers,
                verify=not self.disable_ssl,
                allow_redirects=True,
                timeout=self.timeout,
                proxies=self.proxies
            )
        except Exception as e:
            raise e

        if self.debug:
            log.debug(f"Response: {method} {url}\n{r.content[:1000]!r}")

        content_type = r.headers.get("content-type", "")

        # JSON response
        if "json" in content_type:
            try:
                data = r.json()
            except ValueError:
                raise ex.DataException(f"Invalid JSON response: {r.content!r}")

            if isinstance(data, dict):
                if data.get(constants.STATUS) == constants.ERROR or data.get(constants.ERROR_CODE):
                    if r.status_code == 403:
                        # TODO: handle session expiry
                        pass
                    exp = getattr(ex, str(data.get(constants.ERROR_CODE)), ex.GeneralException)
                    raise exp(data.get(constants.ERROR_MESSAGE, "Unknown Error"), code=r.status_code)
                return data.get("data", data)
            return data

        # Binary response
        if "octet-stream" in content_type:
            return r.content

        # Unknown response type
        raise ex.DataException(f"Unknown Content-Type ({content_type}) Response: {r.content[:1000]!r}")

    # Data Parsing Methods
    def _format_order_response(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Format order response data."""
        order_list = [data] if isinstance(data, dict) else data
        return self._format_datetime_fields(order_list, ["timeStamp", "exchangeUpdateTime", "requestTime"])

    def _format_orders_response(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format orders response data."""
        return self._format_datetime_fields(data, ["timeStamp", "exchangeUpdateTime"])

    def _format_trades_response(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format trades response data."""
        return self._format_datetime_fields(data, ["fillTime", "timeStamp", "exchangeUpdateTime", "requestTime"])

    @staticmethod
    def _format_datetime_fields(data: List[Dict[str, Any]], datetime_fields: List[str]) -> List[Dict[str, Any]]:
        """Convert datetime strings and epoch times in response data."""
        for item in data:
            # Convert datetime strings
            for field in datetime_fields:
                if item.get(field) and len(str(item[field])) == 19:
                    item[field] = dateutil.parser.parse(item[field])

            # Convert epoch time to int
            if item.get("orderTime"):
                dt = datetime.strptime(item["orderTime"], "%Y-%m-%dT%H:%M:%S")
                item["orderTime"] = int(dt.timestamp())

        return data

    def get_holidays(self) -> Dict[str, Any]:
        return self._get(self._routes.HOLIDAYS_LIST)

    def get_index_list(self) -> List[Dict[str, Any]]:
        return self._get(self._routes.INDEX_LIST)

    def get_option_chain_symbols(self):
        return self._get(self._routes.OPTION_CHAIN_SYMBOLS)

    def get_option_chain(self, underlying: str, exchange: Exchange, count: int, expiry: str) -> Any:
        params = dict(
            exchange=str(exchange),
            underlying=underlying,
            count=str(count),
            expiry=expiry
        )
        return self._post(self._routes.OPTION_CHAIN, params=params)

    # Properties
    @property
    def token(self) -> str:
        return self._token or ""


Arrow = ArrowClient