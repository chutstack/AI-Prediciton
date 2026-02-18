from trader.data.adapters import _to_coinbase_product


def test_coinbase_product_format() -> None:
    assert _to_coinbase_product("BTCUSD") == "BTC-USD"
    assert _to_coinbase_product("BTC-USD") == "BTC-USD"
