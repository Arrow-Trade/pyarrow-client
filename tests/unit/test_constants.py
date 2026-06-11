from pyarrow_client.constants import OrderType


def test_order_type_aliases():
    assert OrderType.MKT is OrderType.MARKET
    assert OrderType.SL_LMT is OrderType.STOP_LOSS_LIMIT
    assert OrderType.SL_MKT is OrderType.STOP_LOSS_MARKET
    assert str(OrderType.MKT) == "MKT"
