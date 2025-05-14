# ✅ ta_generator.py
import pandas as pd

def generate_technical_signals(df):
    print("[ta_generator] ✅ 產生技術指標欄位")

    df = df.copy()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")

    # MA20
    df["ma20"] = df["close"].rolling(window=20).mean()
    df["ma_signal"] = df["close"] > df["ma20"]

    # Bollinger Band
    df["bb_mean"] = df["close"].rolling(window=20).mean()
    df["bb_std"] = df["close"].rolling(window=20).std()
    df["bollinger_signal"] = df["close"] > (df["bb_mean"] + df["bb_std"] * 1)

    # RSI (14)
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi_signal"] = df["rsi"] > 70

    # KD (9)
    low_min = df["close"].rolling(window=9).min()
    high_max = df["close"].rolling(window=9).max()
    rsv = (df["close"] - low_min) / (high_max - low_min) * 100
    df["kdj_k"] = rsv.ewm(com=2).mean()
    df["kdj_d"] = df["kdj_k"].ewm(com=2).mean()
    df["kdj_signal"] = df["kdj_k"] > df["kdj_d"]

    # MACD
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"] > 0

    return df
