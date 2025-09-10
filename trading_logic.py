from zoneinfo import ZoneInfo
from spot import *
from config import *
from account_stuff import *
from alpaca_api import AlpacaAPI
from mail import *

# from twit import *
import time
import datetime
from zoneinfo import ZoneInfo
import logging


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
        self.tz = ZoneInfo("America/Los_Angeles")

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

    def handle_already_purchased(self, symbol, latest_trade):
        if symbol in self.purchase_info:
            print(f"Hold {symbol} at {latest_trade}")
            logging.info("Holding {s}")
        else:
            print(f"Price is not far enough from the mean to buy {symbol}")

    def handle_buy_check(self, symbol, latest_trade):
        if (
            symbol not in self.purchase_info
            or (
                datetime.datetime.now(tz=self.tz)
                - self.purchase_info[symbol]["purchase_time"]
            ).total_seconds()
            > min_seconds_between_purchases
        ):
            buy(symbol)
            logging.info(f"{symbol} purchased at {latest_trade}")
            now = datetime.datetime.now(tz=self.tz)
            self.purchase_info[symbol] = {
                "entry_price": latest_trade,
                "purchase_time": now,
            }
            summary[symbol] = {
                "latest_trade": latest_trade,
                "purchase_time": now,
                "order_type": "buy",
            }
        else:
            logging.info(
                f"Buy order of {symbol} was attempted, but not enough time has passed since the last purchase of {symbol}"
            )

    def handle_sell_check(self, symbol, latest_trade, average, stdev):
        entry_price = self.purchase_info[symbol]["entry_price"]
        z = (latest_trade - average) / stdev
        entry_time = self.purchase_info[symbol]["purchase_time"]
        holding_period = datetime.datetime.now(tz=self.tz) - entry_time
        holding_days = holding_period.days
        if (
            (z >= MEAN_EXIT_Z)
            or (latest_trade >= entry_price * HARD_TP)
            or (holding_days >= MAX_HOLD_DAYS)
            or (z <= PANIC_Z)
        ):
            sell(symbol)
            logging.info(f"{symbol} sell order completed")
            exit_time = datetime.datetime.now(tz=self.tz)
            del self.purchase_info[symbol]
            summary[symbol] = {
                "latest_trade": latest_trade,
                "exit_time": exit_time,
                "order_type": "sell",
            }

    def buy_or_sell(
        self,
    ):  # This function determines whether to buy or sell a stock based on the average and standard deviation of the closing prices
        i = 0
        for symbol in self.watchlist:
            logging.info(f"Getting price for {symbol}")
            average, stdev = self.api.get_historical_data(
                symbol, lookback=LOOKBACK
            )  # Gets the average and standard deviation of the closing prices
            latest_trade = self.api.get_latest_trade(
                symbol
            )  # Gets the price of the latest trade
            if (
                (latest_trade is None)
                or (stdev is None)
                or (average is None)
                or (stdev == 0)
            ):  # If either the latest trade or the standard deviation is None, skip to the next symbol
                logging.error(
                    f"Error getting current trade price, stdev, avg, or stdev is 0: Latest trade: {latest_trade}, stdev: {stdev}, avg: {average}"
                )
                continue
            if symbol in self.purchase_info:
                logging.debug(f"Symbol in purchase history check was hit for: {symbol}")
                self.handle_sell_check(symbol, latest_trade, average, stdev)
            elif latest_trade < average - (
                stdev * Z_SCORE
            ):  # If the latest trade is less than the average minus the standard deviation, buy the stock
                logging.debug(
                    f"Should be looking into a buy order for symbol: {symbol}"
                )
                self.handle_buy_check(symbol, latest_trade)
            else:  # If the latest trade is within the average plus or minus the standard deviation, hold the stock
                logging.debug(f"No action being taken for symbol: {symbol}")
                self.handle_already_purchased(symbol, latest_trade)
        i += 1
        logging.info(f"Successfully looped through watchlist. Iteration: {i}")

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
                    f"order placed at: {data['exit_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
        else:
            message += "No sales today\n"

        # tweet(message)
        summary.clear()


def main():
    last_summary_date: datetime.date | None = None
    strategy = MeanReversion(
        watchlist,
        purchase_info,
        target_gain,
        start_date,
    )
    while True:
        try:
            now_pt = datetime.datetime.now(tz=strategy.tz)
            today_pt = now_pt.date()
            if is_market_open():
                strategy.buy_or_sell()
                time.sleep(120)
            else:
                strategy.buy_or_sell()
                after_close = (now_pt.hour > 13) or (
                    now_pt.hour == 13 and now_pt.minute >= 5
                )

                if after_close and (
                    last_summary_date is None or last_summary_date != today_pt
                ):
                    strategy.generate_summary()
                    last_summary_date = today_pt
                    time.sleep(3600)
                    continue
                time.sleep(300)
        except Exception as e:
            logging.error(f"Error in trading loop: {e}")
            time.sleep(60)  # wait before retrying


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(" Exiting...")

        exit()
