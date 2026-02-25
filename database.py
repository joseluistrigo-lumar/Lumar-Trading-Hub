import os
import warnings
import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import datetime
import bcrypt

warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*")

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            timestamp TIMESTAMP NOT NULL,
            asset VARCHAR(50) DEFAULT 'NQ',
            direction VARCHAR(10) NOT NULL,
            entry_price DOUBLE PRECISION NOT NULL,
            exit_price DOUBLE PRECISION NOT NULL,
            stop_loss DOUBLE PRECISION NOT NULL,
            quantity INTEGER NOT NULL,
            pnl DOUBLE PRECISION NOT NULL,
            vwap_position VARCHAR(50) NOT NULL,
            ema_alignment VARCHAR(50) NOT NULL,
            volume_validation VARCHAR(50) NOT NULL,
            orb_level VARCHAR(50) NOT NULL,
            commandments_followed TEXT,
            commandments_broken TEXT,
            emotional_notes TEXT,
            discipline_score DOUBLE PRECISION DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def create_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    password_bytes = password.encode("utf-8")[:72]
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (%s, %s, %s) RETURNING id",
            (username, password_hash, datetime.now().isoformat()),
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return user_id, None
    except psycopg2.IntegrityError:
        conn.rollback()
        conn.close()
        return None, "Username already exists"


def authenticate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
    row = cursor.fetchone()
    conn.close()
    if row and bcrypt.checkpw(password.encode("utf-8")[:72], row["password_hash"].encode("utf-8")):
        return row["id"]
    return None


def insert_trade(user_id, trade_data):
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
            user_id, timestamp, asset, direction, entry_price, exit_price,
            stop_loss, quantity, pnl, vwap_position, ema_alignment,
            volume_validation, orb_level, commandments_followed,
            commandments_broken, emotional_notes, discipline_score
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id,
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


def get_all_trades(user_id):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM trades WHERE user_id = %s ORDER BY timestamp DESC",
        conn,
        params=(user_id,),
    )
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


def delete_trade(trade_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trades WHERE id = %s AND user_id = %s", (trade_id, user_id))
    conn.commit()
    conn.close()
