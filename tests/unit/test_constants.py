from pyarrow_client.constants import OrderType, Exchange


def test_order_type_aliases():
    assert OrderType.MKT is OrderType.MARKET
    assert OrderType.SL_LMT is OrderType.STOP_LOSS_LIMIT
    assert OrderType.SL_MKT is OrderType.STOP_LOSS_MARKET
    assert str(OrderType.MKT) == "MKT"


def test_exchange_mcxfo():
    assert Exchange.MCXFO == "MCXFO"
    assert str(Exchange.MCXFO) == "MCXFO"
    assert Exchange.MCX == "MCX"

