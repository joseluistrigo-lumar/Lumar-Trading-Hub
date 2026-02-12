import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "lumar_trades.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            asset TEXT DEFAULT 'NQ',
            direction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            quantity INTEGER NOT NULL,
            pnl REAL NOT NULL,
            vwap_position TEXT NOT NULL,
            ema_alignment TEXT NOT NULL,
            volume_validation TEXT NOT NULL,
            orb_level TEXT NOT NULL,
            commandments_followed TEXT,
            commandments_broken TEXT,
            emotional_notes TEXT,
            discipline_score REAL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def insert_trade(trade_data):
    conn = get_connection()
    cursor = conn.cursor()

    if trade_data["direction"] == "Long":
        pnl = (trade_data["exit_price"] - trade_data["entry_price"]) * trade_data["quantity"]
    else:
        pnl = (trade_data["entry_price"] - trade_data["exit_price"]) * trade_data["quantity"]

    followed = trade_data.get("commandments_followed", [])
    broken = trade_data.get("commandments_broken", [])
    total = len(followed) + len(broken)
    discipline_score = (len(followed) / total * 100) if total > 0 else 0

    cursor.execute("""
        INSERT INTO trades (
            timestamp, asset, direction, entry_price, exit_price,
            stop_loss, quantity, pnl, vwap_position, ema_alignment,
            volume_validation, orb_level, commandments_followed,
            commandments_broken, emotional_notes, discipline_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trade_data["timestamp"],
        trade_data["asset"],
        trade_data["direction"],
        trade_data["entry_price"],
        trade_data["exit_price"],
        trade_data["stop_loss"],
        trade_data["quantity"],
        pnl,
        trade_data["vwap_position"],
        trade_data["ema_alignment"],
        trade_data["volume_validation"],
        trade_data["orb_level"],
        ",".join(followed),
        ",".join(broken),
        trade_data.get("emotional_notes", ""),
        discipline_score,
    ))
    conn.commit()
    conn.close()
    return pnl, discipline_score


def get_all_trades():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp DESC", conn)
    conn.close()
    return df


def get_metrics(df):
    if df.empty:
        return {
            "total_pnl": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "discipline_score": 0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
        }

    total_pnl = df["pnl"].sum()
    winning = df[df["pnl"] > 0]
    losing = df[df["pnl"] <= 0]
    win_rate = (len(winning) / len(df) * 100) if len(df) > 0 else 0
    gross_profit = winning["pnl"].sum() if len(winning) > 0 else 0
    gross_loss = abs(losing["pnl"].sum()) if len(losing) > 0 else 0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else 0
    avg_discipline = df["discipline_score"].mean() if "discipline_score" in df.columns else 0

    return {
        "total_pnl": total_pnl,
        "win_rate": win_rate,
        "profit_factor": round(profit_factor, 2),
        "discipline_score": round(avg_discipline, 1),
        "total_trades": len(df),
        "winning_trades": len(winning),
        "losing_trades": len(losing),
    }


def delete_trade(trade_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
    conn.commit()
    conn.close()
