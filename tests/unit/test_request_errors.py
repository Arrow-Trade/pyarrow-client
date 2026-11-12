from unittest.mock import MagicMock

import pytest

from pyarrow_client.connect import ArrowClient
from pyarrow_client.exceptions import ArrowException


def _client(status, body):
    client = ArrowClient.__new__(ArrowClient)
    client.app_id, client._token, client.debug = "app", "tok", False
    client.disable_ssl, client.timeout, client.proxies = False, 5, None
    resp = MagicMock(status_code=status, headers={"content-type": "application/json"}, content=b"")
    resp.json.return_value = body
    client.req_session = MagicMock(request=MagicMock(return_value=resp))
    return client


@pytest.mark.parametrize("status", [404, 405])
def test_message_only_error_bodies_raise(status):
    with pytest.raises(ArrowException) as exc:
        _client(status, {"message": "not found"})._request("GET", "https://edge.arrow.trade/x")
    assert exc.value.code == status


def test_success_body_is_returned():
    assert _client(200, {"status": "success", "data": [1]})._request("GET", "https://x") == [1]
