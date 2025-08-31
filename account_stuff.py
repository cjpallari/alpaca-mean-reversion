import requests, json
import datetime
import time
from alpaca_api import AlpacaAPI
from spot import *
from config import *
import datetime
import pytz
from zoneinfo import ZoneInfo

BASE_URL = "https://paper-api.alpaca.markets/v2"
BASE_DATA_URL = "https://data.alpaca.markets/v2"
ACCOUNT_URL = "{}/account".format(BASE_URL)
TRADE_PRICE_URL_PATTERN = f"{BASE_DATA_URL}/stocks/{{symbol}}/trades"
headers = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}


def get_buying_power():
    r = requests.get(ACCOUNT_URL, headers=headers)
    data = r.json()
    return float(data["buying_power"])


def buy(symbol):  # This function buys a stock
    alpaca = AlpacaAPI(headers=headers)
    url = "https://paper-api.alpaca.markets/v2/orders"
    buying_power = get_buying_power()
    allocation = buying_power * 0.05
    latest_trade = alpaca.get_latest_trade(symbol)

    if latest_trade is None or latest_trade <= 0:
        print(f"Invalid trade price for {symbol}: {latest_trade}")
        return

    shares_to_buy = round((allocation / latest_trade), 6)

    if shares_to_buy < 0.0001:
        print("Out of funds")
        return

    payload = {
        "side": "buy",
        "type": "market",
        "time_in_force": "day",  # This is the time in force for the order - good till cancelled
        "symbol": symbol,
        "notional": round(allocation, 2),  # This is the number of shares to buy
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Order failed for {symbol}: {response.text}")
        return None
    data = response.json()

    return data


#write some tests to see if this works
def sell(symbol):
    url = f"https://paper-api.alpaca.markets/v2/positions/{symbol}"
    r = requests.delete(url, headers=headers)  # liquidates entire position
    if r.status_code != 200:
        print(f"Close failed for {symbol}: {r.text}")
        return None
    return r.json()



# def sell(symbol):  # This function sells a stock
#     url = "https://paper-api.alpaca.markets/v2/orders"
#     qty = get_num_of_shares(symbol)

#     if qty <= 0:
#         print(f"No shares available to sell for {symbol}")
#         return None

#     payload = {
#         "side": "sell",
#         "type": "market",
#         "time_in_force": "gtc",
#         "symbol": symbol,
#         "qty": str(qty),
#     }
#     response = requests.post(url, json=payload, headers=headers)
#     data = response.json()
#     if response.status_code == 200:
#         print(f"Sold {qty} shares of {symbol} successfully")
#     else:
#         print(f"Failed to sell {symbol}, reason: {data['message']}")
#     return data


def get_num_of_shares(symbol):
    url = "https://paper-api.alpaca.markets/v2/positions"

    response = requests.get(url, headers=headers)
    data = response.json()

    if response.status_code == 200:
        for list in data:
            if list["symbol"] == symbol:
                # print(f"Symbol: {symbol}, Num of shares: {list['qty']}")
                return float(list["qty"])
        return 0
    else:
        print(
            f"Failed to retrieve number of shares for {symbol}, reason: {data['message']}"
        )
        return 0

def is_market_open(now=None):
    if now is None:
        now = datetime.datetime.now(tz=PT)
    else:
        now = now.astimezone(PT)

    open_time  = now.replace(hour=6, minute=30, second=0, microsecond=0)
    close_time = now.replace(hour=13, minute=0,  second=0, microsecond=0)
    return open_time <= now <= close_time


def main():
    return BASE_DATA_URL


if __name__ == "__main__":
    main()
