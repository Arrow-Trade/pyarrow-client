import pyarrow_client


def test_public_exports():
    for name in (
        "HFTDataStream",
        "QuoteMode",
        "ConnectionConfig",
        "MarketTick",
        "enable_logging",
    ):
        assert hasattr(pyarrow_client, name)
