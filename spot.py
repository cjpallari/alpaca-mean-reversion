from account_stuff import *
from config import API_KEY, SECRET_KEY
import pandas as pd
import datetime

watchlist = {
    # Tech (mature/established)
    "AAPL",   # Apple Inc. - stable, predictable
    "MSFT",   # Microsoft Corporation - mature tech
    "GOOGL",  # Alphabet Inc. (Google) - established
    "INTC",   # Intel Corporation - cyclical, mean reverting
    "CSCO",   # Cisco Systems Inc. - mature networking
    "IBM",    # International Business Machines - value stock
    "ORCL",   # Oracle Corporation - enterprise software
    "TXN",    # Texas Instruments - semiconductor cyclical
    "QCOM",   # Qualcomm - telecom infrastructure
    "ADBE",   # Adobe Inc. - established software
    "V",      # Visa Inc. - payment processor, stable
    "MA",     # Mastercard - payment processor, stable
    "INTU",   # Intuit Inc. - established fintech
    "AVGO",   # Broadcom Inc. - semiconductor
    "FISV",   # Fiserv Inc. - financial services tech
    
    # Consumer Staples (excellent mean reversion)
    "PG",     # Procter & Gamble - consumer staples
    "KO",     # Coca-Cola - defensive consumer
    "PEP",    # PepsiCo - defensive consumer
    "WMT",    # Walmart - defensive retail
    "COST",   # Costco - membership retail
    "JNJ",    # Johnson & Johnson - healthcare/consumer
    "MCD",    # McDonald's - defensive restaurant
    
    # Financials (classic mean reversion sector)
    "JPM",    # JPMorgan Chase - large bank
    "BAC",    # Bank of America - large bank
    "WFC",    # Wells Fargo - regional bank
    "GS",     # Goldman Sachs - investment bank
    "MS",     # Morgan Stanley - investment bank
    
    # Industrials (cyclical mean reversion)
    "HD",     # Home Depot - home improvement retail
    "UPS",    # United Parcel Service - logistics
    "FDX",    # FedEx - logistics
    "CAT",    # Caterpillar - heavy machinery
    "GE",     # General Electric - industrial conglomerate
    "MMM",    # 3M Company - industrial/consumer
    
    # Utilities (ultimate mean reverters)
    "NEE",    # NextEra Energy - utility
    "DUK",    # Duke Energy - utility
    "SO",     # Southern Company - utility
    "D",      # Dominion Energy - utility
    "AEP",    # American Electric Power - utility
    
    # ETFs (diversified mean reversion)
    "SPY",    # SPDR S&P 500 ETF - broad market
    "QQQ",    # Invesco QQQ Trust - tech heavy
    "XLF",    # Financial Select Sector SPDR - financials
    "XLU",    # Utilities Select Sector SPDR - utilities
    "XLP",    # Consumer Staples Select Sector SPDR - staples
    
    # Selected growth with mean reversion characteristics
    "AMZN",   # Amazon - large cap, some mean reversion
    "NFLX",   # Netflix - mature streaming, cyclical
    "PYPL",   # PayPal - established fintech
    "TSLA",
    "NVDA",
    "META",
    "AMD",
    "CRM",
    "SHOP",
    "UBER",
    "LYFT"
}


purchase_info = {}
summary = {}
qty = 5
today = datetime.date.today()
start_date = today - pd.tseries.offsets.BDay(10)
start_date = str(start_date)
# buying_power = float(get_buying_power())
target_gain = 1.05

now = datetime.datetime.now()
purchase_time = datetime.datetime.now()
min_seconds_between_purchases = 259200

headers = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}
