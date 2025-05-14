# modules/ta_generator.py
print("[ta_generator] ✅ 已載入最新版 (修正 KD 錯誤)")

import pandas as pd
import numpy as np

def calculate_technical_indicators(df):
    df = df.copy()
    df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    low_min = df["Low"].rolling(window=9).min()
    high_max = df["High"].rolling(window=9).max()
    rsv = (df["Close"] - low_min) / (high_max - low_min) * 100
    df["K"] = rsv.ewm(com=2).mean()
    df["D"] = df["K"].ewm(com=2).mean()

    df["RSI"] = calculate_rsi(df["Close"], window=14)
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["Upper"] = df["MA20"] + 2 * df["Close"].rolling(window=20).std()
    df["Lower"] = df["MA20"] - 2 * df["Close"].rolling(window=20).std()

    return df

def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def extract_ta_signals(df):
    latest = df.tail(1)
    try:
        return {
            "macd_golden": int((latest["MACD"] > latest["Signal"]).iloc[0]),
            "kd_golden": int((latest["K"] > latest["D"]).iloc[0]),
            "rsi_strong": int((latest["RSI"] > 50).iloc[0]),
        }
    except Exception as e:
        print(f"[ta_generator] ⚠️ 技術指標解析錯誤: {e}")
        return {}
