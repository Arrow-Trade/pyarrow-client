import pytest
import os
from pyarrow_client.connect import ArrowClient

# These tests will be skipped unless specific environment variables are set
# To run them: `ARROW_API_KEY=xxx ARROW_API_SECRET=yyy pytest tests/integration/`

@pytest.fixture
def integration_client():
    api_key = os.getenv("ARROW_API_KEY")
    if not api_key:
        pytest.skip("Skipping integration test: ARROW_API_KEY not set in environment.")
        
    client = ArrowClient(app_id=api_key)
    # Ideally, handle auth automatically if the secret/credentials are provided
    return client

def test_fetch_order_book_integration(integration_client):
    """
    Test making an actual API call to the live/test environment
    """
    # Assuming the token is already set or handled in the fixture
    try:
        orders = integration_client.get_order_book()
        assert isinstance(orders, list)
    except Exception as e:
        pytest.fail(f"Integration test failed with error: {e}")
