import requests
import statistics

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
        url = "https://data.alpaca.markets/v2/stocks/bars"
        params = {
            "symbols": symbol,
            "timeframe": "1Day",     # note the capital D
            "limit": lookback,       # last N trading-day bars
            "adjustment": "raw",
            "feed": "iex",
            "sort": "desc",          # newest first
        }
        r = requests.get(url, headers=self.headers, params=params)
        if r.status_code != 200:
            print(f"Failed bars for {symbol}: {r.status_code} {r.text}")
            return None, None

        data = r.json()
        bars = data.get("bars", {}).get(symbol, [])
        closes = [b["c"] for b in bars]

        if len(closes) < 2:
            return None, None

        avg = sum(closes) / len(closes)
        sd  = statistics.stdev(closes)
        return avg, sd


    # def get_historical_data(self, symbol):
    #     url = f"https://data.alpaca.markets/v2/stocks/bars?symbols={symbol}&timeframe=1day&start={start_date}T00%3A00%3A00Z&limit=1000&adjustment=raw&feed=iex&sort=asc"
    #     response = requests.get(url, headers=self.headers)

    #     if response.status_code == 200:  # If the request is successful
    #         data = response.json()
    #         bars_data = data.get("bars", {}).get(symbol, [])

    #         if bars_data:
    #             closing_prices = [
    #                 bar["c"] for bar in bars_data
    #             ]  # Gets closing price from the api response
    #             average = sum(closing_prices) / len(
    #                 closing_prices
    #             )  # Calculates average of closing prices from the last 7 days
    #             stdev = (
    #                 statistics.stdev(closing_prices) * 2.5
    #             )  # Calculates standard deviation and multiplies by 1.5 - this is the threshold for buying or selling
    #             return average, stdev
    #         else:  # If no data is found for the symbol
    #             print(f"No historical data found for {symbol}")
    #             return None, None
    #     else:  # If the request fails
    #         print(
    #             f"Failed to fetch historical data for {symbol}. Status code: {response.status_code}"
    #         )
    #         return None, None