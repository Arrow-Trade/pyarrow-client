import pytest
from pyarrow_client.exceptions import ArrowException, GeneralException, DataException

def test_arrow_exception():
    exc = ArrowException("Custom error message", 400)
    assert exc.message == "Custom error message"
    assert exc.code == 400
    assert "400 (Bad Request)" in str(exc)
    assert "Custom error message" in str(exc)

def test_general_exception():
    exc = GeneralException("General failure")
    assert exc.message == "General failure"
    assert exc.code == 500
    assert "500 (Internal Server Error)" in str(exc)
    assert "General failure" in str(exc)

def test_data_exception():
    exc = DataException("Data error")
    assert exc.message == "Data error"
    assert exc.code == 502
    assert "502 (Bad Gateway)" in str(exc)
    assert "Data error" in str(exc)

def test_exception_with_request_context():
    exc = GeneralException("Not found", code=404, method="GET", url="https://api.example.com/data")
    output = str(exc)
    assert "404 (Not Found)" in output
    assert "Not found" in output
    assert "GET https://api.example.com/data" in output

def test_exception_without_request_context():
    exc = ArrowException("Some error", 500)
    output = str(exc)
    assert "Request" not in output
