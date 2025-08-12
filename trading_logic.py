import requests
import statistics
from spot import *
from config import *
from account_stuff import *
from alpaca_api import AlpacaAPI
from mail import *
from twit import *
import time
import datetime



class TradingStrategy:
    def __init__(
        self,
        watchlist,
        purchase_info,
        target_gain,
        start_date,
    ):
        self.watchlist = watchlist
        self.purchase_info = purchase_info
        self.target_gain = target_gain
        self.start_date = start_date
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
    ):
        super().__init__(
            watchlist,
            purchase_info,
            target_gain,
            start_date,
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
                message = f"Attempting to purchase ${buying_power * .05} of {symbol} at {latest_trade}"
                if (
                    symbol not in self.purchase_info
                    or (
                        datetime.datetime.now()
                        - self.purchase_info[symbol]["purchase_time"]
                    ).total_seconds()
                    > min_seconds_between_purchases
                ):
                    print(f"Buy {symbol} at {latest_trade}")
                    buy(symbol)
                    now = datetime.datetime.now()
                    self.purchase_info[symbol] = {
                        "latest_trade": latest_trade,
                        "purchase_time": now,
                    }
                    summary[symbol] = {
                        "latest_trade": latest_trade,
                        "purchase_time": now,
                        "order_type": "buy",
                    }
                    print(self.purchase_info)
                else:
                    print("Not enough time has passed between purchases")

            elif symbol in self.purchase_info:
                sell_target = self.purchase_info[symbol]["latest_trade"]
                if latest_trade > sell_target * self.target_gain:
                    sell(symbol)
                    sell_time = datetime.datetime.now()
                    del self.purchase_info[symbol]
                    summary[symbol] = {
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
        purchases = [t for t in summary.items() if t[1]["order_type"] == "buy"]
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
        sales = [t for t in summary.items() if t[1]["order_type"] == "sell"]
        if sales:
            for symbol, data in sales:
                message += (
                    f"Sold {symbol} at: ${data['latest_trade']:.2f} "
                    f"order placed at: {data['purchase_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
        else:
            message += "No sales today\n"

        tweet(message)
        summary.clear()


def main():
    last_summary_date = None
    iteration = 0
    strategy = MeanReversion(
        watchlist,
        purchase_info,
        target_gain,
        start_date,
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
