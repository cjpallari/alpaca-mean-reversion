import requests
import statistics
from spot import *
from config import *
from account_stuff import *
from mail import *
from twit import *
import time


def get_historical_data(symbol):  # This function gets the historical data for a stock
    url = f"https://data.alpaca.markets/v2/stocks/bars?symbols={symbol}&timeframe=1day&start={start_date}T00%3A00%3A00Z&limit=1000&adjustment=raw&feed=iex&sort=asc"
    response = requests.get(url, headers=headers)

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
            # print(f"Symbol: {symbol}, Average: {average}, Stdev: {stdev}")
            return average, stdev
        else:  # If no data is found for the symbol
            print(f"No historical data found for {symbol}")
            return None, None
    else:  # If the request fails
        print(
            f"Failed to fetch historical data for {symbol}. Status code: {response.status_code}"
        )
        return None, None


def get_latest_trade(  # This function gets the latest trade data for a stock
    symbol,
):  # as of right now latest_trade is more accurate than latest_quote
    url = (
        f"https://data.alpaca.markets/v2/stocks/trades/latest?symbols={symbol}&feed=iex"
    )
    response = requests.get(url, headers=headers)

    if response.status_code == 200:  # If the request is successful
        data = response.json()
        trade_data = data.get("trades", {})

        if symbol in trade_data:  # If the symbol is found in the response
            trades = trade_data[symbol]  # Gets the trade data for the symbol
            latest_trade = trades.get("p", None)  # Gets the price of the latest trade
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


def get_latest_quote(
    symbol,
):  # as of right now this does nothing, still trying to determine if latest_quote or latest_trade is more accurate
    url = (
        f"https://data.alpaca.markets/v2/stocks/quotes/latest?symbols={symbol}&feed=iex"
    )
    response = requests.get(url, headers=headers)

    if response.status_code == 200:  #   If the request is successful
        data = response.json()
        # print(data)
        trade_data = data.get("quotes", {})  # Gets the quote data from the response

        if symbol in trade_data:  # If the symbol is found in the response
            trades = trade_data[symbol]  # Gets the quote data for the symbol
            latest_trade = trades.get(
                "bp", None
            )  # Gets the bid price of the latest quote
            print(f"Symbol: {symbol}, Latest quote: {latest_trade}")
            return latest_trade
        else:  # If no quote data is found for the symbol
            print(f"No quote data found for {symbol}")
            return None

    else:  # If the request fails
        print(
            f"Failed to fetch latest quote for {symbol}. Status code: {response.status_code}"
        )
        return None


def buy_or_sell():  # This function determines whether to buy or sell a stock based on the average and standard deviation of the closing prices
    for symbol in watchlist:
        num_of_shares = get_num_of_shares(symbol)
        average, stdev = get_historical_data(
            symbol
        )  # Gets the average and standard deviation of the closing prices
        latest_trade = get_latest_trade(symbol)  # Gets the price of the latest trade
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
                    symbol not in purchase_info
                    or (now - purchase_info[symbol]["purchase_time"]).total_seconds()
                    > min_seconds_between_purchases
                ):
                    print(f"Buy {symbol} at {latest_trade}")
                    buy(symbol)
                    purchase_info[symbol] = {
                        "latest_trade": latest_trade,
                        "purchase_time": purchase_time,
                    }
                    summary[symbol] = {
                        "latest_trade": latest_trade,
                        "purchase_time": purchase_time,
                        "order_type": "buy"
                    }
                    print(purchase_info)
                    #tweet(message)
                    # createMessage('buy', symbol, latest_trade)
                else:
                    print("Not enough time has passed between purchases")
            else:
                print(f"Not enough buying power to buy {symbol}")
        elif symbol in purchase_info:
            sell_target = purchase_info[symbol]["latest_trade"]
            if latest_trade > sell_target * target_gain:
                sell(symbol)
                del purchase_info[symbol]
                summary[symbol] = {
                        "latest_trade": latest_trade,
                        "purchase_time": purchase_time,
                        "order_type": "sell"
                    }
                #tweet(f"Sold {symbol} at {latest_trade}")
        else:  # If the latest trade is within the average plus or minus the standard deviation, hold the stock
            if symbol in purchase_info:
                print(f"Hold {symbol} at {latest_trade}")
            else:
                print(f"Price is not far enough from the mean to buy {symbol}")
    print(purchase_info)

def generate_summary(summary):
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
                f"order placed at: {data['purchase_time'].strftime('%Y-%m-%d %H:%M:')}\n"
            )
    else:
        message += "No sales today\n"
    
    tweet(message)
    summary.clear()


def main():
    last_summary_date = None
    while True:
        time = datetime.datetime.now()
        if is_market_open():
            buy_or_sell()
            time.sleep(120)
        else:
            if time.strftime("%H") == "17" and time.date() != last_summary_date:
                generate_summary(summary)
                last_summary_date = time.date()
            buy_or_sell()
            time.sleep(3600)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        exit()

