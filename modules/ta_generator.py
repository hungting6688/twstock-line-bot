# modules/ta_generator.py
import pandas as pd
import numpy as np

def generate_technical_signals(df):
    print("[ta_generator] ✅ 產生技術指標欄位")

    df["ma20"] = df["close"].rolling(window=20).mean()
    df["ma_signal"] = df["close"] > df["ma20"]

    df["rsi"] = compute_rsi(df["close"], window=14)
    df["rsi_signal"] = df["rsi"] > 50

    df["macd"], df["macd_signal"], _ = compute_macd(df["close"])
    df["macd_signal_flag"] = df["macd"] > df["macd_signal"]

    df["kdj_k"], df["kdj_d"] = compute_kdj(df["close"], df["low"], df["high"])
    df["kdj_signal"] = df["kdj_k"] > df["kdj_d"]

    df["bollinger_mean"] = df["close"].rolling(window=20).mean()
    df["bollinger_std"] = df["close"].rolling(window=20).std()
    df["boll_upper"] = df["bollinger_mean"] + 2 * df["bollinger_std"]
    df["boll_lower"] = df["bollinger_mean"] - 2 * df["bollinger_std"]
    df["boll_signal"] = df["close"] > df["bollinger_mean"]

    return df

def compute_rsi(series, window=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))

def compute_macd(series, short=12, long=26, signal=9):
    short_ema = series.ewm(span=short, adjust=False).mean()
    long_ema = series.ewm(span=long, adjust=False).mean()
    macd = short_ema - long_ema
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line
    return macd, signal_line, hist

def compute_kdj(close, low, high, window=9):
    low_min = low.rolling(window=window).min()
    high_max = high.rolling(window=window).max()
    rsv = (close - low_min) / (high_max - low_min + 1e-10) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    return k, d