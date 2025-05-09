# modules/ta_generator.py

import pandas as pd
import numpy as np

def generate_technical_signals(df: pd.DataFrame) -> pd.DataFrame:
    print("[ta_generator] ✅ 產生技術指標欄位")

    # 技術指標：均線
    df["ma20"] = df["close"].rolling(window=20).mean()
    df["ma_signal"] = df["close"] > df["ma20"]

    # KD 指標（隨機震盪）
    low_min = df["low"].rolling(window=9).min()
    high_max = df["high"].rolling(window=9).max()
    rsv = (df["close"] - low_min) / (high_max - low_min) * 100
    df["kdj_k"] = rsv.ewm(com=2).mean()
    df["kdj_d"] = df["kdj_k"].ewm(com=2).mean()
    df["kdj_signal"] = df["kdj_k"] > df["kdj_d"]

    # MACD
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    df["macd_line"] = ema12 - ema26
    df["macd_signal_line"] = df["macd_line"].ewm(span=9).mean()
    df["macd_signal"] = df["macd_line"] > df["macd_signal_line"]

    # RSI
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi_signal"] = df["rsi"] > 50

    # 布林通道
    df["bollinger_mid"] = df["close"].rolling(window=20).mean()
    df["bollinger_std"] = df["close"].rolling(window=20).std()
    df["bollinger_upper"] = df["bollinger_mid"] + 2 * df["bollinger_std"]
    df["bollinger_lower"] = df["bollinger_mid"] - 2 * df["bollinger_std"]
    df["bollinger_signal"] = df["close"] > df["bollinger_mid"]

    # 弱勢走勢條件（例如跌破均線 + KD死亡交叉）
    df["weak_signal"] = (
        (df["close"] < df["ma20"]) &
        (df["kdj_k"] < df["kdj_d"])
    ).astype(int)

    return df