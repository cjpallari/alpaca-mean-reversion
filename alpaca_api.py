import requests
import statistics
from datetime import *


# eth, doge, sq, dotusd,
class AlpacaAPI:
    def __init__(self, headers):
        self.headers = headers

    def get_latest_trade(
        self,  # This function gets the latest trade data for a stock
        symbol,
    ):  # as of right now latest_trade is more accurate than latest_quote
        url = f"https://data.alpaca.markets/v2/stocks/trades/latest?symbols={symbol}&feed=iex"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:  # If the request is successful
            data = response.json()
            trade_data = data.get("trades", {})

            if symbol in trade_data:  # If the symbol is found in the response
                trades = trade_data[symbol]  # Gets the trade data for the symbol
                latest_trade = trades.get(
                    "p", None
                )  # Gets the price of the latest trade
                print(f"Symbol: {symbol}, Latest Trade: {latest_trade}")
                return latest_trade
            else:  # If no trade data is found for the symbol
                print(f"No trade data found for {symbol}")
                return None

        else:  # If the request fails
            print(
                f"Failed to fetch latest trade data for {symbol}. Status code: {response.status_code}"
            )
            return None

    def get_historical_data(self, symbol, lookback=20):
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
        start = (datetime.now(timezone.utc) - timedelta(days=lookback * 3)).isoformat()
        params = {
            "timeframe": "1Day",  # note the capital D
            "start": start,
            "adjustment": "raw",
            "feed": "iex",
            "sort": "desc",  # newest first
            "limit": lookback,
        }
        r = requests.get(url, headers=self.headers, params=params)
        if r.status_code != 200:
            print(f"Failed bars for {symbol}: {r.status_code} {r.text}")
            return None, None

        data = r.json()
        bars = data.get("bars", [])
        if not isinstance(bars, list):
            print(f"Unexpected bars type for {symbol}: {type(bars)}; payload={data}")
        closes = [b.get("c") for b in bars if isinstance(b, dict) and "c" in b]

        if len(closes) < 2:
            print(f"No/insufficient bars for {symbol}. Response: {data}")
            return None, None

        avg = sum(closes) / len(closes)
        sd = statistics.stdev(closes)
        return avg, sd
