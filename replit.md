# LUMAR Trading Journal & Strategy Tracker

## Overview
A professional trading journal for Nasdaq NQ Futures day traders, built with Python/Streamlit. Tracks trades, discipline, and emotional state using the LUMAR Strategy framework.

## Architecture
- **app.py** - Main Streamlit application with 4 tabs: Dashboard, New Trade, Trade History, Export Data
- **database.py** - SQLite database module for trade CRUD operations and metrics calculation
- **lumar_trades.db** - SQLite database (auto-created on first run)
- **.streamlit/config.toml** - Streamlit config with dark theme

## Tech Stack
- Python 3.11, Streamlit, Pandas, Plotly
- SQLite for local data storage
- Dark theme with Neon Green (#00FF7F), Electric Blue (#00D4FF), Crimson Red (#FF3B3B)

## Key Features
- Dashboard with P&L, Win Rate, Profit Factor, Discipline Score metrics
- Equity curve and P&L distribution charts
- Trade entry form with LUMAR strategy checklist (VWAP, EMA, Volume, ORB)
- 10 Trading Commandments discipline tracking
- Emotional state notes
- Trade history with filtering/sorting
- CSV export

## Running
```
streamlit run app.py --server.port 5000
```
