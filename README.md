# 📈 Mean Reversion Trading Bot

A fully automated trading bot built in **Python** that utilizes a mean reversion strategy to place real-time equity trades using the **Alpaca API**. Designed for 24/7 operation on a **Google Cloud VM**, with persistent session management via `tmux`.

---

## ⚙️ Features

- ✅ Executes trades based on mean reversion indicators  
- 🕒 Runs continuously with scheduled summary generation  
- ☁️ Deployed on Google Cloud with `tmux` for persistent uptime  
- 🔗 Integrates with Alpaca's API for order execution and market data  
- ✅ Logs trade actions and account data for monitoring and debugging  
- 🧠 Modular design (trading logic, account, spot pricing, notifications, etc.)

---

## 🛠️ Tech Stack

- Python  
- Alpaca API  
- Google Cloud Platform (GCP)  
- `tmux` (session persistence)  
- Requests, JSON, Datetime, and other standard libraries

---

## 📁 File Overview

| File | Description |
|------|-------------|
| `trading_logic.py` | Core strategy logic (mean reversion) and trade execution |
| `account_stuff.py` | Handles account details and positions |
| `spot.py` | Fetches current prices for specified assets |
| `mail.py` | Optional email notification logic |
| `twit.py` | (Optional) Twitter integration |
| `todo.txt` | Project planning and ideas |

---

## 🚀 Setup & Deployment

1. Clone the repo  
2. Set Alpaca API keys in a `.env` or config file  
3. Launch via `tmux` on your cloud VM:
   ```bash
   tmux new -s trading-bot
   python trading_logic.py

account_stuff.py	Handles account details and positions
spot.py	Fetches current prices for specified assets
mail.py	Optional email notification logic
twit.py	(Optional) Twitter integration
todo.txt	Project planning and ideas
