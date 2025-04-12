from unittest.mock import Mock, patch
from trading_logic import AlpacaAPI, MeanReversion
from account_stuff import *
import datetime


class Tests:
    def test_get_latest_trade(symbol):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"trades": {"AAPL": {"p": 150.25}}}

        with patch("trading_logic.requests.get", return_value=mock_response):
            api = AlpacaAPI(headers={})
            result = api.get_latest_trade("AAPL")
            assert result == 150.25

    def test_get_historical_data(symbol):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "bars": {"AAPL": [{"c": 150.2}, {"c": 138.99}, {"c": 151.0}]}
        }

        with patch("trading_logic.requests.get", return_value=mock_response):
            api = AlpacaAPI(headers={})
            avg, std_dev = api.get_historical_data("AAPL")
            assert round(avg, 2) == 146.73
            assert round(std_dev, 2) == 10.07

    def test_buy_or_sell_triggers_buy(self):
        mock_api = Mock()
        mock_api.get_latest_trade.return_value = 85
        mock_api.get_historical_data.return_value = (100, 10)  # avg - stdev = 90

        with patch("trading_logic.buy") as mock_buy:
            strategy = MeanReversion(
                watchlist=["AAPL"],
                purchase_info={},
                target_gain=1.1,
                buying_power=1000,
                start_date="2024-01-01",
                now=datetime.datetime.now(),
                min_seconds_between_purchases=0,
                purchase_time=datetime.datetime.now(),
                summary={},
            )
            strategy.api = mock_api  # use mock instead of real API

            strategy.buy_or_sell()

            # ✅ Check side effects
            mock_buy.assert_called_once()
            assert "AAPL" in strategy.purchase_info
            assert strategy.purchase_info["AAPL"]["latest_trade"] == 85

    def test_get_shares(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"symbol": "AAPL", "qty": "10"}]

        with patch("account_stuff.requests.get", return_value=mock_response):
            num_shares = get_num_of_shares("AAPL")
            assert num_shares == 10

    def test_buy(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "order-id-123",
            "symbol": "AAPL",
            "qty": "5",
            "side": "buy",
            "status": "accepted",
        }

        with patch(
            "account_stuff.requests.post", return_value=mock_response
        ) as mock_post:
            result = buy("AAPL")

            # Check that the POST request was made correctly
            mock_post.assert_called_once_with(
                "https://paper-api.alpaca.markets/v2/orders",
                json={
                    "side": "buy",
                    "type": "market",
                    "time_in_force": "gtc",
                    "symbol": "AAPL",
                    "qty": "5",
                },
                headers=headers,
            )

            # Assert the returned data matches the mocked response
            assert result["symbol"] == "AAPL"
            assert result["qty"] == "5"
            assert result["status"] == "accepted"
