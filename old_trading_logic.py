import requests
import statistics
from spot import *
from config import *
from account_stuff import *
from mail import *
from twit import *
import time
import datetime


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

    def get_historical_data(self, symbol):
        url = f"https://data.alpaca.markets/v2/stocks/bars?symbols={symbol}&timeframe=1day&start={start_date}T00%3A00%3A00Z&limit=1000&adjustment=raw&feed=iex&sort=asc"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:  # If the request is successful
            data = response.json()
            bars_data = data.get("bars", {}).get(symbol, [])

            if bars_data:
                closing_prices = [
                    bar["c"] for bar in bars_data
                ]  # Gets closing price from the api response
                average = sum(closing_prices) / len(
                    closing_prices
                )  # Calculates average of closing prices from the last 7 days
                stdev = (
                    statistics.stdev(closing_prices) * 1.5
                )  # Calculates standard deviation and multiplies by 1.5 - this is the threshold for buying or selling
                return average, stdev
            else:  # If no data is found for the symbol
                print(f"No historical data found for {symbol}")
                return None, None
        else:  # If the request fails
            print(
                f"Failed to fetch historical data for {symbol}. Status code: {response.status_code}"
            )
            return None, None


class TradingStrategy:
    def __init__(
        self,
        watchlist,
        purchase_info,
        target_gain,
        start_date,
        min_seconds_between_purchases,
        summary,
    ):
        self.watchlist = watchlist
        self.purchase_info = purchase_info
        self.target_gain = target_gain
        self.start_date = start_date
        self.min_seconds_between_purchases = min_seconds_between_purchases
        self.summary = summary
        self.api = AlpacaAPI(headers)

    def should_buy(self):
        pass

    def should_sell(self):
        pass


class MeanReversion(TradingStrategy):
    def __init__(
        self,
        watchlist,
        purchase_info,
        target_gain,
        start_date,
        min_seconds_between_purchases,
        summary,
    ):
        super().__init__(
            watchlist,
            purchase_info,
            target_gain,
            start_date,
            min_seconds_between_purchases,
            summary,
        )
        self.headers = headers

    def buy_or_sell(
        self,
    ):  # This function determines whether to buy or sell a stock based on the average and standard deviation of the closing prices
        buying_power = get_buying_power()
        for symbol in self.watchlist:
            num_of_shares = get_num_of_shares(symbol)
            average, stdev = self.api.get_historical_data(
                symbol
            )  # Gets the average and standard deviation of the closing prices
            latest_trade = self.api.get_latest_trade(
                symbol
            )  # Gets the price of the latest trade
            if (
                latest_trade is None or stdev is None
            ):  # If either the latest trade or the standard deviation is None, skip to the next symbol
                continue
            if (
                latest_trade < average - stdev
            ):  # If the latest trade is less than the average minus the standard deviation, buy the stock
                message = f"Purchased 5 shares of {symbol} at {latest_trade}"
                if latest_trade * 5 < buying_power:
                    if (
                        symbol not in self.purchase_info
                        or (
                            datetime.datetime.now()
                            - self.purchase_info[symbol]["purchase_time"]
                        ).total_seconds()
                        > self.min_seconds_between_purchases
                    ):
                        print(f"Buy {symbol} at {latest_trade}")
                        buy(symbol)
                        now = datetime.datetime.now()
                        self.purchase_info[symbol] = {
                            "latest_trade": latest_trade,
                            "purchase_time": now,
                        }
                        self.summary[symbol] = {
                            "latest_trade": latest_trade,
                            "purchase_time": now,
                            "order_type": "buy",
                        }
                        print(self.purchase_info)
                    else:
                        print("Not enough time has passed between purchases")
                else:
                    print(f"Not enough buying power to buy {symbol}")
            elif symbol in self.purchase_info:
                sell_target = self.purchase_info[symbol]["latest_trade"]
                if latest_trade > sell_target * self.target_gain:
                    sell(symbol)
                    sell_time = datetime.datetime.now()
                    del self.purchase_info[symbol]
                    self.summary[symbol] = {
                        "latest_trade": latest_trade,
                        "purchase_time": sell_time,
                        "order_type": "sell",
                    }
            else:  # If the latest trade is within the average plus or minus the standard deviation, hold the stock
                if symbol in self.purchase_info:
                    print(f"Hold {symbol} at {latest_trade}")
                else:
                    print(f"Price is not far enough from the mean to buy {symbol}")
        print(self.purchase_info)

    def generate_summary(self):
        message = "Summary of transactions: \n"
        message += "\nPurchases: \n"
        purchases = [t for t in self.summary.items() if t[1]["order_type"] == "buy"]
        if purchases:
            for symbol, data in purchases:
                message += (
                    f"Bought {symbol} at: ${data['latest_trade']:.2f} "
                    f"order placed at: {data['purchase_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
        else:
            message += "No purchases today\n"

        # Add sales
        message += "\nSales:\n"
        sales = [t for t in self.summary.items() if t[1]["order_type"] == "sell"]
        if sales:
            for symbol, data in sales:
                message += (
                    f"Sold {symbol} at: ${data['latest_trade']:.2f} "
                    f"order placed at: {data['purchase_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
        else:
            message += "No sales today\n"

        tweet(message)
        self.summary.clear()


def main():
    last_summary_date = None
    iteration = 0
    strategy = MeanReversion(
        watchlist,
        purchase_info,
        target_gain,
        start_date,
        min_seconds_between_purchases,
        summary,
    )
    while True:
        try:
            current_time = datetime.datetime.now()
            if is_market_open():
                print(iteration)
                iteration += 1
                strategy.buy_or_sell()
                time.sleep(120)
            else:
                if current_time.strftime("%H") >= "16" and (
                    last_summary_date is None
                    or current_time.date() != last_summary_date.date()
                ):
                    strategy.generate_summary()
                    last_summary_date = current_time.date()
                strategy.buy_or_sell()
                time.sleep(3600)
        except Exception as e:
            print(f"Error in trading loop: {e}")
            time.sleep(60)  # wait before retrying


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(" Exiting...")
        exit()