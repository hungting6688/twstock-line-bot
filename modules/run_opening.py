import os
import json
import pandas as pd
import gspread
from datetime import date
from modules.finmind_utils import fetch_finmind_data


# ✅ 從 GitHub Secrets 讀取 Google Sheets 金鑰並登入
def get_tracking_stock_ids(sheet_name="追蹤清單", column_index=1) -> list:
    google_key_json_str = os.getenv("GOOGLE_JSON_KEY")
    if not google_key_json_str:
        raise ValueError("❌ 未設定 GOOGLE_JSON_KEY 環境變數")
    google_key_dict = json.loads(google_key_json_str)
    gc = gspread.service_account_from_dict(google_key_dict)
    sh = gc.open(sheet_name)
    worksheet = sh.sheet1
    col_values = worksheet.col_values(column_index)
    return [v.strip() for v in col_values[1:] if v.strip().isdigit()]  # ✅ 忽略標題 + 過濾非數字

# 🔵 RSI 計算
def compute_rsi(close_prices, period=14):
    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 🔵 KD 計算
def compute_kd(df, period=9):
    low_min = df["low"].rolling(window=period).min()
    high_max = df["high"].rolling(window=period).max()
    rsv = (df["close"] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    return k, d

# 🟢 主程式：開盤分析邏輯
def analyze_opening():
    today = date.today().strftime("%Y-%m-%d")
    stock_ids = get_tracking_stock_ids()  # 從 Google Sheet 讀入股票代號

    messages = []
    for stock_id in stock_ids:
        df = fetch_finmind_data(
            dataset="TaiwanStockPrice",
            params={"stock_id": stock_id, "start_date": "2024-01-01", "end_date": today}
        )
        if df.empty or len(df) < 30:
            continue

        df["RSI"] = compute_rsi(df["close"])
        df["MA5"] = df["close"].rolling(5).mean()
        df["MA20"] = df["close"].rolling(20).mean()
        df["K"], df["D"] = compute_kd(df)

        latest = df.iloc[-1]
        signal_list = []

        # RSI 判斷
        if latest["RSI"] > 70:
            signal_list.append("🔺RSI > 70：短線過熱")
        elif latest["RSI"] < 30:
            signal_list.append("🟢RSI < 30：超跌區，有反彈機會")

        # 均線判斷
        if latest["MA5"] > latest["MA20"]:
            signal_list.append("🟢5日均線高於20日，短期偏多")
        else:
            signal_list.append("🔻短期均線跌破，觀望為主")

        # KD 黃金交叉判斷
        if latest["K"] > latest["D"] and df["K"].iloc[-2] < df["D"].iloc[-2]:
            signal_list.append("🟢KD 黃金交叉出現")

        if signal_list:
            messages.append(f"【{stock_id}】\n" + "\n".join(signal_list))

    if not messages:
        return "✅ 今日開盤追蹤股無明顯技術訊號"
    
    return "【開盤推薦股清單】\n" + "\n\n".join(messages)
