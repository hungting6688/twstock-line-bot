import os
import json
import pandas as pd
import gspread
from datetime import datetime, timedelta
from modules.finmind_utils import fetch_finmind_data

# ✅ 自動避開假日、早上未收盤的情況
def get_latest_valid_trading_date() -> str:
    today = datetime.today()

    if today.weekday() == 5:  # Saturday
        today -= timedelta(days=1)
    elif today.weekday() == 6:  # Sunday
        today -= timedelta(days=2)
    elif today.weekday() < 5 and today.hour < 15:  # 平日早盤前
        today -= timedelta(days=1)
        if today.weekday() == 6:
            today -= timedelta(days=2)
        elif today.weekday() == 5:
            today -= timedelta(days=1)

    return today.strftime("%Y-%m-%d")

# ✅ Google Sheets 額外追蹤股（加上防呆）
def get_tracking_stock_ids(sheet_key="你的 SHEET KEY", column_index=1) -> list:
    try:
        google_key_json_str = os.getenv("GOOGLE_JSON_KEY")
        google_key_dict = json.loads(google_key_json_str)
        gc = gspread.service_account_from_dict(google_key_dict)
        sh = gc.open_by_key(sheet_key)
        worksheet = sh.sheet1
        col_values = worksheet.col_values(column_index)
        return [v.strip() for v in col_values[1:] if v.strip().isdigit()]
    except Exception as e:
        print(f"⚠️ 無法讀取 Google Sheets：{e}")
        return []

# 📊 RSI 計算
def compute_rsi(close_prices, period=14):
    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 📊 KD 計算
def compute_kd(df, period=9):
    low_min = df["low"].rolling(window=period).min()
    high_max = df["high"].rolling(window=period).max()
    rsv = (df["close"] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    return k, d

# ✅ 技術指標分析（共用邏輯）
def analyze_stock_list(stock_ids):
    today_str = get_latest_valid_trading_date()
    messages = []

    for stock_id in stock_ids:
        df = fetch_finmind_data(
            dataset="TaiwanStockPrice",
            params={"stock_id": stock_id, "start_date": "2024-01-01", "end_date": today_str}
        )
        if df.empty or len(df) < 30:
            print(f"⚠️ FinMind 無資料：{stock_id}")
            continue

        df["RSI"] =
