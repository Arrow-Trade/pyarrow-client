# Static SDK reference (curated from pyarrow_client source). Keep in sync with code changes.

REF_OVERVIEW = """# pyarrow-client — overview

- **PyPI name:** `pyarrow-client` (install: `pip install pyarrow-client`)
- **Import package:** `pyarrow_client` (underscore; hyphens are invalid in Python imports)
- **Main HTTP client:** `pyarrow_client.ArrowClient` (alias `pyarrow_client.connect.Arrow` points to the same class)
- **Streaming:** `pyarrow_client.ArrowStreams`, `OrderStream`, `DataStream`, `DataMode`; `pyarrow_client.sockets.HFTDataStream` for HFT binary WebSocket (`wss://socket.arrow.trade`)
- **Trading enums:** `Exchange`, `OrderType`, `ProductType`, `Retention`, `TransactionType`, `Variety`, `QuoteMode` in `pyarrow_client.constants` (re-exported from `pyarrow_client`)
- **Exceptions:** `ArrowException`, `GeneralException`, `DataException` in `pyarrow_client.exceptions`
- **Utilities:** `enable_logging()` on the top-level package; option expiry / symbol lists in `pyarrow_client.arrow_utils` (`expiry_dates`, `stock_options`)

Default REST base URL: `https://edge.arrow.trade`. Auth token exchange uses `https://api.arrow.trade/auth/app/authenticate-token`. Historical candles use host `https://historical-api.arrow.trade` (see `Routes.get_candle_url()`).

Use MCP **resources** under `pyarrow-sdk://reference/...` and **tools** (`sdk_version`, `list_package_exports`, `inspect_class`, `enum_members`, `lookup_constant`) for exact names and values — do not guess method signatures.
"""

REF_AUTHENTICATION = """# Authentication (ArrowClient)

## Constructor

`ArrowClient(app_id: str, timeout: Optional[int] = None, debug: bool = False, root_url: Optional[str] = None, pool_config: Optional[Dict[str, Any]] = None)`

- Session sends headers: `User-Agent: pyarrow-client/<version>`, `appID`, `Content-Type: application/json`, and `token` when set.

## Web / redirect login

1. `login_url()` → opens user flow with `appID` on `https://app.arrow.trade/app/login`.
2. From callback URL, read query param `request-token`.
3. `login(request_token: str, api_secret: str)` — builds SHA256 checksum `sha256(f"{app_id}:{api_secret}:{request_token}")`, POSTs to authenticate endpoint, stores token on success.
4. `get_token()` / `set_token(token: str)` / `invalidate_session()` manage session token.
5. `token` property returns current token or empty string.

## Programmatic login (TOTP)

`auto_login(user_id: str, password: str, api_secret: str, totp_secret: str)`:

1. POST `https://api.arrow.trade/auth/app/login` with user credentials and `appID`.
2. Obtain `requestId`, submit TOTP to `https://api.arrow.trade/auth/validate-2fa`.
3. Parse `redirectUrl` for `request-token`, then call `login()` and `set_token(response["token"])`.

## Errors

HTTP 5xx responses raise `GeneralException` with `code` set. Malformed JSON / non-JSON responses raise `DataException`. API error payloads map `errorCode` to exception classes under `pyarrow_client.exceptions` when present, else `GeneralException`.
"""

REF_HTTP_CLIENT = """# ArrowClient — HTTP API surface

All authenticated calls require a non-empty token (`set_token` / `login` / `auto_login`).

## Orders

- `place_order(exchange, symbol, quantity, disclosed_quantity, product, order_type, variety, transaction_type, price, validity, remarks=None, mpp=False)` → **str** `orderNo`
- `modify_order(order_id, exchange, quantity, symbol, price, disclosed_qty, product, transaction_type, order_type, validity, remarks=None, mpp=False)` → **str** message
- `cancel_order(order_id)` → **str** message
- `cancel_all_orders()` → list of `(order_id, "SUCCESS"|"FAILED", result_or_error)` for pending statuses `OPEN`, `TRIGGER_PENDING`, `PARTIALLY_FILLED`
- `get_order_details(order_id)` → list of dicts (timestamps normalized)
- `get_order_book()` / `get_trade_book()` / `get_positions()` → lists of dicts

## User & margin

- `get_user_details()`, `get_holdings()`, `get_user_limits()`
- `order_margin(...)`, `basket_margin(orders: List[Dict], include_positions=False)`

## Market & info

- `get_quote(mode: QuoteMode, symbol, exchange)`
- `get_quotes(mode: QuoteMode, symbols: list[tuple[str, Exchange]])`
- `candle_data(exchange, token, interval, from_timestamp, to_timestamp, oi=False)` — historical OHLC
- `get_instruments()`, `get_holidays()`, `get_index_list()`, `get_option_chain_symbols()`, `get_option_chain(underlying, exchange, count, expiry)`
- `get_stock_option_symbols()` — list from embedded `stock_options` data

## Utilities

- `get_expiry_dates(symbol: str, year: str)` — static `expiry_dates` table (e.g. NIFTY / year keys); **KeyError** if missing
- Class attribute aliases: `DEFAULT_ROOT_URL`, `DEFAULT_LOGIN_URL`, `VALIDATE_2FA_URL`

## Internal HTTP helpers (not public contract but exist): `_get`, `_post`, `_patch`, `_delete`, `_request`
"""

REF_ENUMS = """# Enumerations (str enums; `str(x)` sends API value)

| Class | Members |
|-------|---------|
| `Variety` | REGULAR=`regular`, COVER=`cover` |
| `Exchange` | NSE, NFO, BSE, BFO, MCX, INDEX |
| `TransactionType` | BUY=`B`, SELL=`S` |
| `OrderType` | MARKET=`MKT`, LIMIT=`LMT`, STOP_LOSS_LIMIT=`SL-LMT`, STOP_LOSS_MARKET=`SL-MKT` |
| `Retention` | DAY, IOC |
| `QuoteMode` | FULL=`full`, OHLCV=`ohlcv`, LTP=`ltp` |
| `ProductType` | MIS=`I`, CNC=`C`, NRML=`M` |

`DataMode` (WebSocket market stream, `sockets.py`): LTP=`ltp`, LTPC=`ltpc`, QUOTE=`quote`, FULL=`full`
"""

REF_EXCEPTIONS = """# Exceptions

- `ArrowException(message, code=500, method=None, url=None)` — base; formatted `__str__` includes status and request info
- `GeneralException` — generic / HTTP-style failures (e.g. 5xx from server)
- `DataException` — bad content-type, invalid JSON, unknown response (default code 502)

REST layer raises mapped exceptions from API `errorCode` when the response JSON includes it.
"""

REF_WEBSOCKETS = """# WebSockets & streaming

## ConnectionConfig (dataclass)

Fields include `appID`, `token`, `debug`, reconnect and timeout tuning (`enable_reconnect`, `max_reconnect_attempts`, `read_timeout`, `ping_interval`, …).

## OrderStream

- URL: `wss://order-updates.arrow.trade?appID=...&token=...`
- Text JSON messages; optional callback `on_order_update(data)` when `data` has `id`.

## DataStream (token-based binary ticks)

- URL: `wss://ds.arrow.trade?appID=...&token=...`
- `subscribe(mode: DataMode, tokens: List[int])` / `unsubscribe(...)` — JSON `code`: `sub`/`unsub`
- `on_ticks` receives parsed `MarketTick` from binary frames (LTP / LTPC / QUOTE / FULL sizes per implementation).

## HFTDataStream (`pyarrow_client.sockets.HFTDataStream`)

- URL: `wss://socket.arrow.trade?appID=...&token=...`
- Binary protocol: LTP packet type 1 (40 bytes), full depth type 2 (196 bytes), response type 99 (540 bytes). Prices in **paise** where documented in source.
- `subscribe(mode, symbols, latency=1000)` — mode `ltpc`/`l` or `full`/`f`; symbols as names **or** int token IDs (not mixed).
- `subscribe_by_segment` / `unsubscribe_by_segment` for `symIds` with exchange segment ids (`EXCH_NSE_CM`, `EXCH_NSE_FO`, …).

## ArrowStreams facade

- `ArrowStreams(appID, token, debug=False)` exposes `order_stream`, `data_stream`, `hft_data_stream`
- `connect_order_stream`, `connect_data_stream`, `connect_hft_data_stream`, `connect_all`, `disconnect_all`
- `subscribe_market_data` / `unsubscribe_market_data` delegate to `DataStream`
- `subscribe_hft_data` / `unsubscribe_hft_data` delegate to `HFTDataStream`
- `get_status()` — string status per stream
"""

REF_ROUTES = """# Routes & URLs (`pyarrow_client.constants`)

`Routes(root_url=None)` defaults root to `https://edge.arrow.trade`; candle base `https://historical-api.arrow.trade`.

Notable path constants (appended to root):

- Orders: `/order/{variety}` place; `/order/regular/{order_id}` modify/delete; `/order/{order_id}` get
- User: `/user/details`, `/user/orders`, `/user/trades`, `/user/positions`, `/user/holdings`, `/user/limits`
- Margin: `/margin/order`, `/margin/basket`
- Market: `/info/quote/{mode}`, `/info/quotes/{mode}`, `/info/option-chain`, `/info/holidays`, `/info/index-list`, ...
- `ALL_INSTRUMENTS` → `/all`

`candle_data` builds: `{candle_url}/candle/{exchange}/{token}/{interval}?from=&to=&oi=`
"""
