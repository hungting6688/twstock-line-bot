
import os
import requests
import pandas as pd
from datetime import datetime, timedelta

def get_latest_valid_trading_date():
    today = datetime.today()
    for i in range(3):
        check_date = today - timedelta(days=i)
        if check_date.weekday() < 5:
            return check_date.strftime("%Y-%m-%d")
    return today.strftime("%Y-%m-%d")

def fetch_finmind_data(stock_id, start_date, end_date):
    token = os.getenv("FINMIND_TOKEN")
    if not token:
        raise ValueError("❌ 未設定 FINMIND_TOKEN")

    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
        "token": token,
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    if not data["data"]:
        print(f"⚠️ FinMind API 無資料，請檢查：{params}")
        return None
    df = pd.DataFrame(data["data"])

    # 增加技術指標 (假設你已經透過 API 有包含這些欄位或本地計算)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["high"] = pd.to_numeric(df["max"], errors="coerce")
    df["low"] = pd.to_numeric(df["min"], errors="coerce")

    # 技術指標：RSI, KD, MA, MACD, Bollinger Bands
    df["ma_5"] = df["close"].rolling(window=5).mean()
    df["ma_20"] = df["close"].rolling(window=20).mean()
    df["rsi_6"] = compute_rsi(df["close"], 6)
    df["kdj_k_9_3"], df["kdj_d_9_3"] = compute_kd(df)
    df["macd_dif_12_26_9"], df["macd_macd_12_26_9"] = compute_macd(df["close"])
    df["bolling_upper"] = df["close"].rolling(20).mean() + 2 * df["close"].rolling(20).std()
    df["bolling_lower"] = df["close"].rolling(20).mean() - 2 * df["close"].rolling(20).std()

    return df

def compute_rsi(series, period):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_kd(df, period=9, k_period=3, d_period=3):
    low_min = df["low"].rolling(window=period).min()
    high_max = df["high"].rolling(window=period).max()
    rsv = (df["close"] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=k_period-1, adjust=False).mean()
    d = k.ewm(com=d_period-1, adjust=False).mean()
    return k, d

def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    macd = dif.ewm(span=signal, adjust=False).mean()
    return dif, macd

def get_hot_stock_ids(limit=100):
    token = os.getenv("FINMIND_TOKEN")
    url = "https://api.finmindtrade.com/api/v4/data"
    today = get_latest_valid_trading_date()
    params = {
        "dataset": "TaiwanStockTradingDaily",
        "start_date": today,
        "end_date": today,
        "token": token,
    }
    resp = requests.get(url, params=params)
    data = resp.json().get("data", [])
    df = pd.DataFrame(data)
    if df.empty or "Trading_turnover" not in df.columns:
        return []
    df["Trading_turnover"] = pd.to_numeric(df["Trading_turnover"], errors="coerce")
    df = df.sort_values(by="Trading_turnover", ascending=False)
    return df["stock_id"].head(limit).tolist()
