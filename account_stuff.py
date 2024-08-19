import requests, json
from datetime import *
from config import *
from spot import *
import datetime
import pytz

BASE_URL = "https://paper-api.alpaca.markets/v2"
BASE_DATA_URL = "https://data.alpaca.markets/v2"
ACCOUNT_URL = "{}/account".format(BASE_URL)
TRADE_PRICE_URL_PATTERN = f"{BASE_DATA_URL}/stocks/{{symbol}}/trades"
headers = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}


def get_account_balance():
    r = requests.get(ACCOUNT_URL, headers=headers)
    data = r.json()
    return data["buying_power"]


def buy(symbol):  # This function buys a stock
    url = "https://paper-api.alpaca.markets/v2/orders"

    payload = {
        "side": "buy",
        "type": "market",
        "time_in_force": "gtc",  # This is the time in force for the order - good till cancelled
        "symbol": symbol,
        "qty": "5",  # This is the number of shares to buy
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data


def sell(symbol):  # This function sells a stock
    url = "https://paper-api.alpaca.markets/v2/orders"
    qty = get_num_of_shares(symbol)

    payload = {
        "side": "sell",
        "type": "market",
        "time_in_force": "gtc",
        "symbol": symbol,
        "qty": qty,
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    print(data)
    if response.status_code == 200:
        print(f"Sold {qty} shares of {symbol} successfully")
    else:
        print(f"Failed to sell {symbol}, reason: {data['message']}")
    return data


def get_num_of_shares(symbol):
    url = "https://paper-api.alpaca.markets/v2/positions"

    response = requests.get(url, headers=headers)
    data = response.json()

    if response.status_code == 200:
        for list in data:
            if list["symbol"] == symbol:
                # print(f"Symbol: {symbol}, Num of shares: {list['qty']}")
                return list["qty"]
            else:
                return 0
    else:
        print(
            f"Failed to retrieve number of shares for {symbol}, reason: {data['message']}"
        )
        return None
    return None


def is_market_open():
    now = datetime.datetime.now()
    ctime = now.strftime("%H:%M:%S")
    tz_ca = pytz.timezone("America/Los_Angeles")
    close = (
        datetime.datetime.now(tz_ca)
        .replace(hour=13, minute=0, second=0, microsecond=0)
        .strftime("%H:%M:%S")
    )
    open = (
        datetime.datetime.now(tz_ca)
        .replace(hour=5, minute=0, second=0, microsecond=0)
        .strftime("%H:%M:%S")
    )

    return ctime < close and ctime > open


def main():
    # get_account_balance()
    return BASE_DATA_URL


if __name__ == "__main__":
    main()

