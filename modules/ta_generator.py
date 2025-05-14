# modules/ta_generator.py
print("[ta_generator] ✅ 已載入最新版 (修正 KD 錯誤)")

import pandas as pd
import yfinance as yf
import numpy as np

def calculate_indicators(df):
    df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    df["Low14"] = df["Low"].rolling(window=14).min()
    df["High14"] = df["High"].rolling(window=14).max()
    df["RSV"] = (df["Close"] - df["Low14"]) / (df["High14"] - df["Low14"]) * 100
    df["K"] = df["RSV"].ewm(com=2).mean()
    df["D"] = df["K"].ewm(com=2).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    df["MA5"] = df["Close"].rolling(window=5).mean()
    df["MA20"] = df["Close"].rolling(window=20).mean()

    df["stddev"] = df["Close"].rolling(window=20).std()
    df["UpperBand"] = df["MA20"] + 2 * df["stddev"]
    df["LowerBand"] = df["MA20"] - 2 * df["stddev"]

    return df

def generate_ta_signals(stock_id):
    try:
        df = yf.download(f"{stock_id}.TW", period="60d", interval="1d", progress=False)
        if df.empty or len(df) < 30:
            return None

        df = calculate_indicators(df)
        latest = df.iloc[-1:]

        signals = {
            "macd_golden": int(latest["MACD"].iloc[0] > latest["Signal"].iloc[0]),
            "kd_golden": int(latest["K"].iloc[0] > latest["D"].iloc[0]),
            "rsi_strong": int(latest["RSI"].iloc[0] > 50),
            "ma5_above_ma20": int(latest["MA5"].iloc[0] > latest["MA20"].iloc[0]),
            "bollinger_bias_up": int(latest["Close"].iloc[0] > latest["UpperBand"].iloc[0]),
            "bollinger_bias_down": int(latest["Close"].iloc[0] < latest["LowerBand"].iloc[0])
        }

        return signals

    except Exception as e:
        print(f"[ta_generator] ⚠️ 技術指標失敗：{stock_id} - {e}")
        return None
