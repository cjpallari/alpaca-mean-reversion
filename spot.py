from account_stuff import *
import datetime

watchlist = {
    "AAPL",  # Apple Inc.
    "MSFT",  # Microsoft Corporation
    "GOOGL",  # Alphabet Inc. (Google)
    "AMZN",  # Amazon.com Inc.
    "META",  # Meta Platforms Inc. (formerly Facebook)
    "TSLA",  # Tesla Inc.
    "NVDA",  # NVIDIA Corporation
    "INTC",  # Intel Corporation
    "AMD",  # Advanced Micro Devices Inc.
    "CRM",  # Salesforce.com Inc.
    "ORCL",  # Oracle Corporation
    "CSCO",  # Cisco Systems Inc.
    "IBM",  # International Business Machines Corporation
    "SAP",  # SAP SE
    "TXN",  # Texas Instruments Incorporated
    "QCOM",  # Qualcomm Incorporated
    "ADBE",  # Adobe Inc.
    "SHOP",  # Shopify Inc.
    "NFLX",  # Netflix Inc.
    "PYPL",  # PayPal Holdings Inc.
    "SQ",  # Block Inc. (formerly Square)
    "UBER",  # Uber Technologies Inc.
    "LYFT",  # Lyft Inc.
    "BABA",  # Alibaba Group Holding Limited
    "BIDU",  # Baidu Inc.
    "JD",  # JD.com Inc.
    "PDD",  # Pinduoduo Inc.
    "DOCU",  # DocuSign Inc.
    "V",  # Visa Inc.
    "MA",  # Mastercard Incorporated
    "INTU",  # Intuit Inc.
    "NOW",  # ServiceNow Inc.
    "TEAM",  # Atlassian Corporation
    "MELI",  # MercadoLibre Inc.
    "ETSY",  # Etsy Inc.
    "TTD",  # The Trade Desk Inc.
    "MRVL",  # Marvell Technology Inc.
    "SWKS",  # Skyworks Solutions Inc.
    "ANET",  # Arista Networks Inc.
    "AVGO",  # Broadcom Inc.
    "FISV",  # Fiserv Inc.
    "KLAC",  # KLA Corporation
    "LRCX",  # Lam Research Corporation
    "WDAY",  # Workday Inc.
    "ETHUSD",  # Ethereum
    "BCH",  # Bitcoin Cash
    "LTC",  # Litecoin
    "DOGEUSD",  # Dogecoin
    "LINK",  # Chainlink
    "EOS",  # EOS.IO
    "TRX",  # TRON
    "VET",  # VeChain
    "UNIUSD",  # Uniswap
    "SOL",  # Solana
    "ATOM",  # Cosmos
    "BYND",  # Beyond Meat Inc.
    "CRWD",  # CrowdStrike Holdings Inc.
    "PTON",  # Peloton Interactive Inc.
    "ZM",  # Zoom Video Communications Inc.
    "SNAP",  # Snap Inc.
    "ROKU",  # Roku Inc.
    "SPCE",  # Virgin Galactic Holdings Inc.
    "SPOT",  # Spotify Technology S.A.
    "U",  # Unity Software Inc.
    "PINS",  # Pinterest Inc.
    "DDOG",  # Datadog Inc.
    "DOTUSD",  # Not sure what is is
    "NKLA",  # Nikola Corporation
    "PLTR",  # Palantir Technologies Inc.
    "LCID",  # Lucid Group Inc.
    "RBLX",  # Roblox Corporation
    "UPST",  # Upstart Holdings Inc.
    "PATH",  # UiPath Inc.
    "SE",  # Sea Limited
    "SNOW",  # Snowflake Inc.
    "ABNB",  # Airbnb Inc.
    "GME",  # GameStop Corporation
}


purchase_info = {}
summary = {}
qty = 5
today = date.today()
start_date = today - timedelta(days=7)
start_date = str(start_date)
buying_power = float(get_account_balance())
target_gain = 1.05

now = datetime.datetime.now()
purchase_time = datetime.datetime.now()
min_seconds_between_purchases = 259200

headers = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}
