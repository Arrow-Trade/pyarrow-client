import pytest
import responses
import urllib.parse
from pyarrow_client.connect import ArrowClient
from pyarrow_client.exceptions import GeneralException

@pytest.fixture
def arrow_client():
    # Intentionally not setting token to test login flow
    return ArrowClient(app_id="test_app_id")

def test_login_url(arrow_client):
    url = arrow_client.login_url()
    assert "https://app.arrow.trade/app/login" in url
    assert "test_app_id" in url

@responses.activate
def test_login(arrow_client):
    url = "https://edge.arrow.trade/auth/app/authenticate-token"
    mock_response = {
        "status": "success",
        "data": {"token": "valid_token"}
    }
    responses.add(responses.POST, url, json=mock_response, status=200)
    
    response = arrow_client.login(request_token="req_token", api_secret="secret")
    assert response["token"] == "valid_token"
    assert arrow_client.get_token() == "valid_token"

@responses.activate
def test_login_app_secret_alias(arrow_client):
    url = "https://edge.arrow.trade/auth/app/authenticate-token"
    mock_response = {
        "status": "success",
        "data": {"token": "valid_token"}
    }
    responses.add(responses.POST, url, json=mock_response, status=200)

    response = arrow_client.login(request_token="req_token", app_secret="secret")
    assert response["token"] == "valid_token"
    body = responses.calls[0].request.body
    assert b"checkSum" in body
    assert b"checksum" in body

@responses.activate
def test_login_failure(arrow_client):
    url = "https://edge.arrow.trade/auth/app/authenticate-token"
    mock_response = {
        "status": "error",
        "message": "Invalid checksum"
    }
    responses.add(responses.POST, url, json=mock_response, status=400)
    
    with pytest.raises(GeneralException):
        arrow_client.login(request_token="req_token", api_secret="secret")

def test_generate_checksum(arrow_client):
    checksum = arrow_client._generate_checksum("req_token", "secret")
    # SHA256 of appID:apiSecret:requestToken
    import hashlib
    expected = hashlib.sha256(b"test_app_id:secret:req_token").hexdigest()
    assert checksum == expected

@responses.activate
def test_auto_login(arrow_client):
    # Mocking standard web login URLs
    login_url = arrow_client.DEFAULT_LOGIN_URL
    validate_url = arrow_client.VALIDATE_2FA_URL
    auth_token_url = "https://edge.arrow.trade/auth/app/authenticate-token"
    
    # 1. Login user step
    responses.add(
        responses.POST, 
        login_url, 
        json={"status": "success", "requestId": "req_123"}, 
        status=200
    )
    
    # 2. Validate 2FA step
    responses.add(
        responses.POST, 
        validate_url, 
        json={"status": "success", "redirectUrl": "https://callback.com?request-token=req_token"}, 
        status=200
    )
    
    # 3. App authentication step
    responses.add(
        responses.POST, 
        auth_token_url, 
        json={"status": "success", "data": {"token": "final_token"}}, 
        status=200
    )
    
    response = arrow_client.auto_login("user", "pass", "api_secret", "JBSWY3DPEHPK3PXP") # valid base32 string for totp
    assert response["token"] == "final_token"
    assert arrow_client.get_token() == "final_token"
