# LUMAR Trading Journal & Strategy Tracker

## Overview
A professional trading journal for Nasdaq NQ Futures day traders, built with Python/Streamlit. Tracks trades, discipline, and emotional state using the LUMAR Strategy framework. Features user authentication with private data per trader.

## Architecture
- **app.py** - Main Streamlit application with auth system (login/signup) and 4 tabs: Dashboard, New Trade, Trade History, Export Data
- **database.py** - SQLite database module with user auth (bcrypt hashing), trade CRUD operations, and metrics calculation
- **lumar_trades.db** - SQLite database (auto-created on first run)
- **.streamlit/config.toml** - Streamlit config with dark theme

## Database Schema
- **users** table: id, username (unique), password_hash (bcrypt), created_at
- **trades** table: id, user_id (FK to users), timestamp, asset, direction, entry/exit prices, stop_loss, quantity, pnl, LUMAR checklist fields, commandments, emotional_notes, discipline_score

## Tech Stack
- Python 3.11, Streamlit, Pandas, Plotly
- SQLite for local data storage
- bcrypt for password hashing
- Dark theme with Neon Green (#00FF7F), Electric Blue (#00D4FF), Crimson Red (#FF3B3B)

## Key Features
- User authentication (login/signup) with private data per trader
- Dashboard with P&L, Win Rate, Profit Factor, Discipline Score metrics
- Equity curve and P&L distribution charts
- Trade entry form with LUMAR strategy checklist (VWAP, EMA, Volume, ORB)
- 10 Trading Commandments discipline tracking
- Emotional state notes
- Trade history with filtering/sorting
- CSV export
- Sidebar with LUMAR branding, YouTube link, website link, quick stats

## Running
```
streamlit run app.py --server.port 5000
```
