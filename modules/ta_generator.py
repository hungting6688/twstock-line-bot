# modules/ta_generator.py

import pandas as pd
import numpy as np

def generate_ta_signals(df):
    print("[ta_generator] ✅ 產生技術指標欄位")

    df = df.copy()
    df["macd_signal"] = False
    df["kdj_signal"] = False
    df["rsi_signal"] = False
    df["ma_signal"] = False
    df["bollinger_signal"] = False

    try:
        close = df["close"]

        # 計算 MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        df["macd_signal"] = macd > signal

        # 計算 KD
        low_min = close.rolling(window=9, min_periods=1).min()
        high_max = close.rolling(window=9, min_periods=1).max()
        rsv = (close - low_min) / (high_max - low_min + 1e-9) * 100
        k = rsv.ewm(com=2).mean()
        d = k.ewm(com=2).mean()
        df["kdj_signal"] = k > d

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        df["rsi_signal"] = rsi > 50

        # 均線
        ma5 = close.rolling(window=5).mean()
        ma20 = close.rolling(window=20).mean()
        ma60 = close.rolling(window=60).mean()
        df["ma_signal"] = (close > ma5) & (close > ma20) & (close > ma60)

        # 布林通道
        mid = close.rolling(window=20).mean()
        df["bollinger_signal"] = close > mid

    except Exception as e:
        print(f"[ta_generator] ⚠️ 技術指標處理失敗: {e}")

    return df
