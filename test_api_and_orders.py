# tests/test_api_and_orders.py
import pytest
from unittest.mock import Mock, patch
import time
# test_generate_summary.py
import datetime
import types

# Import your modules
import trading_logic as tl
import account_stuff as acct
from alpaca_api import AlpacaAPI

# ---------------------------
# AlpacaAPI.get_latest_trade
# ---------------------------
def test_get_latest_trade():
    """
    Your code calls: GET .../trades/latest?symbols=AAPL&feed=iex
    and expects: {"trades": {"AAPL": {"p": 150.25, ...}}}
    """
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"trades": {"AAPL": {"p": 150.25}}}

    with patch("trading_logic.requests.get", return_value=mock_resp):
        api = tl.AlpacaAPI(headers={})
        price = api.get_latest_trade("AAPL")
        assert price == 150.25


# --------------------------------
# AlpacaAPI.get_historical_data()
# --------------------------------
def test_get_historical_data_avg_sd():
    """
    get_historical_data returns (average, raw stdev).
    For closes [150.2, 138.99, 151.0]:
      avg ≈ 146.73, stdev ≈ 6.71496
    """
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "bars": {"AAPL": [{"c": 150.2}, {"c": 138.99}, {"c": 151.0}]}
    }

    with patch("alpaca_api.requests.get", return_value=mock_resp):
        api = AlpacaAPI(headers={})
        avg, sd = api.get_historical_data("AAPL", lookback=3)
        assert round(avg, 2) == 146.73
        assert round(sd, 2) == 6.71


# -------------
# account_stuff
# -------------
def test_buy_places_notional_and_day_tif():
    """
    - POST /v2/orders
    - payload uses `notional` (no `qty`)
    - time_in_force == 'day'
    """
    mock_post = Mock()
    mock_post.status_code = 200
    mock_post.json.return_value = {
        "id": "order-id-123",
        "symbol": "AAPL",
        "notional": "500.00",
        "side": "buy",
        "status": "accepted",
    }

    with patch("account_stuff.get_buying_power", return_value=10_000.00), \
         patch("trading_logic.AlpacaAPI.get_latest_trade", return_value=50.00), \
         patch("account_stuff.requests.post", return_value=mock_post) as req_post:

        result = acct.buy("AAPL")

        # Assert request + payload
        req_post.assert_called_once()
        url_arg, kw = req_post.call_args
        assert url_arg[0] == "https://paper-api.alpaca.markets/v2/orders"
        payload = kw["json"]

        assert payload["side"] == "buy"
        assert payload["type"] == "market"
        assert payload["time_in_force"] == "day"
        assert payload["symbol"] == "AAPL"
        assert "qty" not in payload
        # Allow 500 or 500.00 depending on round()
        assert float(payload["notional"]) == pytest.approx(500.0)

        assert result["symbol"] == "AAPL"
        assert result["status"] == "accepted"


def test_sell_closes_position_via_delete():
    """
    Your sell() calls DELETE /v2/positions/{symbol}
    """
    mock_delete = Mock()
    mock_delete.status_code = 200
    mock_delete.json.return_value = {"symbol": "AAPL", "status": "closed"}

    with patch("account_stuff.requests.delete", return_value=mock_delete) as req_delete:
        result = acct.sell("AAPL")

        req_delete.assert_called_once()
        url_arg, kw = req_delete.call_args
        assert url_arg[0] == f"{acct.BASE_URL}/positions/AAPL"
        assert kw["headers"] == acct.headers

        assert result["symbol"] == "AAPL"
        assert result["status"] == "closed"


def test_get_num_of_shares_tolerates_fractionals():
    """
    Your current function might cast to int/float or return the raw string.
    Accept either, but ensure it represents the same quantity.
    """
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"symbol": "AAPL", "qty": "10.125000000"}]

    with patch("account_stuff.requests.get", return_value=mock_resp):
        qty = acct.get_num_of_shares("AAPL")

        # Accept string, float, or int behavior:
        if isinstance(qty, str):
            assert qty == "10.125000000"
        else:
            # If code converts to number, allow tiny rounding error
            assert float(qty) == pytest.approx(10.125, rel=1e-12)


def test_sell_liquidates_position_end_to_end():
    import pytest
    from unittest.mock import Mock, patch
    import account_stuff as acct

    # Before: you own 10.125 shares
    pre_get = Mock()
    pre_get.status_code = 200
    pre_get.json.return_value = [{"symbol": "AAPL", "qty": "10.125000000"}]

    # After: position list does NOT include AAPL (fully closed)
    post_get = Mock()
    post_get.status_code = 200
    post_get.json.return_value = []  # or omit AAPL from the list

    # DELETE response
    mock_delete = Mock()
    mock_delete.status_code = 200
    mock_delete.json.return_value = {"symbol": "AAPL", "status": "closed"}

    with patch("account_stuff.requests.get", side_effect=[pre_get, post_get]) as req_get, \
         patch("account_stuff.requests.delete", return_value=mock_delete) as req_delete:

        # Pre-condition
        qty_before = acct.get_num_of_shares("AAPL")
        assert float(qty_before) == pytest.approx(10.125, rel=1e-12)

        # Action
        result = acct.sell("AAPL")
        assert result["status"] == "closed"
        req_delete.assert_called_once_with(f"{acct.BASE_URL}/positions/AAPL", headers=acct.headers)

        # Post-condition
        qty_after = acct.get_num_of_shares("AAPL")
        assert float(qty_after) == 0.0

def sell_and_verify(symbol, retries=10, sleep_s=0.2):
    """Close position then poll positions until the symbol disappears."""
    resp = acct.sell(symbol)
    if not resp:
        return None
    for _ in range(retries):
        qty = acct.get_num_of_shares(symbol)
        try:
            if float(qty) == 0.0:
                return resp
        except Exception:
            if str(qty) in ("0", "0.0"):
                return resp
        time.sleep(sleep_s)
    raise RuntimeError(f"Position for {symbol} not closed after {retries} checks")


def test_sell_and_verify_polls_until_closed():
    # DELETE returns success
    mock_delete = Mock()
    mock_delete.status_code = 200
    mock_delete.json.return_value = {"symbol": "AAPL", "status": "closed"}

    # GET /positions returns:
    # 1) still have shares, 2) still have shares, 3) none left
    pre = Mock();  pre.status_code = 200;  pre.json.return_value  = [{"symbol":"AAPL","qty":"2.5"}]
    mid = Mock();  mid.status_code = 200;  mid.json.return_value  = [{"symbol":"AAPL","qty":"1.0"}]
    post= Mock(); post.status_code = 200; post.json.return_value = []  # closed

    with patch("account_stuff.requests.delete", return_value=mock_delete) as req_del, \
         patch("account_stuff.requests.get", side_effect=[pre, mid, post]) as req_get, \
         patch("account_stuff.time.sleep") as _sleep:  # don't actually sleep
        resp = sell_and_verify("AAPL", retries=5, sleep_s=0.01)

        assert resp["status"] == "closed"
        req_del.assert_called_once_with(f"{acct.BASE_URL}/positions/AAPL", headers=acct.headers)
        # polled until gone (consumed all three side_effects)
        assert req_get.call_count == 3






class DummyStrategy:
    """Minimal stand-in to call the same generate_summary implementation.
    If generate_summary is defined on MeanReversion, use MeanReversion instead.
    """
    generate_summary = tl.MeanReversion.generate_summary


def test_generate_summary_with_purchases_and_sales(monkeypatch):
    # Build a fake summary (module-level) with one buy and one sell
    fake_summary = {
        "AAPL": {
            "order_type": "buy",
            "latest_trade": 188.42,
            "purchase_time": datetime.datetime(2025, 8, 12, 10, 30, 5),
        },
        "MSFT": {
            "order_type": "sell",
            "latest_trade": 411.01,
            "purchase_time": datetime.datetime(2025, 8, 12, 11, 45, 0),
        },
    }

    # Capture the tweet text
    tweeted = {}
    def fake_tweet(msg: str):
        tweeted["msg"] = msg

    # Monkeypatch the module-level summary and tweet
    monkeypatch.setattr(tl, "summary", fake_summary, raising=True)
    monkeypatch.setattr(tl, "tweet", fake_tweet, raising=True)

    # Call the same method your code uses
    s = DummyStrategy.__new__(DummyStrategy)  # no init needed
    DummyStrategy.generate_summary(s)

    # Assert tweet was called once with the expected content
    assert "Summary of transactions:" in tweeted["msg"]
    assert "\nPurchases:" in tweeted["msg"]
    assert "Bought AAPL at: $188.42 order placed at: 2025-08-12 10:30:05" in tweeted["msg"]
    assert "\nSales:" in tweeted["msg"]
    assert "Sold MSFT at: $411.01 order placed at: 2025-08-12 11:45:00" in tweeted["msg"]

    # Assert the summary dict was cleared
    assert tl.summary == {}


def test_generate_summary_with_no_activity(monkeypatch):
    # Start with an empty summary
    fake_summary = {}

    tweeted = {}
    def fake_tweet(msg: str):
        tweeted["msg"] = msg

    monkeypatch.setattr(tl, "summary", fake_summary, raising=True)
    monkeypatch.setattr(tl, "tweet", fake_tweet, raising=True)

    s = DummyStrategy.__new__(DummyStrategy)
    DummyStrategy.generate_summary(s)

    # Verify the "no activity" messaging
    msg = tweeted["msg"]
    assert "Summary of transactions:" in msg
    assert "Purchases:" in msg
    assert "No purchases today" in msg
    assert "Sales:" in msg
    assert "No sales today" in msg

    # Still cleared (was already empty)
    assert tl.summary == {}

