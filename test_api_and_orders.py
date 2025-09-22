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
def test_buy_posts_notional_market_order_for_crypto():
    # 30% of 1000 = 300 notional
    with patch("account_stuff.get_buying_power", return_value=1000.0):
        with patch("alpaca_api.AlpacaAPI.get_latest_trade", return_value=60000.0):
            mock_post = Mock()
            mock_post.status_code = 200
            mock_post.json.return_value = {
                "id": "order-123",
                "symbol": "BTC/USD",
                "notional": "300.00",
                "side": "buy",
                "status": "accepted",
            }

            # IMPORTANT: patch the module where `buy` is defined
            with patch("account_stuff.requests.post", return_value=mock_post) as post:
                result = acct.buy("BTC/USD")

                post.assert_called_once()
                (called_url,) = post.call_args[0]
                called_kwargs = post.call_args[1]

                assert called_url.endswith("/orders")
                assert called_kwargs["json"]["symbol"] == "BTC/USD"
                assert called_kwargs["json"]["side"] == "buy"
                assert called_kwargs["json"]["type"] == "market"
                # your code uses GTC now
                assert called_kwargs["json"]["time_in_force"] == "gtc"
                # 30% of 1000.0 = 300.00
                assert called_kwargs["json"]["notional"] == 300.00

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


# test_alpaca_api_bars.py
from unittest.mock import Mock, patch
from alpaca_api import AlpacaAPI

# ---- 1) ensures we pass `start` and use the crypto v1beta3 endpoint ----
def test_get_historical_data_sends_start_param_and_uses_crypto_endpoint():
    symbol = "BTC/USD"
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "bars": {
            symbol: [
                {"t": "2025-09-19T19:30:00Z", "c": 64000.0},
                {"t": "2025-09-19T19:31:00Z", "c": 64100.0},
            ]
        }
    }

    with patch("alpaca_api.requests.get", return_value=mock_resp) as mock_get:
        api = AlpacaAPI(headers={})
        avg, sd = api.get_historical_data(symbol, lookback=2, timeframe="1Min")

        # called once with the crypto bars endpoint
        assert mock_get.call_count == 1
        called_url = mock_get.call_args[0][0]
        called_kwargs = mock_get.call_args[1]
        assert called_url.endswith("/v1beta3/crypto/us/bars")

        # verify `start` is present in params and looks like an ISO-8601 string
        params = called_kwargs["params"]
        assert "start" in params and isinstance(params["start"], str)
        assert params["symbols"] == symbol
        assert params["timeframe"] == "1Min"
        assert params["limit"] == 2

        # sanity: still computes outputs
        assert round(avg, 2) == 64050.00
        # stdev of [64000, 64100] is 70.71...
        assert round(sd, 2) == 70.71

# ---- 2) computes avg/stdev over last `lookback` closes (multiple bars) ----
def test_get_historical_data_avg_sd_multiple_bars():
    symbol = "BTC/USD"
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "bars": {
            symbol: [
                {"t": "2025-09-19T19:30:00Z", "c": 64000.0},
                {"t": "2025-09-19T19:31:00Z", "c": 64100.0},
                {"t": "2025-09-19T19:32:00Z", "c": 63900.0},
            ]
        }
    }

    with patch("alpaca_api.requests.get", return_value=mock_resp):
        api = AlpacaAPI(headers={})
        avg, sd = api.get_historical_data(symbol, lookback=3, timeframe="1Min")

        # average of [64000, 64100, 63900] = 64000
        assert round(avg, 2) == 64000.00
        # sample stdev across all 3 values => 100.0
        assert round(sd, 2) == 100.00

# ---- 3) returns (None, None) when fewer than 2 bars are returned ----
def test_get_historical_data_insufficient_bars_returns_none():
    symbol = "BTC/USD"
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"bars": {symbol: [{"t": "2025-09-22T00:00:00Z", "c": 64000.0}]}}  # only one bar

    with patch("alpaca_api.requests.get", return_value=mock_resp):
        api = AlpacaAPI(headers={})
        avg, sd = api.get_historical_data(symbol, lookback=3, timeframe="1Min")
        assert avg is None and sd is None

