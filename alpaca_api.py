import requests
import statistics
from datetime import *
from urllib.parse import quote
import logging


# eth, doge, sq, dotusd,
class AlpacaAPI:
    DATA_BASE = "https://data.alpaca.markets"

    def __init__(self, headers):
        self.headers = headers

    def get_latest_trade(
        self,  # This function gets the latest trade data for a stock
        symbol,
    ):  # as of right now latest_trade is more accurate than latest_quote
        # url = f"https://data.alpaca.markets/v2/stocks/trades/latest?symbols={symbol}&feed=iex"
        url = f"https://data.alpaca.markets/v1beta3/crypto/us/latest/trades?symbols={quote(symbol, safe='')}"

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:  # If the request is successful
            data = response.json()
            trade_data = data.get("trades", {})

            if symbol in trade_data:  # If the symbol is found in the response
                trades = trade_data[symbol]  # Gets the trade data for the symbol
                latest_trade = trades.get(
                    "p", None
                )  # Gets the price of the latest trade
                logging.info(f"Symbol: {symbol}, Latest Trade: {latest_trade}")
                return latest_trade
            else:  # If no trade data is found for the symbol
                logging.warning(f"No trade data found for {symbol}")
                return None

        else:  # If the request fails
            logging.error(
                f"Failed to fetch latest trade data for {symbol}. Status code: {response.status_code}"
            )
            return None

    # def get_historical_data(self, symbol, lookback=20):
    #     # url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
    #     url = f"https://data.alpaca.markets/v1beta3/crypto/us/bars?symbols={quote(symbol, safe='')}&timeframe=1Min&limit=100"
    #     start = (datetime.now(timezone.utc) - timedelta(days=lookback * 3)).isoformat()
    #     params = {
    #         "timeframe": "1Day",  # note the capital D
    #         "start": start,
    #         "adjustment": "raw",
    #         "feed": "iex",
    #         "sort": "desc",  # newest first
    #         "limit": lookback,
    #     }
    #     r = requests.get(url, headers=self.headers, params=params)
    #     if r.status_code != 200:
    #         print(f"Failed bars for {symbol}: {r.status_code} {r.text}")
    #         return None, None

    #     data = r.json()
    #     bars = data.get("bars", [])
    #     if not isinstance(bars, list):
    #         print(f"Unexpected bars type for {symbol}: {type(bars)}; payload={data}")
    #     closes = [b.get("c") for b in bars if isinstance(b, dict) and "c" in b]

    #     if len(closes) < 2:
    #         print(f"No/insufficient bars for {symbol}. Response: {data}")
    #         return None, None

    #     avg = sum(closes) / len(closes)
    #     sd = statistics.stdev(closes)
    #     return avg, sd

    def get_historical_data(self, symbol, lookback=20, timeframe="1Day", timeout=15):
        crypto = "/" in symbol

        if crypto:
            url = f"{self.DATA_BASE}/v1beta3/crypto/us/bars"
            params = {"symbols": symbol, "timeframe": timeframe, "limit": lookback}
        else:
            url = f"{self.DATA_BASE}/v2/stocks/{symbol}/bars"
            params = {"timeframe": timeframe, "limit": lookback}

        r = requests.get(url, headers=self.headers, params=params, timeout=timeout)
        try:
            r.raise_for_status()
        except Exception:
            logging.error(f"Failed bars for {symbol}: {r.status_code} {r.text}")
            return None, None

        data = r.json()
        bars_obj = data.get("bars", {})
        # crypto: dict keyed by symbol; stocks: list
        if isinstance(bars_obj, dict):
            bars_list = bars_obj.get(symbol, [])
        else:
            bars_list = bars_obj

        if not isinstance(bars_list, list) or len(bars_list) < 2:
            logging.error(f"No/insufficient bars for {symbol}. Response: {data}")
            return None, None

        bars_list.sort(key=lambda b: b.get("t"))
        closes = [b["c"] for b in bars_list if isinstance(b, dict) and "c" in b][
            -lookback:
        ]
        if len(closes) < 2:
            logging.error(f"Insufficient closes extracted for {symbol}.")
            return None, None

        avg = sum(closes) / len(closes)
        sd = statistics.stdev(closes)
        return avg, sd
