import os
import json
import pandas as pd
import gspread
from datetime import datetime, timedelta
from modules.finmind_utils import fetch_finmind_data

# ✅ 自動避開假日與早盤資料不全
def get_latest_valid_trading_date() -> str:
    today = datetime.today()
    if today.weekday() == 5:
        today -= timedelta(days=1)
    elif today.weekday() == 6:
        today -= timedelta(days=2)
    elif today.weekday() < 5 and today.hour < 15:
        today -= timedelta(days=1)
        if today.weekday() == 6:
            today -= timedelta(days=2)
        elif today.weekday() == 5:
            today -= timedelta(days=1)
    return today.strftime("%Y-%m-%d")

# ✅ 從 Google Sheets 讀取使用者追蹤股（自動讀取 Secrets 中的 SHEET ID）
def get_tracking_stock_ids(sheet_key, column_index=1) -> list:
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

# 📊 RSI 指標計算
def compute_rsi(close_prices, period=14):
    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 📊 KD 指標計算
def compute_kd(df, period=9):
    low_min = df["low"].rolling(window=period).min()
    high_max = df["high"].rolling(window=period).max()
    rsv = (df["close"] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    return k, d

# 🔍 分析一組股票清單（系統股或自選股都可）
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

        df["RSI"] = compute_rsi(df["close"])
        df["MA5"] = df["close"].rolling(5).mean()
        df["MA20"] = df["close"].rolling(20).mean()
        df["K"], df["D"] = compute_kd(df)
        latest = df.iloc[-1]

        signal_list = []

        if latest["RSI"] > 70:
            signal_list.append("🔺RSI > 70：短線過熱")
        elif latest["RSI"] < 30:
            signal_list.append("🟢RSI < 30：超跌反彈機會")

        if latest["MA5"] > latest["MA20"]:
            signal_list.append("🟢5日均線高於20日，短期偏多")
        else:
            signal_list.append("🔻短期均線跌破，觀望為主")

        if latest["K"] > latest["D"] and df["K"].iloc[-2] < df["D"].iloc[-2]:
            signal_list.append("🟢KD 黃金交叉出現")

        if signal_list:
            messages.append(f"【{stock_id}】\n" + "\n".join(signal_list))

    return messages

# 🟢 主流程：合併系統推薦與使用者追蹤股
def analyze_opening():
    # ✅ 系統內建熱門股（未來可改為自動抓熱門前200）
    hot_stock_ids = ["2603", "3231", "1513", "3707", "2303"]
    hot_signals = analyze_stock_list(hot_stock_ids)

    # ✅ 讀取使用者追蹤股（從 Secrets 讀 SHEET ID）
    sheet_key = os.getenv("GOOGLE_SHEET_ID")
    sheet_signals = []
    if sheet_key:
        sheet_stock_ids = get_tracking_stock_ids(sheet_key=sheet_key)
        sheet_signals = analyze_stock_list(sheet_stock_ids) if sheet_stock_ids else []

    # 📨 組合訊息
    final_msgs = []
    if hot_signals:
        final_msgs.append("📊 系統推薦：\n" + "\n\n".join(hot_signals))
    if sheet_signals:
        final_msgs.append("📝 額外追蹤：\n" + "\n\n".join(sheet_signals))

    return "\n\n".join(final_msgs) if final_msgs else "✅ 今日無明顯技術推薦股"
