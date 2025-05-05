import os
import requests
import pandas as pd
from datetime import datetime, timedelta

def get_latest_valid_trading_date():
    """取得最近一個有效交易日（排除假日、週末）"""
    today = datetime.today()
    for i in range(5):
        check_date = today - timedelta(days=i)
        if check_date.weekday() < 5:
            return check_date.strftime("%Y-%m-%d")
    return today.strftime("%Y-%m-%d")

def fetch_finmind_data(dataset, stock_id, start_date, end_date):
    token = os.getenv("FINMIND_TOKEN")
    if not token:
        raise ValueError("❌ 未設定 FINMIND_TOKEN 環境變數")

    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": dataset,
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
        "token": token,
    }
    resp = requests.get(url, params=params)
    data = resp.json()

    if "data" not in data or not data["data"]:
        print(f"⚠️ FinMind API 無資料或格式錯誤：{dataset} / {stock_id} / {start_date} - {end_date}")
        return None

    return pd.DataFrame(data["data"])

def fetch_stock_technical_data(stock_id, start_date, end_date):
    df = fetch_finmind_data("TaiwanStockPrice", stock_id, start_date, end_date)
    if df is None or df.empty:
        print(f"⚠️ FinMind 無資料：{stock_id}")
        return None

    df = df.sort_values("date")
    df["MA5"] = df["close"].rolling(window=5).mean()
    df["MA20"] = df["close"].rolling(window=20).mean()

    # RSI6
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=6).mean()
    avg_loss = loss.rolling(window=6).mean()
    rs = avg_gain / avg_loss
    df["RSI6"] = 100 - (100 / (1 + rs))

    # KD 指標
    low_min = df["low"].rolling(window=9).min()
    high_max = df["high"].rolling(window=9).max()
    rsv = (df["close"] - low_min) / (high_max - low_min) * 100
    df["K9"] = rsv.ewm(com=2).mean()
    df["D9"] = df["K9"].ewm(com=2).mean()

    # MACD
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["DIF"] = ema12 - ema26
    df["MACD"] = df["DIF"].ewm(span=9, adjust=False).mean()

    # 布林通道
    df["20MA"] = df["close"].rolling(window=20).mean()
    df["stddev"] = df["close"].rolling(window=20).std()
    df["upper_band"] = df["20MA"] + 2 * df["stddev"]
    df["lower_band"] = df["20MA"] - 2 * df["stddev"]

    return df

def get_hot_stock_ids(limit=100, filter_type="all"):
    """根據成交金額排序，回傳前 N 檔熱門股票代號"""
    token = os.getenv("FINMIND_TOKEN")
    if not token:
        raise ValueError("❌ 未設定 FINMIND_TOKEN 環境變數")

    trade_date = get_latest_valid_trading_date()
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockPrice",
        "start_date": trade_date,
        "end_date": trade_date,
        "token": token
    }
    resp = requests.get(url, params=params)
    data = resp.json()

    if "data" not in data or not data["data"]:
        print("⚠️ 無法取得當日成交資料或格式錯誤：", data)
        return []

    df = pd.DataFrame(data["data"])
    df["turnover"] = df["close"] * df["TradingVolume"]
    df = df.sort_values("turnover", ascending=False)

    if filter_type == "large_cap":
        return df.head(limit)["stock_id"].tolist()
    elif filter_type == "small_cap":
        return df.tail(limit)["stock_id"].tolist()
    else:
        return df.head(limit)["stock_id"].tolist()
