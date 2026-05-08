# pyarrow-client — Official Python SDK for Arrow Trading

[![PyPI version](https://badge.fury.io/py/pyarrow-client.svg)](https://badge.fury.io/py/pyarrow-client)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/pyarrow-client.svg)](https://pypi.org/project/pyarrow-client/)

This package is the **official Arrow Trading API Python client**. It wraps REST endpoints for orders, portfolio, margins, and market data, plus WebSocket helpers for live quotes and order updates.

**Documentation (install, quick start, authentication, API reference):**  
[https://docs.arrow.trade/python-sdk/getting-started/](https://docs.arrow.trade/python-sdk/getting-started/)

Use that site as the source of truth for examples and behavior. This README only covers basics for PyPI.

## Installation

```bash
pip install pyarrow-client
```

- **PyPI package name:** `pyarrow-client` (hyphen)
- **Python import:** `pyarrow_client` (underscore). Do not confuse with the unrelated Apache `pyarrow` library.

Dependencies are declared in the package metadata (`requests`, `websocket-client`, `pyotp`, `python-dateutil`, `urllib3`). See [requirements](https://docs.arrow.trade/python-sdk/getting-started/#requirements) on the docs site.

## Development

```bash
git clone https://github.com/arrow-trade/pyarrow-client.git
cd pyarrow-client
pip install -e .
pip install pytest pytest-cov responses
pytest tests/
```

## License

[MIT](LICENSE)

## Support

- **Docs:** [https://docs.arrow.trade](https://docs.arrow.trade)
- **Email:** [support@arrow.trade](mailto:support@arrow.trade)

## Disclaimer

Trading involves risk. This software is provided as-is; use it in line with Arrow’s terms and your own compliance obligations.
